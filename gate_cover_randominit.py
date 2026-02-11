# gate_cover.py
# Python 3.8+ (no future imports)
# Assumptions (per user):
# - layers[t][ctrl]=tgt (<10000) and layers[t][tgt]=ctrl+10000
# - delay=1, dbar_t=1 (ignored)
# - fully-connected network: 1 EPR per TeleGate remote gate, 1 EPR per TeleData teleported qubit
# - IMPORTANT: Future gates are ONLY used to estimate ncov in the objective; we DO NOT "cover/skip" future gates.

import math
from dataclasses import dataclass
import os
from typing import Dict, List, Tuple, Optional, Set, Any

import numpy as np

random_seed = 432

# ----------------------------- Parsing -----------------------------

def analyze_qasm(qasm_filelocation: str) -> Tuple[np.ndarray, int]:
    """
    Parse a (simple) QASM-like file into layers[t][q] encoding:
      - layers[t][q] = -1: qubit q not in any 2-qubit gate at layer t
      - for 'cx q[a],q[b];' (a control, b target):
          layers[t][a] = b
          layers[t][b] = a + 10000

    Single-qubit gates only advance the local timebin of the acted qubit.
    """
    with open(qasm_filelocation, "r") as f:
        lines = f.readlines()

    if not lines:
        raise ValueError("Empty input file.")

    # Expect first line contains number of qubits, e.g., 'qreg q[30];'
    num_qubits = int(lines[0].split("[")[1].split("]")[0])
    flag_list = [-1] * num_qubits
    gates: List[List[int]] = [[-1] * num_qubits]

    for raw in lines[1:]:
        line = raw.strip()
        if not line or line.startswith("//") or line.startswith("#"):
            continue
        if line.startswith(("OPENQASM", "include", "qreg", "creg")):
            continue

        if line.startswith("cx"):
            a, b = tuple(int(q.split("[")[1].split("]")[0]) for q in line.split()[1].split(","))

            # keep your original alignment policy
            if flag_list[a] >= flag_list[b]:
                flag_list[a] += 1
                flag_list[b] = flag_list[a]
            else:
                flag_list[b] += 1
                flag_list[a] = flag_list[b]

            while len(gates) < (flag_list[a] + 1):
                gates.append([-1] * num_qubits)

            t = flag_list[a]  # == flag_list[b]
            gates[t][a] = b
            gates[t][b] = a + 10000
        else:
            # treat as a 1-qubit gate: advance that qubit timebin
            if "[" not in line or "]" not in line:
                continue
            c = int(line.split("[")[1].split("]")[0])
            flag_list[c] += 1
            while len(gates) < (flag_list[c] + 1):
                gates.append([-1] * num_qubits)

    return np.array(gates, dtype=int), num_qubits


class Circuit:
    def __init__(self, filelocation: str):
        self.layers, self.num_qubits = analyze_qasm(filelocation)

    def count_2q_gates(self) -> int:
        """Count CNOTs by counting control entries (<10000)."""
        count = 0
        for t in range(self.layers.shape[0]):
            row = self.layers[t]
            for q in range(self.num_qubits):
                a = int(row[q])
                if 0 <= a < 10000:
                    count += 1
        return count


# ----------------------------- gate_cover core -----------------------------

@dataclass(frozen=True)
class Gate:
    gid: int
    layer: int
    control: int
    target: int


@dataclass
class TeleCandidate:
    kind: str  # "TeleData" or "TeleGate"
    migrations: List[Tuple[int, int, int]]  # (qubit, src_qpu, dst_qpu); empty for TeleGate
    ncov_est: int                           # ONLY for objective estimation
    n_epr: int                              # entanglement cost

    def cost(self) -> float:
        return self.n_epr / max(1, self.ncov_est)


def _extract_gates(layers: np.ndarray) -> List[Gate]:
    """Flatten layers into an ordered list of directed CNOT gates."""
    if layers.size == 0:
        return []
    T, Q = layers.shape
    gates: List[Gate] = []
    gid = 0
    for t in range(T):
        row = layers[t]
        for ctrl in range(Q):
            tgt = int(row[ctrl])
            if tgt == -1:
                continue
            if 0 <= tgt < 10000:
                if not (0 <= tgt < Q):
                    raise ValueError(f"Invalid target index at layer {t}: layers[{t}][{ctrl}]={tgt}, Q={Q}.")
                back = int(row[tgt])
                if back != ctrl + 10000:
                    raise ValueError(
                        f"Inconsistent encoding at layer {t}: layers[{t}][{ctrl}]={tgt} "
                        f"but layers[{t}][{tgt}]={back} (expected {ctrl+10000})."
                    )
                gates.append(Gate(gid=gid, layer=t, control=ctrl, target=tgt))
                gid += 1
            # tgt>=10000 is target entry; ignore
    return gates


def _initial_mapping(Q: int, L: int) -> Tuple[Dict[int, int], List[Set[int]]]:
    if L <= 0:
        raise ValueError("L must be > 0.")
    # P = math.ceil(Q / L)
    P=Q//L + 1
    mapping: Dict[int, int] = {}
    qpu_qubits: List[Set[int]] = [set() for _ in range(P)]
    for q in range(Q):
        p = q // L
        mapping[q] = p
        qpu_qubits[p].add(q)
    return mapping, qpu_qubits


def _is_local(g: Gate, mapping: Dict[int, int]) -> bool:
    return mapping[g.control] == mapping[g.target]


def _apply_migrations(mapping: Dict[int, int], qpu_qubits: List[Set[int]], migrations: List[Tuple[int, int, int]]) -> None:
    for q, src, dst in migrations:
        if mapping.get(q) != src:
            raise RuntimeError(f"Migration mismatch: qubit {q} expected in QPU {src}, found {mapping.get(q)}.")
        qpu_qubits[src].remove(q)
        qpu_qubits[dst].add(q)
        mapping[q] = dst


def _estimate_ncov_after_migration(
    g: Gate,
    gates: List[Gate],
    idx: int,
    mapping: Dict[int, int],
    migrations: List[Tuple[int, int, int]],
    lookahead_gates: int,
) -> int:
    """
    ONLY for objective estimation.
    Simulate migrations and count how many subsequent gates become local within the lookahead window.
    """
    sim_map = dict(mapping)
    for q, _, dst in migrations:
        sim_map[q] = dst

    ncov = 1
    end = min(len(gates), idx + 1 + lookahead_gates)
    for j in range(idx + 1, end):
        gj = gates[j]
        if sim_map[gj.control] == sim_map[gj.target]:
            ncov += 1
    return ncov


def _teledata_candidates_for_gate(
    g: Gate,
    gates: List[Gate],
    idx: int,
    mapping: Dict[int, int],
    qpu_qubits: List[Set[int]],
    L: int,
    lookahead_gates: int,
) -> List[TeleCandidate]:
    """
    Generate feasible TeleData candidates for this remote gate.
    Fully-connected: 1 EPR per teleported qubit.
    Capacity constraint: dst QPU must not exceed L.
    """
    src_c = mapping[g.control]
    src_t = mapping[g.target]
    P = len(qpu_qubits)

    def capacity_ok(dst_qpu: int, extra: int) -> bool:
        return (len(qpu_qubits[dst_qpu]) + extra) <= L

    cands: List[TeleCandidate] = []

    # A) move control -> target QPU
    if capacity_ok(src_t, 1):
        mig = [(g.control, src_c, src_t)]
        ncov = _estimate_ncov_after_migration(g, gates, idx, mapping, mig, lookahead_gates)
        cands.append(TeleCandidate(kind="TeleData", migrations=mig, ncov_est=ncov, n_epr=1))

    # B) move target -> control QPU
    if capacity_ok(src_c, 1):
        mig = [(g.target, src_t, src_c)]
        ncov = _estimate_ncov_after_migration(g, gates, idx, mapping, mig, lookahead_gates)
        cands.append(TeleCandidate(kind="TeleData", migrations=mig, ncov_est=ncov, n_epr=1))

    # C) move both -> third QPU
    for k in range(P):
        if k == src_c or k == src_t:
            continue
        if capacity_ok(k, 2):
            mig = [(g.control, src_c, k), (g.target, src_t, k)]
            ncov = _estimate_ncov_after_migration(g, gates, idx, mapping, mig, lookahead_gates)
            cands.append(TeleCandidate(kind="TeleData", migrations=mig, ncov_est=ncov, n_epr=2))

    return cands


def _telegate_candidate_for_gate() -> TeleCandidate:
    """
    Under the user's requested semantics ("do not put future covered gates into covered/D"),
    we DO NOT implement multi-gate TeleGate reuse here, otherwise you'd double-count future gates.
    So TeleGate is per-remote-gate:
      - ncov_est = 1
      - n_epr = 1
    """
    return TeleCandidate(kind="TeleGate", migrations=[], ncov_est=1, n_epr=1)







def gate_cover(
    layers: np.ndarray,
    L: int,
    *,
    lookahead_gates: int = 16,
    mapping0: Optional[Dict[int, int]] = None,
) -> Dict[str, Any]:
    """
    Gate-by-gate scheduling.

    IMPORTANT CHANGE (per user):
      - We DO NOT pre-mark future gates as covered.
      - Future gates ONLY contribute to objective estimation (ncov_est).
      - Every gate will be visited in order; its local/remote nature is evaluated under CURRENT mapping.

    New (per user):
      - Return mapping_by_layer: a T x Q list-of-lists where
            mapping_by_layer[t][q] = QPU id of logical qubit q
        after finishing all gates in layer t (i.e., end-of-layer snapshot).
    """
    if layers.size == 0:
        return {
            "D": [],
            "final_mapping": {},
            "gates": [],
            "mapping_events": [],
            "mapping_by_layer": [],
        }

    gates = _extract_gates(layers)
    T = layers.shape[0]
    Q = layers.shape[1]

    if mapping0 is None:
        mapping, qpu_qubits = _initial_mapping(Q, L)
    else:
        mapping = dict(mapping0)
        # Per user: P = floor(Q/L) + 1
        P = Q // L + 1
        qpu_qubits = [set() for _ in range(P)]

        for q in range(Q):
            if q not in mapping:
                raise ValueError(f"mapping0 missing qubit {q}.")
            p = mapping[q]
            if not (0 <= p < P):
                raise ValueError(f"mapping0[{q}]={p} invalid, P={P}.")
            qpu_qubits[p].add(q)

        for p in range(P):
            if len(qpu_qubits[p]) > L:
                raise ValueError(
                    f"Initial mapping violates capacity: QPU {p} has {len(qpu_qubits[p])}>{L}."
                )

    D: List[Dict[str, Any]] = []

    # (Scheme B) sparse log: only when TELEDATA changes mapping
    mapping_events: List[Dict[str, Any]] = []

    # Full per-layer mapping snapshots: T x Q
    mapping_by_layer: List[Optional[List[int]]] = [None] * T

    def _snapshot_vector() -> List[int]:
        # mapping[q] must exist for all q in [0..Q-1]
        return [mapping[q] for q in range(Q)]

    # Edge case: if there are no extracted gates, mapping never changes.
    if len(gates) == 0:
        v = _snapshot_vector()
        for t in range(T):
            mapping_by_layer[t] = v[:]  # copy row
        return {
            "D": D,
            "final_mapping": mapping,
            "gates": gates,
            "mapping_events": mapping_events,
            "mapping_by_layer": mapping_by_layer,  # type: ignore
        }

    last_layer_done = -1  # we will fill mapping_by_layer in order

    for idx, g in enumerate(gates):
        # If we jumped to a new layer, finalize snapshots for layers that have ended.
        # At this moment, 'mapping' is already the mapping AFTER finishing last processed gate,
        # i.e., end-of-(g.layer-1) and any empty layers before g.layer.
        if g.layer > last_layer_done + 1:
            # layers (last_layer_done+1 .. g.layer-1) have no more gates to process (either empty
            # or we just finished the previous layer). Snapshot current mapping for them.
            v = _snapshot_vector()
            for t in range(last_layer_done + 1, min(g.layer, T)):
                mapping_by_layer[t] = v[:]  # copy row
            last_layer_done = g.layer - 1

        # Now process gate g (which is in layer g.layer)
        if _is_local(g, mapping):
            D.append(
                {
                    "op": "LOCAL",
                    "gid": g.gid,
                    "layer": g.layer,
                    "control": g.control,
                    "target": g.target,
                }
            )
        else:
            td_cands = _teledata_candidates_for_gate(
                g, gates, idx, mapping, qpu_qubits, L, lookahead_gates
            )
            tg_cand = _telegate_candidate_for_gate()
            best = min(td_cands + [tg_cand], key=lambda c: c.cost())

            if best.kind == "TeleData":
                _apply_migrations(mapping, qpu_qubits, best.migrations)
                D.append(
                    {
                        "op": "TELEDATA",
                        "gid_trigger": g.gid,
                        "layer_trigger": g.layer,
                        "migrations": best.migrations,
                        "n_epr": best.n_epr,
                        "ncov_est": best.ncov_est,
                        "cost": best.cost(),
                    }
                )
                mapping_events.append(
                    {
                        "gid_trigger": g.gid,
                        "layer_trigger": g.layer,
                        "migrations": best.migrations,
                        "mapping": mapping.copy(),  # snapshot dict (optional)
                    }
                )
            else:
                D.append(
                    {
                        "op": "TELEGATE",
                        "gid_trigger": g.gid,
                        "layer_trigger": g.layer,
                        "control": g.control,
                        "target": g.target,
                        "n_epr": 1,
                        "ncov_est": 1,
                        "cost": 1.0,
                    }
                )

        # If this is the last gate in its layer (lookahead to next gate's layer), snapshot end-of-layer.
        next_layer = gates[idx + 1].layer if idx + 1 < len(gates) else None
        if next_layer is None or next_layer != g.layer:
            if 0 <= g.layer < T:
                mapping_by_layer[g.layer] = _snapshot_vector()
                last_layer_done = max(last_layer_done, g.layer)

    # Fill any remaining tail layers after the last gate layer (including possibly empty layers)
    if last_layer_done < T - 1:
        v = _snapshot_vector()
        for t in range(last_layer_done + 1, T):
            mapping_by_layer[t] = v[:]  # copy row

    # Sanity: ensure no None remains (shouldn't happen, but guard)
    for t in range(T):
        if mapping_by_layer[t] is None:
            mapping_by_layer[t] = _snapshot_vector()

    return {
        "D": D,
        "final_mapping": mapping,          # final mapping after full scheduling
        "gates": gates,
        "mapping_events": mapping_events,  # kept (scheme B)
        "mapping_by_layer": mapping_by_layer,
    }


# ----------------------------- main -----------------------------

if __name__ == "__main__":
    
    circuit_types = ["random"]

    base_root = rf"C:\Users\Butch\Desktop\TON2025revision\gate_cover_evals"
    for L in [5,15,25]:
        for circuit_type in circuit_types:

            out_dir = os.path.join(base_root, circuit_type, f"{L}_cap")
            os.makedirs(out_dir, exist_ok=True)

            # 👉 CSV 文件名
            out_file = os.path.join(out_dir, "results.csv")

            with open(out_file, "w", newline="") as f:
                # CSV header
                f.write("num_qubit,total_epr\n")

                # for i in range(1,9):
                #     num_qubit=math.ceil((i+0.5)*L)
                for num_qubit in range(30,101,10):
                    if circuit_type == "random":
                        file_path = rf"C:\Users\Butch\OneDrive - Stony Brook University\ICDCS_2025\random_circuits_new\{num_qubit}qubits_{num_qubit}layers.txt"
                    else:  # qft
                        file_path = rf"C:\Users\Butch\OneDrive - Stony Brook University\ICDCS_2025\qft_circuits\qft_circuit({num_qubit}qubits).txt"

                    circuit = Circuit(file_path)

                    result = gate_cover(
                        circuit.layers,
                        L,
                        lookahead_gates=10**9
                    )

                    total_epr = sum(op.get("n_epr", 0) for op in result["D"])

                    # 👉 CSV 行
                    f.write(f"{num_qubit},{total_epr}\n")

                    print(f"[{circuit_type}] num_qubit={num_qubit}, total_epr={total_epr}")

            print(f"CSV written to: {out_file}\n")