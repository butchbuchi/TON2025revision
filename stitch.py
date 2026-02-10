import numpy as np
from collections import defaultdict
from circuit_utils import Circuit
from itertools import product
import pandas as pd
import time
from FT_circuit import FT_circuit_func
def bipartite_max_mapping(P,P_bar):
    def compute_weight(node_a, node_b):
        """
        Compute the weight between two nodes based on the number of common elements.
        """
        return len(node_a & node_b)
    
    def build_weight_matrix(P, P_bar):
        """
        Build the weight matrix for the bipartite graph.
        """
        n, m = len(P), len(P_bar)
        weight_matrix = [[0] * m for _ in range(n)]
    
        for i, node_p in enumerate(P.values()):
            for j, node_p_bar in enumerate(P_bar.values()):
                weight_matrix[i][j] = compute_weight(set(node_p), set(node_p_bar))
    
        return weight_matrix
    
    def max_weight_matching(P, P_bar):
        """
        Find the maximum weight matching for the bipartite graph.
        """
        from scipy.optimize import linear_sum_assignment
    
        # Build the weight matrix
        weight_matrix = build_weight_matrix(P, P_bar)
    
        # Solve the assignment problem using the Hungarian algorithm
        row_ind, col_ind = linear_sum_assignment(weight_matrix, maximize=True)
    
        # Extract the maximum weight matching
        matching = [(i, j, weight_matrix[i][j]) for i, j in zip(row_ind, col_ind)]
    
        return matching
    
    def update_p_bar(P, P_bar, matching):
        """
        Update P_bar keys based on the matching results.
        """
        updated_p_bar = {}
        P_keys = list(P.keys())
        P_bar_keys = list(P_bar.keys())
        for i, j, _ in matching:
            updated_p_bar[P_keys[i]] = P_bar[P_bar_keys[j]]
        return updated_p_bar

    # Find the maximum weight matching
    result = max_weight_matching(P, P_bar)
    
    # Update P_bar based on the matching
    updated_p_bar = update_p_bar(P, P_bar, result)
    
    # # Print the updated P_bar
    # print("Updated P_bar:", updated_p_bar)
    
    # # Print the matching results
    # for i, j, weight in result:
    #     print(f"P[{list(P.keys())[i]}] matched with P_bar[{list(P_bar.keys())[j]}] with weight {weight}")
    # #Return the updated P_bar
    return updated_p_bar
  

def find_connected_components(qubits, pairs):
    """
    根据pairs构建图，找到量子比特的连通分量。
    pairs为[(q1, q2), (q3, q4), ...]
    """
    adjacency = {q: set() for q in qubits}
    for q1, q2 in pairs:
        adjacency[q1].add(q2)
        adjacency[q2].add(q1)

    visited = set()
    components = []

    for q in qubits:
        if q not in visited:
            stack = [q]
            comp = []
            while stack:
                node = stack.pop()
                if node not in visited:
                    visited.add(node)
                    comp.append(node)
                    for neigh in adjacency[node]:
                        if neigh not in visited:
                            stack.append(neigh)
            components.append(comp)

    return components

def first_fit_partition(qubits, pairs, num_qpus, max_qubits_per_qpu):
    """
    首先将由pairs定义的连通分量作为整体分配给QPU。
    然后将剩余的独立量子比特分配到QPU中。
    """
    qubits = list(qubits)
    components = find_connected_components(qubits, pairs)

    # 初始化 QPU bins
    bins = defaultdict(list)

    # 按连通分量尝试分配
    for comp in components:
        assigned = False
        # 优先尝试将连通分量分配到现有的 QPU 中
        for qpu, bin_qubits in bins.items():
            if len(bin_qubits) + len(comp) <= max_qubits_per_qpu:
                bin_qubits.extend(comp)
                assigned = True
                break
        # 如果无法分配到现有 QPU，则尝试新建 QPU 分区
        if not assigned:
            if len(bins) < num_qpus and len(comp)<=max_qubits_per_qpu:
                bins[len(bins)] = comp[:]
            else:
                # 无法分配新的 QPU，返回错误
                # print(f"Unable to assign component {comp} to any QPU. Current bins: {bins}")
                return None

    # 将未分配的量子比特分配到 QPU
    remaining_qubits = set(qubits) - {q for bin_qubits in bins.values() for q in bin_qubits}
    for q in remaining_qubits:
        assigned = False
        for qpu, bin_qubits in bins.items():
            if len(bin_qubits) < max_qubits_per_qpu:
                bin_qubits.append(q)
                assigned = True
                break
        if not assigned:
            if len(bins) < num_qpus:
                bins[len(bins)] = [q]
            else:
                print(f"Unable to assign qubit {q} to any QPU. Current bins: {bins}")
                return None

    return bins

def find_qubit_partition(circuit, num_qpus, max_qubits_per_qpu):
    """
    对每一层尝试寻找一个有效的分区方案。
    确保每个量子比特都被分配到某个 QPU。
    """
    L, Q = circuit.shape
    partitions = {}

    # 遍历所有可能的子线路范围
    for start in range(L):
        for end in range(start, L):
            # 收集[start, end]子线路的所有量子比特和pairs
            qubits = set(range(Q))
            pairs = []
            seen_pairs = set()

            for layer in range(start, end + 1):
                for q in range(Q):
                    target = circuit[layer, q]
                    if 0 <= target < Q and target != q:
                        pair = tuple(sorted((q, target)))
                        if pair not in seen_pairs:
                            seen_pairs.add(pair)
                            pairs.append(pair)

            # 尝试分区
            partition = first_fit_partition(qubits, pairs, num_qpus, max_qubits_per_qpu=max_qubits_per_qpu)
            if partition is not None:
                partitions[start, end]= partition
                
                    
    # # 遍历 partitions 字典
    # for (start, end), partition in partitions.items():
    #     # 解包并打印 start 和 end
    #     print(f"Start: {start}, End: {end}")
    #     # print(f"Partition: {partition}")

    #     # 遍历 partition 的键和值
    #     for qpu, qubits in partition.items():
    #         print(f"  QPU: {qpu}, Qubits: {qubits}")

        
        
    return partitions

def compute_stitching_cost(partition1, partition2):
    """
    计算两个相邻层分区间的Stitching成本。
    成本定义为与上一层相比需要更换QPU的量子比特数量。
    """
    # 首先建立 qubit -> QPU 的映射
    qubit_to_qpu_1 = {}
    for qpu, qubits in partition1.items():
        for q in qubits:
            qubit_to_qpu_1[q] = qpu

    qubit_to_qpu_2 = {}
    for qpu, qubits in partition2.items():
        for q in qubits:
            qubit_to_qpu_2[q] = qpu

    # 假设两层的量子比特数量与标签一致
    all_qubits = set(qubit_to_qpu_1.keys()).union(set(qubit_to_qpu_2.keys()))
    cost = 0
    for q in all_qubits:
        # 如果上一层和下一层的QPU不同，需要花费1的Stitching代价
        if qubit_to_qpu_1.get(q, -1) != qubit_to_qpu_2.get(q, -1):
            cost += 1

    return cost

def dynamic_programming_partitions(circuit, num_qpus, max_qubits_per_qpu):
    """
    利用动态规划寻找从第0层到最后一层的最优分区序列，使Stitching成本最小。
    这里的示例简单地对每层计算分区，然后相邻层之间计算Stitching成本。
    """
    partitions = find_qubit_partition(circuit, num_qpus, max_qubits_per_qpu)
    if not partitions:
        print("No valid partitions found.")
        return 

    return dynamic_programming_stitching(len(circuit), partitions)

import math

# 假设partitions[(start, end)] = partition_info 字典已给出
# partition_info包含子电路分区方案
# compute_stitching_cost(partitions[(s1,e1)], partitions[(s2,e2)])为已知函数

def dynamic_programming_stitching(m, partitions):
    # dp[i][j] = S[1, i, j]的值
    # i, j满足1 <= i <= j <= m
    # 初始化dp为无穷大
    dp = [[math.inf]*(m) for _ in range(m)]
    #dp_map才是最终涉及的mapping
    dp_map={}
    
    for j in range(0, m):
        # 检查 (0, j) 是否在 partitions 中
        if (0, j) in partitions:
            # 从 1 到 j 是一个 ZCSC，无需 Stitching 成本
            dp[0][j] = 0
            dp_map[(0,j)] = partitions[(0, j)]  # 将对应的分区存入 dp_map

    # 计算dp
    for j in range(0, m):      # 终点
        for i in range(0, j+1):  # 起点（要小于等于j）
            if (i, j) in partitions:
                # (i, j)是一个ZCSC，需要尝试用 (1, i', i) + SC((i',i),(i,j)) 来更新dp[i][j]
                # i' < i
                best_cost = math.inf
                best_i_prime=-1
                for i_prime in range(0, i):
                    if dp[i_prime][i-1] < math.inf:
                        # 计算Stitching成本
                        cost = dp[i_prime][i-1]
                        if cost < best_cost:
                            best_cost = cost
                            best_i_prime=i_prime
                if best_cost!=math.inf:
                    dp_map[(i,j)]=bipartite_max_mapping(dp_map[(best_i_prime,i-1)],partitions[(i,j)])
                    stiching_cost=compute_stitching_cost(dp_map[(best_i_prime,i-1)],dp_map[(i,j)])
                    # print(f"stiching cost for {i-1} to {i}:",stiching_cost)
                    best_cost+=stiching_cost
                if best_cost < dp[i][j]:
                    dp[i][j] = best_cost

    # 计算最终答案
    # 我们需要min_i dp[i][m]
    final_cost = math.inf
    final_i = None
    for i in range(0, m):
        if dp[i][m-1] < final_cost:
            final_cost = dp[i][m-1]
            final_i = i
    print(final_i)
    print(dp_map[(final_i,m-1)])
    print("final_cost:",final_cost)
    # 返回最终成本和相应分解的起点final_i（若需要回溯请在dp中保留额外信息）
    
    qpu_in_use=len(dp_map[(final_i,m-1)])
    while final_i!=0:
        final_cost_temp = math.inf
        m=final_i
        for i in range(0, m):
            if dp[i][m-1] < final_cost_temp:
                final_cost_temp = dp[i][m-1]
                final_i = i
        if qpu_in_use<len(dp_map[(final_i,m-1)]):
            qpu_in_use=len(dp_map[(final_i,m-1)])
                
            
    return final_cost,qpu_in_use

        
    

# # 示例使用
# L = 3  # 层数
# Q = 6  # 量子比特数
# num_qpus = 3
# max_qubits_per_qpu = 2

# # 示例电路（与原始代码类似）
# circuit = np.array([
#     [-1, 4, -1, -1, 1, -1],
#     [-1, 4, -1, -1, 1, -1],
#     [-1, -1, -1, 5, -1, 3]
# ])

# Q=50
# file_path=f"C:/Users/Butch/Desktop/qcirc_construction/qft_circuits/qft_circuit({Q}qubits).txt"
# circuit=Circuit(file_path)
# circuit=circuit.layers
# L=len(circuit)
# num_qpus=50
# save_path=f"C:/Users/Butch/Desktop/qcirc_construction/baseline_code/stitch_final_plots/stitch_{Q}qft.csv"
# with open(save_path,'w') as file:
#           file.write("x,stitch,time,num_qpus\n")
# for max_qubits_per_qpu in range(25,26):
#     start_time=time.time()
#     print("max_qubits_per_qpu:",max_qubits_per_qpu)
#     total_cost_ave=0
#     qpu_in_use_ave=0
#     for i in range(1):
#         total_cost,qpu_in_use = dynamic_programming_partitions(circuit, num_qpus, max_qubits_per_qpu)
#         total_cost_ave+=total_cost
#         qpu_in_use_ave+=qpu_in_use
#     total_cost_ave/=1
#     qpu_in_use_ave/=1
#     print(f"Total stitching cost: {total_cost_ave}")
#     data = pd.DataFrame({
#         'x':  [max_qubits_per_qpu],
#         'stitch': [total_cost_ave],
#         'time':[(time.time()-start_time)/1],
#         'num_qpus':[qpu_in_use_ave]
#         })
#     data.to_csv(save_path, mode='a', header=False, index=False)
    
    
max_qubits_per_qpu=25
repeat_times=1
for repeat_time in range(repeat_times):
    for max_qubits_per_qpu in range(max_qubits_per_qpu,26,10):
        save_path=f"C:/Users/Butch/Desktop/OneDrive - Stony Brook University/TON/FT_perform_evals/Data/Rd/ZS/{max_qubits_per_qpu}_cap.csv"
        with open(save_path,'w') as file:
                file.write("circuit_size,stitch,time,num_qpus\n")
        for Q in range(30,101,10):
            file_path=file_path=f"C:/Users/Butch/Desktop/OneDrive - Stony Brook University/ICDCS_2025/random_circuits_new/{Q}qubits_{Q}layers.txt"
            circuit=Circuit(file_path)
            layers=circuit.layers
            layers=FT_circuit_func(circuit.layers,5)
            L=len(layers)
            num_qpus=500
            start_time=time.time()
            print("max_qubits_per_qpu:",max_qubits_per_qpu)
            total_cost_ave=0
            qpu_in_use_ave=0
            for i in range(1):
                total_cost,qpu_in_use = dynamic_programming_partitions(layers, num_qpus, max_qubits_per_qpu)
                total_cost_ave+=total_cost
                qpu_in_use_ave+=qpu_in_use
            total_cost_ave/=1
            qpu_in_use_ave/=1
            print(f"Total stitching cost: {total_cost_ave}")
            data = pd.DataFrame({
                'circuit_size':  [Q],
                'stitch': [total_cost_ave],
                'time':[(time.time()-start_time)/1],
                'num_qpus':[qpu_in_use_ave]
                })
            data.to_csv(save_path, mode='a', header=False, index=False)
    # dp_result, total_cost = dynamic_programming_partitions(circuit, num_qpus, max_qubits_per_qpu)

    # for layer, partition, cost in dp_result:
    #     print(f"Layer {layer} partition (cost {cost}):")
    #     for qpu, qubits in partition.items():
    #         print(f"  QPU {qpu}: {qubits}")
    # print(f"Total stitching cost: {total_cost}")