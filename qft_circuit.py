import math
from qiskit import QuantumCircuit
import numpy as np
from qiskit import QuantumCircuit, transpile
import matplotlib.pyplot as plt
from qiskit.qasm2 import dumps 
from tqdm import tqdm
from qiskit.circuit.library import QFT
def qft(n):
    """
    构建 n 比特的量子傅里叶变换（QFT）电路。
    
    参数:
    n (int): 量子比特数
    
    返回:
    QuantumCircuit: 实现 QFT 的量子电路
    """
    # 创建 n 比特量子电路
    qc = QuantumCircuit(n)
    
    # QFT 的主循环
    for j in range(n):
        # 对第 j 个比特应用 Hadamard 门
        qc.h(j)
        
        # 对第 j 个比特和后面的比特应用受控相位旋转门
        for k in range(j + 1, n):
            angle = np.pi / (2 ** (k - j))
            qc.cp(angle, k, j)  # 受控相位旋转门 cp(θ) 作用于比特 k -> j
    
    # 反转量子比特顺序
    for i in range(n // 2):
        qc.swap(i, n - i - 1)
    
    return qc

# 示例: 构建 3 比特的 QFT 电路
# 指定基础门集
# basis_gates = ['u3', 'u1', 'cx']
basis_gates = ['u3', 'u1', 'cx']
# for n in tqdm(range(10,91,10)):
#     qc_transpiled = transpile(qft(n), basis_gates=basis_gates)
#     qasm_code = dumps(qc_transpiled)
#     with open(f"C:/Users/Butch\Desktop/qcirc_construction/qft_circuits/qft_circuit({n}qubits).txt", "w") as file:
#         file.write(qasm_code)
num_qubit=3
for L in [5,10,20]:
    for i in range (1,9):
        num_qubit=math.ceil((i+0.5)*L)
        # qc_transpiled_nft = transpile(QFT(num_qubit,approximation_degree=0,do_swaps=False), basis_gates=basis_gates_ft,optimization_level=3)
        # qc_transpiled_ft= transpile(qc_transpiled_nft, basis_gates=basis_gates_ft,optimization_level=3)
        qc_transpiled = transpile(qft(num_qubit), basis_gates=basis_gates)
        qasm_code = dumps(qc_transpiled)
        with open(rf"C:\Users\Butch\OneDrive - Stony Brook University\ICDCS_2025\qft_circuits\qft_circuit({num_qubit}qubits).txt", "w") as file:
            file.write(qasm_code)
        # 绘制电路
        # qc_transpiled.draw('mpl')
        # plt.show()

