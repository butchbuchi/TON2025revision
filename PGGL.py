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

def get_unique_filename(base_path):
    if not os.path.exists(base_path):
        return base_path
    base, ext = os.path.splitext(base_path)
    counter = 1
    new_path = f"{base}_{counter}{ext}"
    while os.path.exists(new_path):
        counter += 1
        new_path = f"{base}_{counter}{ext}"
    return new_path
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
    def init_enhanced(self,extra_space=1):
        # print("The original limit of QPU is",self.limit_qpu)
        # print("The extra space is",extra_space)
        self.limit_qpu=[x-extra_space for x in self.limit_qpu]
        # print("The new limit of QPU is",self.limit_qpu)
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
        self.limit_qpu=[x+extra_space for x in self.limit_qpu]
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

#########################################################################################################################################################################################
    def PG(self, node_pre, node_next,PG_one_direct=False,trans=False):
        if trans:
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
        
        else:
            #need to consider whether pre or next layer exists
            if node_pre==None:
                for i in range(self.num_qubit):
                    if self.check_gate(i):
                        temp=self.find_frequent([self.map[self.layer[i]],node_next.map[i]])
                        if self.usage_qpu[temp]<self.limit_qpu[temp]:     
                            self.usage_qpu[temp]+=1
                            self.usage_qpu[self.map[i]]-=1
                            self.map[i]=temp
                    else:
                        temp=node_next.map[i]
                        if self.usage_qpu[temp]<self.limit_qpu[temp]:
                            self.usage_qpu[temp]+=1
                            self.usage_qpu[self.map[i]]-=1
                            self.map[i]=temp
            elif node_next==None:
                for i in range(self.num_qubit):
                    if self.check_gate(i):
                        temp=self.find_frequent([self.map[self.layer[i]],node_pre.map[i]])
                        if self.usage_qpu[temp]<self.limit_qpu[temp]:
                            self.usage_qpu[temp]+=1
                            self.usage_qpu[self.map[i]]-=1
                            self.map[i]=temp
                    else:
                        temp=node_pre.map[i]
                        if self.usage_qpu[temp]<self.limit_qpu[temp]:   
                            self.usage_qpu[temp]+=1
                            self.usage_qpu[self.map[i]]-=1
                            self.map[i]=temp
            else:
                for i in range(self.num_qubit):
                    if self.check_gate(i):
                        temp=self.find_frequent([node_pre.map[i],self.map[self.layer[i]],node_next.map[i]])
                        if self.usage_qpu[temp]<self.limit_qpu[temp]:
                            self.usage_qpu[temp]+=1
                            self.usage_qpu[self.map[i]]-=1
                            self.map[i]=temp
                    else:
                        if PG_one_direct:
                            temp=node_pre.map[i]
                        else:
                            temp=self.find_frequent([node_pre.map[i],node_next.map[i]])
                        if self.usage_qpu[temp]<self.limit_qpu[temp]:
                            self.usage_qpu[temp]+=1
                            self.usage_qpu[self.map[i]]-=1
                            self.map[i]=temp
########################################################################################################################################Use transition function to update the node

    
##########################################################################################################################################################################################
    # def GL(self):
    #     for i in range(self.num_qubit):
    #         if self.check_gate(i) and not self.check_local(i):
    #             if self.usage_qpu[self.map[i]]<self.limit_qpu[self.map[i]]:
    #                 self.map[self.layer[i]]=self.map[i]
    #                 self.usage_qpu[self.map[i]]+=1
    #                 self.usage_qpu[self.map[self.layer[i]]]-=1
##########################################################################################################################################################################################
    def GL(self, node_pre,node_next,trans=False):
        if trans: 
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
        else:
            if node_pre==None:
                for i in range(self.num_qubit):
                    if self.check_gate(i):
                        temp=random.choice([self.map[i],self.map[self.layer[i]],node_next.map[i]])
                        if self.usage_qpu[temp]<self.limit_qpu[temp]:                           
                            self.usage_qpu[temp]+=1
                            self.usage_qpu[self.map[i]]-=1
                            self.map[i]=temp
                        
                    else:
                        temp=random.choice([self.map[i],node_next.map[i]])
                        if self.usage_qpu[temp]<self.limit_qpu[temp]:                           
                            self.usage_qpu[temp]+=1
                            self.usage_qpu[self.map[i]]-=1
                            self.map[i]=temp  
            elif node_next==None:
                for i in range(self.num_qubit):
                    if self.check_gate(i):
                        temp=random.choice([self.map[i],self.map[self.layer[i]],node_pre.map[i]])
                        if self.usage_qpu[temp]<self.limit_qpu[temp]:                          
                            self.usage_qpu[temp]+=1
                            self.usage_qpu[self.map[i]]-=1
                            self.map[i]=temp
                    else:
                        temp=random.choice([self.map[i],node_pre.map[i]])
                        if self.usage_qpu[temp]<self.limit_qpu[temp]:
                            self.usage_qpu[temp]+=1
                            self.usage_qpu[self.map[i]]-=1           
                            self.map[i]=temp          
            else:
                for i in range(self.num_qubit):
                    if self.check_gate(i):
                        temp=random.choice([self.map[i],node_pre.map[i],self.map[self.layer[i]],node_next.map[i]])
                        if self.usage_qpu[temp]<self.limit_qpu[temp]:                            
                            self.usage_qpu[temp]+=1
                            self.usage_qpu[self.map[i]]-=1
                            self.map[i]=temp
                    else:
                        temp=random.choice([self.map[i],node_pre.map[i],node_next.map[i]])
                        if self.usage_qpu[temp]<self.limit_qpu[temp]:                           
                            self.usage_qpu[temp]+=1
                            self.usage_qpu[self.map[i]]-=1
                            self.map[i]=temp
########################################################################################################################################Use transition function to update the node

    
##########################################################################################################################################################################################

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

def total_PG(nodes,PG_one_direct=False,trans=False):
    for i in range(len(nodes)):
        if i==0: nodes[i].PG(None,nodes[i+1],PG_one_direct=PG_one_direct,trans=trans)
        elif i==(len(nodes)-1): nodes[i].PG(nodes[i-1],None,PG_one_direct=PG_one_direct,trans=trans)
        else:
            nodes[i].PG(nodes[i-1],nodes[i+1],PG_one_direct=PG_one_direct,trans=trans)

def total_GL(nodes):
    for i in range(len(nodes)):
        if i==0: nodes[i].GL(None,nodes[i+1])
        elif i==(len(nodes)-1): nodes[i].GL(nodes[i-1],None)
        else:nodes[i].GL(nodes[i-1],nodes[i+1])
        
#The FTQC circuit conversion is included in optimize_under function
def optimize_under(file_path,num_qpu,limit_qpu,epochs,anastz=None,anastz_mode=None,print_nodes=False,compute_cost=True,randomize=False,turbulance=0,training_mode=False,PG_mode=False,FT_mode=True,period=50,GL_start_point=100,PG_one_direct=False,extra_space=1,trans=False):
    cooling_rate=1 
    correcting_period=5
    circuit=Circuit(file_path)
    if FT_mode:
        layers=FT_circuit_func(circuit.layers,correcting_period)
        # print("Original_circuit layers shape",circuit.layers.T.shape)
        # print("FT_circuit layers shape",layers.T.shape)
        num_qubit=circuit.num_qubits*8
    else:
        layers=circuit.layers
        # print("Original_circuit layers shape",circuit.layers.T.shape)
        num_qubit=circuit.num_qubits
    # num_qpu=math.ceil(num_qubit/limit_qpu)
    
    nodes = [Node(num_qubit, num_qpu,  layer,limit_qpu) for layer in layers]
    

    if anastz is None :
        for i in range(len(layers)):
            nodes[i]=Node(num_qubit, num_qpu,layers[i],limit_qpu)
            nodes[i].init_enhanced(extra_space=extra_space)


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
    # for node in nodes:
    #     node.shuffle_node()
    
    num_qpu=max(node.num_qpu for node in nodes )

            
    for node in nodes:
        node.num_qpu=num_qpu

    
            
    cycle=period
    if training_mode:training_cost=[total_cost(nodes)]##training_mode is used for iterative_progress
    if PG_mode:##PG_mode use only PG, no GL
        for epoch in range(epochs):
            total_PG(nodes,PG_one_direct=PG_one_direct,trans=trans)
            if training_mode:
                training_cost.append(total_cost(nodes))
        if training_mode:
            return training_cost
        else:
            cost=total_cost(nodes)
            remote_cost_list=total_remote_gates(nodes)
            max_QPU=0
            for node in nodes:
                if max(node.map)>max_QPU:
                    max_QPU=max(node.map)
            return cost,remote_cost_list, max_QPU+1
    for epoch in range(GL_start_point):
        total_PG(nodes,PG_one_direct=PG_one_direct,trans=trans)
        if training_mode:
            training_cost.append(total_cost(nodes))
    for epoch in range (GL_start_point,epochs-GL_start_point):
        if epoch%cycle==0:
            total_GL(nodes,)
        else:
            total_PG(nodes,PG_one_direct=PG_one_direct,trans=trans)
        if training_mode:
            training_cost.append(total_cost(nodes))
    for epoch in range(epochs-GL_start_point,epochs):
        total_PG(nodes,PG_one_direct=PG_one_direct,trans=trans)
        if training_mode:
            training_cost.append(total_cost(nodes))
        
        # print("{}/{} epochs optimized".format(epoch,epochs))
    if training_mode:
        return training_cost
    cost=total_cost(nodes)
    remote_cost_list=total_remote_gates(nodes)
    max_QPU=0
    for node in nodes:
        if max(node.map)>max_QPU:
            max_QPU=max(node.map)
    return cost,remote_cost_list, max_QPU+1

def random_mapping(circuit_type='QFT', num_qubit=30, limit_qpu=25,num_qpu=300, seed=4321):
    random.seed(seed)
    np.random.seed(seed)
    if circuit_type == 'QFT':
        file_path = f"C:/Users/Butch/Desktop/OneDrive - Stony Brook University/ICDCS_2025/qft_circuits/qft_circuit({num_qubit}qubits).txt"
    elif circuit_type == 'Rd':
        file_path = f"C:/Users/Butch/Desktop/OneDrive - Stony Brook University/ICDCS_2025/random_circuits_new/{num_qubit}qubits_{num_qubit}layers.txt"
    # create the output directory if it doesn't exist
    output_dir = f"C:/Users/Butch/Desktop/OneDrive - Stony Brook University/TON/NFT_perform_evals/Data_random/{circuit_type}"
    os.makedirs(output_dir, exist_ok=True)
    output_file = f"{output_dir}/{limit_qpu}_cap.csv"


    # 写入表头（如果文件不存在）
    if not os.path.exists(output_file):
        pd.DataFrame(columns=[
            'circuit_size', 'y_local_reg'
        ]).to_csv(output_file, index=False)


    circuit = Circuit(file_path)
    layers = circuit.layers
    shuffled_list = list(range(circuit.num_qubits))
    random.shuffle(shuffled_list)

    nodes = [Node(num_qubit, num_qpu,  layer,limit_qpu) for layer in layers]

    node=nodes[0]
    node.map = [-1] * num_qubit
    count = 0
    index = 0
    for i in shuffled_list:
        node.map[i] = index
        count += 1
        if count == limit_qpu:
            count = 0 
            index += 1
    node.usage_qpu = [node.map.count(i) for i in range(num_qpu)]

    for i in range(1,len(nodes)):
        nodes[i].map = node.map.copy()
        nodes[i].usage_qpu = node.usage_qpu.copy()


    num_qpu=max(node.num_qpu for node in nodes )
            
    for node in nodes:
        node.num_qpu=num_qpu
    
    random_cost = total_cost(nodes)
    # 当前这一项的数据
    row = {
        'circuit_size': num_qubit,
        'y_local_reg': random_cost
    }

    # 每次追加写入一行
    pd.DataFrame([row]).to_csv(output_file, mode='a', header=False, index=False)
    print(f"Random mapping cost for {circuit_type}{num_qubit} with {limit_qpu} limit per QPU: ", random_cost) 

def experiment_qft_constant_limit(run_id,num_qpu,limit_qpu,seed,circuit_size=list(range(30,101,10)),epochs=1000,SA=False,repeat_times=1,PG_one_direct=False, Circuit_type="Rd",PG_mode=False,FT_mode=True,period=50,GL_start_point=100,extra_space=1,multi_process=False,trans=False):
    random.seed(seed)
    np.random.seed(seed)
    global calling_time
    calling_time+=1
    for repeat_time in range(repeat_times):
        epochs=epochs
        x=[]
        y_local_reg=[]
        qpu_in_use=[]
        time_list=[]
        telegate_cost=[]
        teledata_cost=[]
        if trans: trans_type="trans"
        else: trans_type="notrans"
        if multi_process:
            if PG_mode:
                if FT_mode:
                    output_dir = f"FT_perform_evals/parallel_processing_Data_{trans_type}/{Circuit_type}/PG/{limit_qpu[0]}_cap/{extra_space}_extra_space"
                else:
                    output_dir = f"NFT_perform_evals/parallel_processing_Data_{trans_type}/{Circuit_type}/PG/{limit_qpu[0]}_cap/{extra_space}_extra_space"
            else:
                if FT_mode:
                    output_dir = f"FT_perform_evals/parallel_processing_Data_{trans_type}/{Circuit_type}/PGGL/{limit_qpu[0]}_cap/{extra_space}_extra_space"
                else:
                    output_dir = f"NFT_perform_evals/parallel_processing_Data_{trans_type}/{Circuit_type}/PGGL/{limit_qpu[0]}_cap/{extra_space}_extra_space"
        else:
            if PG_mode:
                if FT_mode:
                    output_dir = f"FT_perform_evals/Data_{trans_type}/{Circuit_type}/PG/{limit_qpu[0]}_cap/{extra_space}_extra_space"
                else:
                    output_dir = f"NFT_perform_evals/Data_{trans_type}/{Circuit_type}/PG/{limit_qpu[0]}_cap/{extra_space}_extra_space"
            else:
                if FT_mode:
                    output_dir = f"FT_perform_evals/Data_{trans_type}/{Circuit_type}/PGGL/{limit_qpu[0]}_cap/{extra_space}_extra_space"
                else:
                    output_dir = f"NFT_perform_evals/Data_{trans_type}/{Circuit_type}/PGGL/{limit_qpu[0]}_cap/{extra_space}_extra_space"
        # create the output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        if PG_one_direct:
            output_file = f"{output_dir}/{run_id}.csv"
        else:
            output_file = f"{output_dir}/{run_id}.csv"
        # ensure the output file has a unique name
        output_file = get_unique_filename(output_file)
    


        # 写入表头（如果文件不存在）
        if not os.path.exists(output_file):
            pd.DataFrame(columns=[
                'circuit_size', 'y_local_reg', 'telegate_cost',
                'teledata_cost', 'num_qpu', 'time'
            ]).to_csv(output_file, index=False)

        for num_qubit in circuit_size:
            if Circuit_type=="Rd":
                file_path = f"C:/Users/Butch/Desktop/OneDrive - Stony Brook University/ICDCS_2025/random_circuits_new/{num_qubit}qubits_{num_qubit}layers.txt"
            elif Circuit_type=="QFT":
                file_path = f"C:/Users/Butch/Desktop/OneDrive - Stony Brook University/ICDCS_2025/qft_circuits/qft_circuit({num_qubit}qubits).txt"

            ave_cost = 0
            ave_max_QPU = 0
            ave_remote_cost = 0
            start_time = time.time()
            
            print(f"{limit_qpu[0]}_cap,{num_qubit}_{Circuit_type} in progress...", flush=True)
            for k in range(1):
                cost, remote_cost_list, max_QPU = optimize_under(
                file_path, num_qpu, limit_qpu, epochs,
                anastz=None, anastz_mode=False, PG_mode=PG_mode,FT_mode=FT_mode,print_nodes=False,GL_start_point=GL_start_point,period=period,extra_space=extra_space,trans=trans )
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
            print(f"Done, saved in {output_file}", flush=True)

        
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

def iterative_progress(num_qubit,limit_qpu,num_qpu,period=50,epochs=1000,GL_start_point=100,PG_one_direct=False,FT_mode=True,Circuit_type="Rd",trans=False,extra_space=1):
    # decide the file path based on Circuit_type
    if Circuit_type=="Rd":
        file_path = f"C:/Users/Butch/Desktop/OneDrive - Stony Brook University/ICDCS_2025/random_circuits_new/{num_qubit}qubits_{num_qubit}layers.txt"
    elif Circuit_type=="QFT":
        file_path = f"C:/Users/Butch/Desktop/OneDrive - Stony Brook University/ICDCS_2025/qft_circuits/qft_circuit({num_qubit}qubits).txt"
    # decide whether to use FT or NFT mode
    if trans:
        trans_type="trans"
    else:
        trans_type="notrans"
    if FT_mode:
        output_dir = f"FT_perform_evals/Data_{trans_type}/{Circuit_type}/iterative_progress/{limit_qpu[0]}_cap"
    else:
        output_dir = f"NFT_perform_evals/Data_{trans_type}/{Circuit_type}/iterative_progress/{limit_qpu[0]}_cap"
    # create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    if PG_one_direct:
        output_file = f"{output_dir}/training_{limit_qpu[0]}_{num_qubit}_{period}period_{epochs}epochs_{GL_start_point}GL_start_point_PG_one_direct.csv"
    else:
        output_file = f"{output_dir}/training_{limit_qpu[0]}_{num_qubit}_{period}period_{epochs}epochs_{GL_start_point}GL_start_point.csv"
    # ensure the output file has a unique name
    output_file = get_unique_filename(output_file)
    
    PGGL_cost_list=optimize_under(
        file_path, num_qpu, limit_qpu, epochs=epochs,training_mode=True,PG_mode=False,FT_mode=FT_mode,period=period,GL_start_point=GL_start_point,PG_one_direct=PG_one_direct,extra_space=extra_space,trans=trans)
    PG_cost_list=optimize_under(
        file_path, num_qpu, limit_qpu, epochs=epochs,training_mode=True,PG_mode=True,FT_mode=FT_mode,period=period,GL_start_point=GL_start_point,PG_one_direct=PG_one_direct,extra_space=extra_space,trans=trans)
    
    row={
        'iteration': num_qubit,
        'PG_cost': PG_cost_list[-1],
        'PGGL_cost': PGGL_cost_list[-1]
    }
    print("length of PG_cost_list:", len(PG_cost_list))
    print("length of PGGL_cost_list:", len(PGGL_cost_list))
    df=pd.DataFrame({
        "iteration": list(range(len(PG_cost_list))),
        "PG_cost": PG_cost_list, 
        "PGGL_cost": PGGL_cost_list
    })
    df.to_csv(output_file, index=False)
    plt.plot(list(range(len(PG_cost_list))), PG_cost_list, label='PG Cost',color='violet')
    plt.plot(list(range(len(PGGL_cost_list))), PGGL_cost_list, label='PGGL Cost',color='green')
    plt.xlabel("Iteration")
    plt.ylabel("Cost")
    plt.title(f"Iterative Progress for {num_qubit} Qubits")
    plt.legend()
    plt.savefig(output_file.replace(".csv", ".png"))
    plt.show()
if __name__ == "__main__":

    experiment_qft_constant_limit(run_id=0,num_qpu=300,seed=432,circuit_size=list(range(30,101,10)),limit_qpu=[25]*300,Circuit_type="QFT",FT_mode=False,trans=False )

    # experiment_qft_constant_limit(
    #     run_id=5, num_qpu=300, limit_qpu=[25]*300, seed=4321, repeat_times=1, PG_one_direct=False
    # )

    # for limit_qpu in [5,15,25]:
    #     for i in range(30,101,10):
    #         random_mapping(circuit_type='QFT', num_qubit=i, limit_qpu=limit_qpu, num_qpu=300, seed=4321)


    # GL_start_point=100
    # num_qpu=300
    # num_qubit=100
    # limit_qpu=[25]*num_qpu
    # iterative_progress(num_qubit,limit_qpu,num_qpu,period=100,epochs=1000,GL_start_point=GL_start_point,PG_one_direct=False,FT_mode=False,Circuit_type="Rd",trans=True)


    # for n in tqdm(range(5,26,10)):
    #     mean=n
    #     std_dev = 0
    #     num_qpu=300
    #     qpu_limit=[int(round(random.gauss(mean,std_dev))) for _ in range(num_qpu)]
    #     sorted_qpu_limit=sorted(qpu_limit,reverse=True)
    #     print(sorted_qpu_limit)
    #     experiment_qft_constant_limit(num_qpu,sorted_qpu_limit,1)

    # iterative_progress(100,[25]*20,20,Circuit_type="QFT",FT_mode=False,trans=False,extra_space=1)
# for n in tqdm(range(5,26,10)):
#     mean=n
#     std_dev = 0
#     num_qpu=300
#     qpu_limit=[int(round(random.gauss(mean,std_dev))) for _ in range(num_qpu)]
#     sorted_qpu_limit=sorted(qpu_limit,reverse=True)
#     print(sorted_qpu_limit)
#     experiment_qft_constant_limit(num_qpu,sorted_qpu_limit,1)

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

# cost of random mappings
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
    #     for limit_qpu in range(156,157,1):
    #         circuit=Circuit(f"C:/Users/Butch/Desktop/OneDrive - Stony Brook University/ICDCS_2025/random_circuits_new/{circuit_size}qubits_{circuit_size}layers.txt")
    #         correcting_period=5
    #         layers=FT_circuit_func(circuit.layers,correcting_period)
    #         # print("Original_circuit layers shape",circuit.layers.T.shape)
    #         # print("FT_circuit layers shape",layers.T.shape)
    #         num_qubits=circuit.num_qubits*8
    #         nodes=random_mappings(num_qubits, limit_qpu, layers)
    #         print(f"cost of random mappings for {circuit_size} qubits and size {limit_qpu} qpus:", total_cost(nodes))


