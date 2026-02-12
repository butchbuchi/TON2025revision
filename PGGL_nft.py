from random import randint,choice
from circuit_utils import Circuit
from matplotlib import pyplot as plt
import random
# from baseline_code import telegate_SA
from tqdm import tqdm
import pandas as pd
from concurrent.futures import ProcessPoolExecutor
import os
import time
import math
import numpy as np
from FT_circuit import FT_circuit_func
import gate_cover_randominit
# from baseline_code.gurobi.gurobi_verification import read_mapping

#this function checks whether the QPU has overflowed
#returns a list of dict containing overflowed qpu and the overflowed number
# random.seed(432)
# np.random.seed(432)
calling_time=12
def check_validity(num_qpu, limit_qpu,map_list):
    usage_qpu_list=[0]*num_qpu 
    for qpu in map_list:
        usage_qpu_list[qpu]+=1
    return [{"qpu":qpu, 'extra_usage':occu-limit_qpu[qpu]} for qpu,occu in enumerate(usage_qpu_list) if occu>limit_qpu[qpu] ]

class Node:
    def __init__(self, num_qubit, num_qpu,layer,limit_qpu=[]):
        self.num_qubit=num_qubit
        self.map=[-1]*self.num_qubit
        self.num_qpu=num_qpu
        self.layer=layer
        self.limit_qpu=limit_qpu
        self.usage_qpu=[0]*self.num_qpu
        
        
#intialize the node: put all relevant qubits in the same node
    def init(self,):
        if self.num_qubit>sum(self.limit_qpu): raise MemoryError("The qpu network is out of memory!")
        temp_layer=self.layer.copy()
        for i in range(len(temp_layer)):
            #if there's a remot gate, put the two qubits in the same random qpu
            if temp_layer[i]==-1:
                temp=choice(self.available_qpu())
                self.map[i]=temp
                self.usage_qpu[temp]+=1
            elif temp_layer[i]>-1:
                if self.available_qpu_two()==[]:
                    temp_layer[temp_layer[i]]=-1
                    temp_layer[i]=-1
                    i-=1
                    continue
                temp=choice(self.available_qpu_two())
                self.map[i]=temp
                self.map[temp_layer[i]]=temp         
                self.usage_qpu[temp]+=2
                temp_layer[temp_layer[i]]=-2
        
        
                
# in init_enhanced(), we always leave one-qubit space free
    def init_enhanced(self,):
        
        self.limit_qpu=[x-1 for x in self.limit_qpu]
        if self.num_qubit>sum(self.limit_qpu): raise MemoryError("The qpu network is out of memory!")
        temp_layer=self.layer.copy()
        current_qpu=0
        anchor=-1
        for i in range(self.num_qubit):
            if self.usage_qpu[current_qpu]==self.limit_qpu[current_qpu]:
                current_qpu+=1
            #if there's a remot gate, put the two qubits in the same random qpu
            if temp_layer[i]==-1:
                if anchor!=-1:
                    self.map[i]=anchor
                    self.usage_qpu[anchor]+=1
                    anchor=-1
                else:
                    self.map[i]=current_qpu
                    self.usage_qpu[current_qpu]+=1
            elif temp_layer[i]>-1:
                if self.usage_qpu[current_qpu]<self.limit_qpu[current_qpu]-1:
                    pass
                else:
                    anchor=current_qpu
                    current_qpu+=1
                self.map[i]=current_qpu
                self.map[temp_layer[i]]=current_qpu
                self.usage_qpu[current_qpu]+=2
                temp_layer[temp_layer[i]]=-2
        self.limit_qpu=[x+1 for x in self.limit_qpu]
        self.num_qpu=current_qpu+1

#
    def shuffle_node(self,):
        qubit_list=list(range(self.num_qubit))
        random.shuffle(qubit_list)
        qpu_list=list(range(self.num_qpu))
        random.shuffle(qpu_list)
        new_node=Node(self.num_qubit, self.num_qpu, self.limit_qpu, self.layer)
        for i in range (self.num_qubit):
            new_node.map[i]=self.map[qubit_list[i]]
            new_node.usage_qpu[new_node.map[i]]+=1

            

    def available_qpu(self):
        available_list=[]
        for i in range(self.num_qpu):
            if self.usage_qpu[i]<self.limit_qpu[i]:
                available_list.append(i)
        return available_list

    def available_qpu_two(self):
        available_list=[]
        for i in range(self.num_qpu):
            if self.usage_qpu[i]<self.limit_qpu[i]-1:
                available_list.append(i)
        return available_list
#check whether involved in two-qubit gates
    def check_gate(self,qubit):
        if self.layer[qubit]!=-1: return True
        else: return False
#check whether involed in local two-qubit gates
    def check_local(self, qubit):
        if self.layer[qubit] == -1:
            raise ValueError(f"the qubit {qubit} is not in any two-qubit gate")
        if self.map[qubit]==self.map[self.layer[qubit]]: return True
        else: return False

    def count_remote_gates(self):
        count=0
        for qubit in range(self.num_qubit):
            if self.check_gate(qubit):
                if self.check_local(qubit): continue
                count+=0.5
        return count

#
    def node_transition(self, map_list):
        self.recursion_times = getattr(self, 'recursion_times', 0)
        if self.recursion_times > 499:
            return

        wrong_list = check_validity(self.num_qpu, self.limit_qpu, map_list)
        if not wrong_list:
            # legal, no modification
            self.map = map_list.copy()
            self.usage_qpu = [map_list.count(i) for i in range(self.num_qpu)]
            return

        wrong_qpu_list = [item['qpu'] for item in wrong_list]
        wrong_usage_list = [item['extra_usage'] for item in wrong_list]

        modified_map_list = map_list.copy()
        for qubit in range(self.num_qubit):
            qpu = map_list[qubit]
            if qpu in wrong_qpu_list and self.map[qubit] != qpu:
                idx = wrong_qpu_list.index(qpu)
                if wrong_usage_list[idx] > 0:
                    wrong_usage_list[idx] -= 1
                    modified_map_list[qubit] = self.map[qubit]

        if not check_validity(self.num_qpu, self.limit_qpu, modified_map_list):
            self.map = modified_map_list.copy()
            self.usage_qpu = [modified_map_list.count(i) for i in range(self.num_qpu)]
            return
        else:
            self.recursion_times += 1
            self.node_transition(modified_map_list)

                

    def find_frequent(self,target_list):
        if len(target_list)==2:
            if target_list[0]==target_list[1]: return target_list[0]
            else: return random.choice(target_list)
        elif len(target_list)==3:
            if target_list[0]==target_list[1] or target_list[0]==target_list[2]: return target_list[0]
            elif target_list[1]==target_list[2]: return target_list[1]
            else: return random.choice(target_list) 
#############################################################################################################################################################################################
    # def PG(self,node_pre,node_next,turbulance=0):
    #     if (node_pre==None and node_next==None): return 
    #     temp_map_list=[]
    #     if node_pre==None:
    #         qubit_list=range(self.num_qubit)           
    #         for qubit in qubit_list:
    #             #add turbulance
    #             #special turbulance for qubit0
    #             if random.random()<turbulance*3 and qubit==0:
    #                 temp_map_list.append(randint(0,self.num_qpu-1))
    #                 continue
    #             #turbulance for other qubits
    #             if random.random()<turbulance:
    #                 temp_map_list.append(randint(0,self.num_qpu-1))
    #                 continue
    #             if self.check_gate(qubit): 
    #                 if self.check_local(qubit):
    #                     if self.map[qubit]==node_next.map[qubit]: 
    #                         temp_map_list.append(self.map[qubit])
    #                         continue
    #                     else:
    #                         if choice([True,False]):
    #                             temp_map_list.append(self.map[qubit])
    #                             continue
    #                         else:  temp_map_list.append(node_next.map[qubit])
    #                         # self.move_qubit(qubit,node_next.map[qubit])
    #                 else:
    #                     if self.map[qubit]==node_next.map[qubit]:
    #                         if choice([True,False]): 
    #                             temp_map_list.append(self.map[qubit])
    #                             continue
    #                         else:temp_map_list.append(node_next.map[qubit])
    #                         # self.move_qubit(qubit,node_next.map[qubit])
    #                     else: temp_map_list.append(node_next.map[qubit])
    #             else:
    #                 if self.map[qubit]==node_next.map[qubit]: 
    #                     temp_map_list.append(self.map[qubit])
    #                     continue
    #                 else: temp_map_list.append(node_next.map[qubit])

    #     elif node_next==None:
    #         qubit_list=range(self.num_qubit)
    #         for qubit in qubit_list:
    #             #add turbulance
    #             #special turbulance for qubit0
    #             if random.random()<turbulance*3 and qubit==0:
    #                 temp_map_list.append(randint(0,self.num_qpu-1))
    #                 continue
    #             #turbulance for other qubits
    #             if random.random()<turbulance:
    #                 temp_map_list.append(randint(0,self.num_qpu-1))
    #                 continue
    #             if self.check_gate(qubit): 
    #                 if self.check_local(qubit):
    #                     if self.map[qubit]==node_pre.map[qubit]: 
    #                         temp_map_list.append(self.map[qubit])
    #                         continue
    #                     else:
    #                         if choice([True,False]):
    #                             temp_map_list.append(self.map[qubit]) 
    #                             continue
    #                         else:temp_map_list.append(node_pre.map[qubit])
    #                         # self.move_qubit(qubit,node_pre.map[qubit])
    #                 else:
    #                     if self.map[qubit]==node_pre.map[qubit]:
    #                         if choice([True,False]): 
    #                             temp_map_list.append(self.map[qubit])
    #                             continue
    #                         else:temp_map_list.append(node_pre.map[qubit])
    #                         # continue
    #                     else: temp_map_list.append(node_pre.map[qubit])
    #             else:
    #                 if self.map[qubit]==node_pre.map[qubit]: 
    #                     temp_map_list.append(self.map[qubit])
    #                     continue
    #                 else:temp_map_list.append(node_pre.map[qubit])

    #     else:
    #         qubit_list=range(self.num_qubit)
    #         for qubit in qubit_list:
    #             #add turbulance
    #             #special turbulance for qubit0
    #             if random.random()<turbulance*3 and qubit==0:
    #                 temp_map_list.append(randint(0,self.num_qpu-1))
    #                 continue
    #             #turbulance for other qubits
    #             if random.random()<turbulance:
    #                 temp_map_list.append(randint(0,self.num_qpu-1))
    #                 continue
    #             if self.check_gate(qubit): 
    #                 if self.check_local(qubit):
    #                     if node_pre.map[qubit]==node_next.map[qubit]:
    #                         if self.map[qubit]==node_pre.map[qubit]: 
    #                             temp_map_list.append(self.map[qubit])
    #                             continue
    #                         else: temp_map_list.append(node_pre.map[qubit])
    #                     else:
    #                         if self.map[qubit]==node_pre.map[qubit] or self.map[qubit]==node_next.map[qubit]: 
    #                             temp_map_list.append(self.map[qubit])
    #                             continue
    #                         # elif self.map[qubit]==node_next.map[qubit]: 
    #                         #     # continue
    #                         #     flag=self.move_qubit(qubit,node_pre.map[qubit]) 
    #                         else:
    #                             random_flag=randint(0,2)
    #                             if random_flag==0: 
    #                                 temp_map_list.append(self.map[qubit])
    #                                 continue
    #                             elif random_flag==1: temp_map_list.append(node_pre.map[qubit])
    #                             else:temp_map_list.append(node_next.map[qubit])
    #                             # random_flag=randint(0,1)
    #                             # if random_flag==0: continue
    #                             # else: 
    #                                 #flag= self.move_qubit(qubit,node_pre.map[qubit]) 
    #                 else:
    #                     if node_pre.map[qubit]==node_next.map[qubit]:
    #                         if self.map[qubit]==node_pre.map[qubit]: 
    #                             temp_map_list.append(self.map[qubit])
    #                         else: temp_map_list.append(node_pre.map[qubit])
    #                     else:###########双比特门中，前后两个不一样
    #                         if self.map[qubit]==node_pre.map[qubit] or self.map[qubit]==node_next.map[qubit]:
    #                             if self.map[self.layer[qubit]]==node_pre.map[qubit] or self.map[self.layer[qubit]]==node_next.map[qubit]:
    #                                 temp_map_list.append(self.map[self.layer[qubit]])
    #                             else:
    #                                 random_flag=randint(0,2)
    #                                 if random_flag==0: 
    #                                     temp_map_list.append(self.map[qubit])
    #                                     continue
    #                                 elif random_flag==1: temp_map_list.append(node_pre.map[qubit])
    #                                 else: temp_map_list.append(node_next.map[qubit])
    #                                 # continue
    #                         else: 
    #                             if self.map[self.layer[qubit]]==node_pre.map[qubit] or self.map[self.layer[qubit]]==node_next.map[qubit]:
    #                                 temp_map_list.append(self.map[self.layer[qubit]])
    #                             else:
    #                                 random_flag=randint(0,2)
    #                                 if random_flag==0: temp_map_list.append(node_pre.map[qubit])
    #                                 elif random_flag==1: temp_map_list.append(node_next.map[qubit])
    #                                 else: temp_map_list.append(self.map[self.layer[qubit]])
    #                                 # flag=self.move_qubit(qubit,node_pre.map[qubit])
    #             else:
    #                 if node_pre.map[qubit]==node_next.map[qubit]:
    #                     if self.map[qubit]==node_pre.map[qubit]: 
    #                         temp_map_list.append(self.map[qubit])
    #                         continue
    #                     else: temp_map_list.append(node_pre.map[qubit])
    #                 else:
    #                     if self.map[qubit]==node_pre.map[qubit]:
    #                         if choice([True,False]):temp_map_list.append(node_next.map[qubit])
    #                         else:temp_map_list.append(self.map[qubit])
    #                     elif self.map[qubit]==node_next.map[qubit]:
    #                         if choice([True,False]): temp_map_list.append(node_pre.map[qubit])
    #                         else:temp_map_list.append(self.map[qubit])
    #                         # flag=self.move_qubit(qubit,node_pre.map[qubit])
    #                     else:
    #                         if choice([True,False]):temp_map_list.append(node_next.map[qubit])
    #                         else : temp_map_list.append(node_pre.map[qubit])
    #                         # flag=self.move_qubit(qubit,node_pre.map[qubit])
    #     self.node_transition(temp_map_list)

#####################################################################################################################################
    def PG(self, node_pre, node_next):
        #need to consider whether pre or next layer exists
        temp_map_list=[]
        if node_pre==None:
            for i in range(self.num_qubit):
                if self.check_gate(i):
                    temp_map_list.append(self.find_frequent([self.map[self.layer[i]],node_next.map[i]]))
                else:
                    temp_map_list.append(node_next.map[i])
        elif node_next==None:
            for i in range(self.num_qubit):
                if self.check_gate(i):
                    temp_map_list.append(self.find_frequent([self.map[self.layer[i]],node_pre.map[i]]))
                else:
                    temp_map_list.append(node_pre.map[i])
        else:
            for i in range(self.num_qubit):
                if self.check_gate(i):
                    temp_map_list.append(self.find_frequent([node_pre.map[i],self.map[self.layer[i]],node_next.map[i]]))
                else:
                    temp_map_list.append(self.find_frequent([node_pre.map[i],node_next.map[i]]))
        self.node_transition(temp_map_list)

    # def GL(self):
    #     for i in range(self.num_qubit):
    #         if self.check_gate(i) and not self.check_local(i):
    #             if self.usage_qpu[self.map[i]]<self.limit_qpu[self.map[i]]:
    #                 self.map[self.layer[i]]=self.map[i]
    #                 self.usage_qpu[self.map[i]]+=1
    #                 self.usage_qpu[self.map[self.layer[i]]]-=1

#############################################################################################################################################################################################
    # def GL1(self, node_pre,cosistency_weight):
    #         if (node_pre==None ): return
    #         qubit_list=range(self.num_qubit)
    #         temp_map_list=[]
    #         for qubit in qubit_list:
    #             if self.check_gate(qubit): 
    #                 if self.check_local(qubit):
    #                     if node_pre.map[qubit]==node_pre.map[qubit]: 
    #                         temp_map_list.append(self.map[qubit])
    #                         continue
    #                     else:
    #                         if random.random()<cosistency_weight: temp_map_list.append(node_pre.map[qubit])
    #                         else:temp_map_list.append(self.map[qubit])
    #                 else:
    #                     if node_pre.map[qubit]==node_pre.map[qubit]: 
    #                         if random.random()<cosistency_weight:  temp_map_list.append(self.map[qubit])
    #                         else: temp_map_list.append(self.map[self.layer[qubit]])
    #                     else:
    #                         if random.random()<cosistency_weight: temp_map_list.append(node_pre.map[qubit])
    #                         else:                          temp_map_list.append(self.map[self.layer[qubit]])
    #             else:
    #                 if node_pre.map[qubit]==node_pre.map[qubit]: 
    #                     temp_map_list.append(self.map[qubit])
    #                     continue
    #                 else: temp_map_list.append(node_pre.map[qubit])
    #         self.node_transition(temp_map_list)

    # def GL2(self, node_next,consistency_weight):
    #     if (node_next==None ): return
    #     qubit_list=range(self.num_qubit)
    #     temp_map_list=[]
    #     for qubit in qubit_list:
    #         flag=1
    #         if self.check_gate(qubit): 
    #             if self.check_local(qubit):
    #                 if node_next.map[qubit]==node_next.map[qubit]: 
    #                     temp_map_list.append(self.map[qubit])
    #                     continue
    #                 else:
    #                     if random.random()<consistency_weight: temp_map_list.append(node_next.map[qubit])
    #                     else:temp_map_list.append(self.map[qubit])
    #             else:
    #                 if node_next.map[qubit]==node_next.map[qubit]: 
    #                     if random.random()<consistency_weight: temp_map_list.append(self.map[qubit])
    #                     else:temp_map_list.append(self.map[self.layer[qubit]])
    #                 else:
    #                     if random.random()<consistency_weight: temp_map_list.append(node_next.map[qubit])
    #                     else:                           temp_map_list.append(self.map[self.layer[qubit]])
    #         else:
    #             if node_next.map[qubit]==node_next.map[qubit]:
    #                 temp_map_list.append(self.map[qubit])
    #                 continue
    #             else: temp_map_list.append(node_next.map[qubit])  
    #     self.node_transition(temp_map_list) 
    #####################################################################################################################################
    def GL(self, node_pre,node_next):
        temp_map_list=[]
        if node_pre==None:
            for i in range(self.num_qubit):
                if self.check_gate(i):
                    temp_map_list.append(random.choice([self.map[i],self.map[self.layer[i]],node_next.map[i]]))
                else:
                    temp_map_list.append(random.choice([self.map[i],node_next.map[i]]))
        elif node_next==None:
            for i in range(self.num_qubit):
                if self.check_gate(i):
                    temp_map_list.append(random.choice([self.map[i],self.map[self.layer[i]],node_pre.map[i]]))
                else:
                    temp_map_list.append(random.choice([self.map[i],node_pre.map[i]]))
        else:
            for i in range(self.num_qubit):
                if self.check_gate(i):
                    temp_map_list.append(random.choice([self.map[i],node_pre.map[i],self.map[self.layer[i]],node_next.map[i]]))
                else:
                    temp_map_list.append(random.choice([self.map[i],node_pre.map[i],node_next.map[i]]))
        self.node_transition(temp_map_list)

#############################################################################################################################################################################################



def cost(self,node_pre,node_next,):
    cost=0
    temp_layer=self.layer.copy()
    #compute the remote gates in one node
    for qubit in range(self.num_qubit):
        if temp_layer[qubit]==-1: continue
        else:
            #if two revelant qubits are in the same qpu,cost+1 
            if self.map[qubit]!=self.map[temp_layer[qubit]]: cost+=1
            temp_layer[temp_layer[qubit]]=-1
    #compute the cost of moving qubits
    if node_pre==None:
        pass
    else:
        for qubit in range(self.num_qubit):
            #################################################cost=1 in mode0;cost=0.5 in mode1
            if self.map[qubit]!=node_pre.map[qubit]: cost+=1
    if node_next==None:
        pass
    else:
        for qubit in range(self.num_qubit):
            if self.map[qubit]!=node_next.map[qubit]: cost+=1
    return cost
                
def total_cost(nodes):
    cost = 0
    if len(nodes) == 1: 
        return nodes[0].count_remote_gates()
    for i in range(len(nodes) - 1):
        cost += nodes[i].count_remote_gates()
        for j in range(nodes[i].num_qubit):
            if nodes[i].map[j] != nodes[i + 1].map[j]: 
                cost += 1
    cost += nodes[-1].count_remote_gates()
    return cost

def total_remote_gates(nodes):
    cost=0
    for i in range(len(nodes)):
        cost+=nodes[i].count_remote_gates()
    return cost

def total_PG(nodes):
    for i in range(len(nodes)):
        if i==0: nodes[i].PG(None,nodes[i+1])
        elif i==(len(nodes)-1): nodes[i].PG(nodes[i-1],None)
        else:
            nodes[i].PG(nodes[i-1],nodes[i+1])

def total_GL(nodes):
    for i in range(len(nodes)):
        if i==0: nodes[i].GL(None,nodes[i+1])
        elif i==(len(nodes)-1): nodes[i].GL(nodes[i-1],None)
        else:nodes[i].GL(nodes[i-1],nodes[i+1])
# def total_GL1(nodes,   consistency_weight):
#     for i in range(len(nodes)):
#         if len(nodes)==1: nodes[0].GL1()
#         else:
#             if i==0: nodes[i].GL1(None,consistency_weight)
#             else:
#                 nodes[i].GL1(nodes[i-1],consistency_weight)
# def total_GL2(nodes,   consistency_weight):
#     for i in range(len(nodes)):
#         if len(nodes)==1: nodes[0].GL2()
#         else:
#             if i==(len(nodes)-1): nodes[i].GL2(None,consistency_weight)
#             else:
#                 nodes[i].GL2(nodes[i+1],consistency_weight)

#The FTQC circuit conversion is included in optimize_under function
def optimize_under(file_path,num_qpu,limit_qpu,epochs,anastz=None,anastz_mode=None,print_nodes=False,compute_cost=True,randomize=False,turbulance=0):
    cooling_rate=1 
    correcting_period=5
    circuit=Circuit(file_path)
    layers=circuit.layers
    print("Original_circuit layers shape",circuit.layers.T.shape)
    num_qubit=circuit.num_qubits
    # num_qpu=math.ceil(num_qubit/limit_qpu)
    
    nodes = [Node(num_qubit, num_qpu,  layer,limit_qpu) for layer in layers]
    

    if anastz is None :
        for i in range(len(layers)):
            nodes[i]=Node(num_qubit, num_qpu,layers[i],limit_qpu)
            nodes[i].init_enhanced()

        # if randomize:
        #     nodes=randomize_mappings(num_qubit, limit_qpu,layers)
        # for node in nodes:
        #     print(node.map)
        #使每个节点一致
        

    else:
        if anastz_mode == "telegate":
            for node in nodes:
                node.map=anastz.copy()
                for i in range(node.num_qpu):
                    node.usage_qpu[i] = len([qpu for qpu in node.map if qpu == i])
        elif anastz_mode == "hybrid":
             for i in range(len(nodes)):
                nodes[i].map=anastz[i].copy()
                for j in range(nodes[i].num_qpu):
                    nodes[i].usage_qpu[j] = len([qpu for qpu in nodes[i].map if qpu == j])
        elif anastz_mode == "gatecover":
            for i in range(len(nodes)):
                nodes[i].map=anastz[i].copy()
                for j in range(nodes[i].num_qpu):
                    nodes[i].usage_qpu[j] = len([qpu for qpu in nodes[i].map if qpu == j])
    # for node in nodes:
    #     node.shuffle_node()
    
    num_qpu=max(node.num_qpu for node in nodes )

            
    for node in nodes:
        node.num_qpu=num_qpu



    # initail_interval=1
    # cycle=50
    # # initail_interval=2
    # # cycle=50
    # interval=initail_interval
    # interval_attenuation=True
    # #consistency_weight for crit2/3
    # consistency_weight=0
    
    # for epoch in (range(1,epochs+1)):
    #     # if epoch>200 and epoch%200==0:
    #     #     cycle=int(0.9*cycle)
    #     # turbulance*=cooling_rate
    #     check_point_1=interval
    #     check_point_2=check_point_1+(cycle-2*interval)//2
    #     check_point_3=check_point_2+interval
    #     interval_attenuation=False
    #     if epoch<100:
    #         total_PG(nodes)
    #     if epoch%cycle<check_point_1:
    #         total_GL1(nodes,consistency_weight)
    #         # PG(nodes)
    #         #test code
    #     elif epoch%cycle<check_point_2:total_PG(nodes)
    #     elif epoch%cycle<check_point_3-1:
    #         total_GL2(nodes,consistency_weight)
    #         # PG(nodes)
    #     elif epoch%cycle==check_point_3:total_PG(nodes)
    #     # elif epoch%cycle==check_point_3:total_optimize_random_swap(nodes)
    #     else: 
    #         total_PG(nodes)
            
    #     # print("{}/{} epochs optimized".format(epoch,epochs))
    #     # if interval_attenuation:
    #     #     interval=int((epoch/epochs)*initail_interval)
            
    # for epoch in (range(epochs+1 ,epochs+101)): 
    #     total_PG(nodes)
    cycle=50
    cost=1e9
    for epoch in range(100):
        total_PG(nodes)
    for epoch in range (100,epochs-100):
        if epoch%cycle==0:
            cost=min(cost,total_cost(nodes))
            total_GL(nodes)
        else:
            total_PG(nodes)
    for epoch in range(epochs-100,epochs):
        total_PG(nodes)
        
        # print("{}/{} epochs optimized".format(epoch,epochs))
    cost=min(cost,total_cost(nodes))
    remote_cost_list=total_remote_gates(nodes)
    max_QPU=0
    for node in nodes:
        if max(node.map)>max_QPU:
            max_QPU=max(node.map)
    if print_nodes:
        best_mappings=[node.map for node in nodes]
        return cost,remote_cost_list, max_QPU+1, best_mappings
    return cost,remote_cost_list, max_QPU+1

def experiment_qft_constant_limit(L,run_id,num_qpu,limit_qpu,circuit_type="QFT",seed=None,SA=False,repeat_times=1,anastz=None,anastz_mode=None,print_nodes=False,plusGC=False):
    random.seed(seed)
    np.random.seed(seed)
    global calling_time
    calling_time+=1
    for repeat_time in range(repeat_times):
        epochs=1000
        x=[]
        y_local_reg=[]
        qpu_in_use=[]
        time_list=[]
        telegate_cost=[]
        teledata_cost=[]

        if anastz is not None:
            output_dir = f"NFT_perform_evals/Data/{circuit_type}/GCLABUBU/{limit_qpu[0]}_cap"
        elif plusGC:
            output_dir = f"NFT_perform_evals/Data/{circuit_type}/LABUBUGC/{limit_qpu[0]}_cap"
        else:
            output_dir = f"NFT_perform_evals/Data/{circuit_type}/PGGL/{limit_qpu[0]}_cap"
        os.makedirs(output_dir, exist_ok=True)
        output_file = f"{output_dir}/{run_id}.csv"

        # 写入表头（如果文件不存在）
        if not os.path.exists(output_file):
            pd.DataFrame(columns=[
                'circuit_size', 'y_local_reg', 'telegate_cost',
                'teledata_cost', 'num_qpu', 'time'
            ]).to_csv(output_file, index=False)

        # for i in range(1,9):
        #     num_qubit=math.ceil((i+0.5)*L)
        for num_qubit in (range(30,101,10)):
            if circuit_type=="QFT":
                 file_path = rf"C:\Users\Butch\OneDrive - Stony Brook University\ICDCS_2025\qft_circuits\qft_circuit({num_qubit}qubits).txt"
            else:
                file_path=f"C:/Users/Butch/Desktop/OneDrive - Stony Brook University/ICDCS_2025/random_circuits_new/{num_qubit}qubits_{num_qubit}layers.txt"

            ave_cost = 0
            ave_max_QPU = 0
            ave_remote_cost = 0
            start_time = time.time()

            for k in range(1):
                if anastz is not None:
                    circuit = gate_cover_randominit.Circuit(file_path)
                    results=gate_cover_randominit.gate_cover(circuit.layers,L,lookahead_gates=1e9)
                    anastz=results["mapping_by_layer"]
                    total_epr = sum(op.get("n_epr", 0) for op in results["D"])
                    print(f"Total EPR pairs used in gate cover: {total_epr}")
                if print_nodes:
                    cost, remote_cost_list, max_QPU, best_mappings = optimize_under(
                        file_path, num_qpu, limit_qpu, epochs,
                        anastz=anastz, anastz_mode=anastz_mode, print_nodes=print_nodes
                    )
                else:
                    cost, remote_cost_list, max_QPU = optimize_under(
                        file_path, num_qpu, limit_qpu, epochs,
                        anastz=anastz, anastz_mode=anastz_mode, print_nodes=print_nodes
                    )
                print(f"Cost after Labubu: {cost}")
                if plusGC:
                    assert print_nodes, "to use plusGC, print_nodes must be True to get the best_mappings from optimize_under"
                    results = gate_cover_randominit.gate_cover(circuit.layers, L, lookahead_gates=1e9, initial_mapping=best_mappings)
                    cost = sum(op.get("n_epr", 0) for op in results["D"])
                    remote_cost_list = sum(
                        op.get("n_epr", 0)
                        for op in results["D"]
                        if op.get("op") == "TELEGATE"
                    )
                    print(f"Cost after plusGC: {cost}")
                ave_cost += cost
                ave_max_QPU += max_QPU
                ave_remote_cost += remote_cost_list

            elapsed_time = (time.time() - start_time)
            ave_cost /= 1
            ave_max_QPU /= 1
            ave_remote_cost /= 1

            # 当前这一项的数据
            row = {
                'circuit_size': num_qubit,
                'y_local_reg': ave_cost,
                'telegate_cost': ave_remote_cost,
                'teledata_cost': ave_cost - ave_remote_cost,
                'num_qpu': ave_max_QPU,
                'time': elapsed_time
            }

            # 每次追加写入一行
            pd.DataFrame([row]).to_csv(output_file, mode='a', header=False, index=False)
        
        # for num_qubit in (range(30,101,10)):
        #     # d=int(0.1*num_qubit)
        #     # if d%2==1:
        #     #     d+=1
        #     file_path=f"C:/Users/Butch/Desktop/OneDrive - Stony Brook University/ICDCS_2025/random_circuits_new/{num_qubit}qubits_{num_qubit}layers.txt"
        #     # sa_cost=y_SA[limit_qpu-2]
        #     ave_cost=0
        #     ave_max_QPU=0
        #     ave_remote_cost=0
        #     start_time=time.time()
        #     for k in range(1):
        #         cost,remote_cost_list,max_QPU=optimize_under(file_path,num_qpu,limit_qpu,epochs,anastz=None,anastz_mode=False,print_nodes=False)
        #         ave_cost+=cost
        #         ave_max_QPU+=max_QPU
        #         ave_remote_cost+=remote_cost_list
        #     time_list.append((time.time()-start_time)/1)
        #     ave_cost/=1
        #     ave_max_QPU/=1
        #     ave_remote_cost/=1
        #     telegate_cost.append(ave_remote_cost)
        #     teledata_cost.append(ave_cost-ave_remote_cost)
        #     y_local_reg.append(ave_cost)
        #     x.append(num_qubit)  
        #     qpu_in_use.append(ave_max_QPU)
        
        # data = pd.DataFrame({
        # 'circuit_size': x,
        # # 'y_SA': y_SA[3:],
        # 'y_local_reg': y_local_reg,
        # 'telegate_cost':telegate_cost,
        # 'teledata_cost':teledata_cost,
        # # 'percentage':percentage,
        # 'num_qpu':qpu_in_use,
        # 'time':time_list
        # })

        # output_dir = f"FT_perform_evals/parallel_processing_Data/Rd/PGGL/{limit_qpu[0]}_cap"
        # os.makedirs(output_dir, exist_ok=True)
        # data.to_csv(f"{output_dir}/{run_id}.csv", index=False)
        # plt.show()


for n in tqdm([25,15,5]):
# for n in tqdm([15]):
    mean=n
    std_dev = 0
    num_qpu=300
    # anastz="gatecover"
    anastz=None
    qpu_limit=[int(round(random.gauss(mean,std_dev))) for _ in range(num_qpu)]
    sorted_qpu_limit=sorted(qpu_limit,reverse=True)
    # print(sorted_qpu_limit)
    experiment_qft_constant_limit(n,run_id=4,num_qpu=num_qpu,limit_qpu=sorted_qpu_limit,seed=1,repeat_times=1, anastz=anastz,anastz_mode=None, print_nodes=True, plusGC=True)

#count the number of CX gates in the FT circuit
# for circuit_size in range(30,101,10):
#     circuit=Circuit(f"C:/Users/Butch/Desktop/OneDrive - Stony Brook University/ICDCS_2025/random_circuits_new/{circuit_size}qubits_{circuit_size}layers.txt")
#     layers=FT_circuit_func(circuit.layers,5)
#     print("Original_circuit layers shape",circuit.layers.T.shape)
#     print("FT_circuit layers shape",layers.T.shape)
#     num_cx=0
#     for i in range(len(circuit.layers)):
#         for j in range(len(circuit.layers[i])):
#             if circuit.layers[i][j]!=-1:
#                 num_cx+=1
#     num_cx/=2
#     print(f"Number of CX gates in the origin circuit{circuit_size}:", num_cx)

#     num_cx=0
#     for i in range(len(layers)):
#         for j in range(len(layers[i])):
#             if layers[i][j]!=-1:
#                 num_cx+=1
#     num_cx/=2
#     print(f"Number of CX gates in the FT circuit{circuit_size}:", num_cx)

#cost of random mappings
# def random_mappings(num_qubit, limit_qpu, layers):
#     map_list = [-1] * num_qubit
#     num_qpu = math.ceil(num_qubit / limit_qpu)
#     shuffled_list = list(range(num_qubit))
#     random.shuffle(shuffled_list)
#     count = 0
#     index=0
#     for i in range(num_qubit):
#         map_list[shuffled_list[i]]=index
#         count += 1
#         if count==limit_qpu:
#             count = 0 
#             index += 1
#     nodes = [Node(num_qubit, num_qpu, layer, limit_qpu) for layer in layers]
#     for node in nodes:
#         node.map = map_list.copy()
#         for i in range(node.num_qpu):
#             node.usage_qpu[i] = len([qpu for qpu in node.map if qpu == i])
#     return nodes
# for circuit_size in range(30,101,10):
#     for limit_qpu in range(5,26,10):
#         circuit=Circuit(f"C:/Users/Butch/Desktop/OneDrive - Stony Brook University/ICDCS_2025/random_circuits_new/{circuit_size}qubits_{circuit_size}layers.txt")
#         layers=circuit.layers
#         nodes=random_mappings(circuit.num_qubits, limit_qpu, layers)
#         print(f"cost of random mappings for {circuit_size} qubits and size {limit_qpu} qpus:", total_cost(nodes))

