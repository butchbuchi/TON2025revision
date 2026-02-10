import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import random
import itertools

random.seed(42)

class Graph:
    def __init__(self, n, p):
        """
        初始化 Graph 类，生成 Erdős-Rényi 随机图。
        
        参数:
        n: 节点的数量
        p: 边的生成概率
        """
        self.n = n  # 节点数量
        self.p = p  # 边的生成概率
        self.G = nx.erdos_renyi_graph(n, p)  # 生成随机图
    
    def print_graph_info(self):
        """
        打印图的节点和边信息。
        """
        print("Nodes:", self.G.nodes())
        print("Edges:", self.G.edges())
    
    def draw_graph(self, edge_colors=None):
        """
        绘制图形并显示。
        
        参数:
        edge_colors: 边的颜色列表，默认为 None。如果提供，则使用指定颜色绘制边。
        """
        if edge_colors:
            # 确保边颜色数量与边数量一致
            if len(edge_colors) < len(self.G.edges()):
                print("Warning: Edge colors list is shorter than the number of edges.")
                edge_colors = edge_colors * (len(self.G.edges()) // len(edge_colors) + 1)
            edge_colors = edge_colors[:len(self.G.edges())]
        else:
            edge_colors = 'black'  # 如果没有提供颜色，则使用默认颜色

        # 绘制图
        nx.draw(self.G, with_labels=True, edge_color=edge_colors)
        plt.show()

# # 示例用法：
# if __name__ == "__main__":
#     n = 4
#     p = 1
#     edge_colors = ['red', 'blue', 'green', 'black']

#     # 创建 Graph 类的实例
#     my_graph = Graph(n, p)

#     # 打印图的节点和边信息
#     my_graph.print_graph_info()

#     # 绘制图
#     my_graph.draw_graph(edge_colors=edge_colors)

class Mapping:
    def __init__(self, topo, n):
        """
        初始化 Mapping 类.
        
        参数:
        topo: nodes topology
        n: number of qubits
        map: list of size n, where each item represents the node which a qubit lands in
        """
        self.n=n
        self.map=[0]*n
        self.topo=topo
    
    ##initialize the qubit mapping randomly
    def initialize(self):
        for i in range(self.n):
            self.map[i]=random.randint(1,self.topo.n)

    ##move q1 to q2's node(teleportate a bit/teledata)
    def teledata(self,q1,q2):
        self.map[q1]=self.map[q2]
        return 1

    def telegate(self,q1,q2):
        return 1


    ## swap two qubits from different nodes
    def swap(self,q1,q2):
        temp=self.map[q1]
        self.map[q1]=self.map[q2]
        self.map[q2]=temp
        return 1

class Circuit:
    def __init__(self,qasm_filelocation):
        """ 
        初始化 Circuit 类.
        
        convert QASM to a list of different timeslots,
        quantum gates in each timeslot are saved a list of tuples
        """
        self.layers,self.num_qubits=analyze_qasm(qasm_filelocation)

    def count_gates(self):
        count=0
        for temp_layers in self.layers:
            for qubit in range(len(temp_layers)):
                if temp_layers[qubit]==-1: continue
                else:
                    count+=0.5
        return count
    #align the circuit at certain timeslot with qubit mapping to find out the remote gates
    def align_with_mapping(self,t,mapping:Mapping):
        #circuit_t is a temp copy of circuit at time t 
        circuit_t=self.layers[t].copy()
        # print(circuit_t)
        for i in range(self.num_qubits):
            # print(circuit_t)
            # print("current pair:",i,circuit_t[i])
            if circuit_t[i]==-1:   continue
            else:
                #if two qubit under 2qubit gates are in the same node, erase them from circuit_t
                if mapping.map[i]==mapping.map[circuit_t[i]]:
                    # print(circuit_t[i],circuit_t[self.layers[t][i]])
                    circuit_t[i]=-1
                    circuit_t[self.layers[t][i]]=-1
                    # print(circuit_t[i],circuit_t[self.layers[t][i]])
        return circuit_t





#transform quantum gates in qasm, group 2-qubit gates by timeslot
def analyze_qasm(qasm_filelocation):
    with open (qasm_filelocation,'r') as file:
        lines=file.readlines()
        #get the number of qubits
        num_qubits=int(lines[0].split("[")[1].split("]")[0])
        #flag_list is used to indicate the timeslot
        flag_list=[-1]*num_qubits   

        #any qubits at any timebin will be labeled -1, unless it's involved in a 2qubit gate
        #gates is the list of gates up to the timebin so far
        gates=[[-1]*num_qubits]
        for line in lines[1:]:
            line=line.strip()
            #if it's a 2qubit gate
            if line.startswith("cx"):
                a,b = tuple(int(q.split("[")[1].split("]")[0]) for q in line.split()[1].split(","))
                if flag_list[a]>=flag_list[b]:
                    flag_list[a]+=1
                    flag_list[b]=flag_list[a]
                else:
                    flag_list[b]+=1
                    flag_list[a]=flag_list[b]
                #the flag_list indicates the timebin so far, 
                while len(gates)<(flag_list[a]+1):
                    gates.append([-1]*num_qubits)
                #we don't care which is the controlling one, just write down the qubit under the same operation
                gates[flag_list[a]][a]=b
                gates[flag_list[b]][b]=a
            else:
                c = int(line.split("[")[1].split("]")[0])
                flag_list[c]+=1
                while len(gates)<(flag_list[c]+1):
                    gates.append([-1]*num_qubits)
    
    return np.array(gates), num_qubits
                
# # print(analyze_qasm("/Users/butch/Desktop/qcirc_construction/10_8_2125.txt"))
# circuit=Circuit("/Users/butch/Desktop/qcirc_construction/10_8_2125.txt")
# graph=Graph(1,1)
# map=Mapping(graph,circuit.num_qubits)
# map.initialize()

# # for t in range(len(circuit.layers)):
# #     print("This is the initial list for remote gates at time {}:".format(t),circuit.align_with_mapping(t,map))

# #multi_gates is temp list to store remote gates at certain timeslot
# multi_gates=[]
# num_engtangle=0

###############################################
# # random test
# for t in range(len(circuit.layers)):
#     multi_gates=circuit.align_with_mapping(t,map)
#     print("This is the list for remote gates at time {}:".format(t), multi_gates)
#     for i in range(circuit.num_qubits):
#         if multi_gates[i]!=-1:
#             num_engtangle+=1
#             # from the random dice and deterministric dice we can see that teledata truely helps.
#             dice=random.randint(1,3)
#             # dice=3
#             if dice==1:
#                 map.telegate(i,multi_gates[i])
#                 multi_gates[multi_gates[i]]=-1
#                 multi_gates[i]=-1
#             elif dice==2:
#                 map.teledata(i,multi_gates[i])
#                 multi_gates[multi_gates[i]]=-1
#                 multi_gates[i]=-1
#             elif dice==3:
#                 map.teledata(multi_gates[i],i)
#                 multi_gates[multi_gates[i]]=-1
#                 multi_gates[i]=-1
# print(num_engtangle)

###############################################


# for t in range(len(circuit.layers)-1):
#     multi_gates=circuit.align_with_mapping(t,map)
#     print("This is the list for remote gates at time {}:".format(t), multi_gates)
#     action_qubit,action_space=compute_action_space(multi_gates)
#     num_engtangle+=len(action_qubit)
#     best_actions=[]
#     best_reward=10000
#     for actions in action_space:
#         temp_map=map
#         for i in range(len(action_qubit)):
#             action=actions[i]
#             if action==1:
#                 temp_map.telegate(action_qubit[i],multi_gates[action_qubit[i]])
#             elif action==2:
#                 temp_map.teledata(action_qubit[i],multi_gates[action_qubit[i]])
#             elif action==3:
#                 temp_map.teledata(multi_gates[action_qubit[i]],action_qubit[i])
#         next_state_action_qubit,_=compute_action_space(circuit.align_with_mapping(t+1,temp_map))
#         reward=len(next_state_action_qubit)
#         if reward < best_reward:
#             best_reward=reward
#             best_actions=actions


#     for i in range(len(best_actions)):
#         action=best_actions[i]
#         if action==1:
#             map.telegate(i,multi_gates[i])
#         elif action==2:
#             map.teledata(i,multi_gates[i])
#         elif action==3:
#             map.teledata(multi_gates[i],i)

# multi_gates=circuit.align_with_mapping(len(circuit.layers)-1,map)
# print("This is the list for remote gates at time {}:".format(len(circuit.layers)-1), multi_gates)
# num_engtangle+=best_reward
# print("greedy:", num_engtangle)

def get_parameters():
    import os
    import pandas as pd
    save_path=f"random_circuits_new/circuit_parameters_skipsingle.csv"
    if not os.path.exists(save_path):  # 如果文件不存在
        with open(save_path, 'w') as f:
            f.write("num_qubit,depth,#CNOT\n")  # 写入内容
    else:
        print(f"The file '{save_path}' already exists. No content was written.")

    for num_qubit in range(30,101,10):
        # d=int(0.1*num_qubit)
        # if d%2==1:
        #     d+=1
        file_path=f"random_circuits_new/{num_qubit}qubits_{num_qubit}layers.txt"
        circuit=Circuit(file_path).layers
        print(len(circuit))
        num_CNOT=0
        #如果某layer只用单比特门，直接忽略
        num_layer=0
        temp=0
        for layer in circuit:
            temp=num_CNOT
            for i in range(num_qubit):
                num_CNOT+=(layer[i]!=-1)
            if num_CNOT>temp:
                num_layer+=1
        num_CNOT/=2
        data = pd.DataFrame({
        'num_qubit':  [num_qubit],
        'depth': [num_layer],
        '#CNOT':[num_CNOT]
        })
        # 追加到 CSV 文件
        data.to_csv(save_path, mode='a', header=False, index=False)

if __name__=="__main__":
    get_parameters()