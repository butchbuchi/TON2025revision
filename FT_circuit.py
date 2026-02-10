import numpy as np
from circuit_utils import Circuit

def g1(ft_layers,target_layer=[]):
    for i in range(int(ft_layers.shape[0]/8)):
        ft_layers[i*8+7,target_layer[2]]=i*8+0
        ft_layers[i*8+0,target_layer[2]]=i*8+7
        ft_layers[i*8+7,target_layer[3]]=i*8+4
        ft_layers[i*8+4,target_layer[3]]=i*8+7
        ft_layers[i*8+7,target_layer[4]]=i*8+5
        ft_layers[i*8+5,target_layer[4]]=i*8+7
        ft_layers[i*8+7,target_layer[5]]=i*8+6
        ft_layers[i*8+6,target_layer[5]]=i*8+7
def g2(ft_layers,target_layer=[]):
    for i in range(int(ft_layers.shape[0]/8)):
        ft_layers[i*8+7,target_layer[2]]=i*8+1
        ft_layers[i*8+1,target_layer[2]]=i*8+7
        ft_layers[i*8+7,target_layer[3]]=i*8+3
        ft_layers[i*8+3,target_layer[3]]=i*8+7
        ft_layers[i*8+7,target_layer[4]]=i*8+5
        ft_layers[i*8+5,target_layer[4]]=i*8+7
        ft_layers[i*8+7,target_layer[5]]=i*8+6
        ft_layers[i*8+6,target_layer[5]]=i*8+7
def g3(ft_layers,target_layer=[]):
    for i in range(int(ft_layers.shape[0]/8)):
        ft_layers[i*8+7,target_layer[2]]=i*8+2
        ft_layers[i*8+2,target_layer[2]]=i*8+7
        ft_layers[i*8+7,target_layer[3]]=i*8+3
        ft_layers[i*8+3,target_layer[3]]=i*8+7
        ft_layers[i*8+7,target_layer[4]]=i*8+4
        ft_layers[i*8+4,target_layer[4]]=i*8+7
        ft_layers[i*8+7,target_layer[5]]=i*8+5
        ft_layers[i*8+5,target_layer[5]]=i*8+7

def g4(ft_layers,target_layer=[]):
    for i in range(int(ft_layers.shape[0]/8)):
        ft_layers[i*8+7,target_layer[2]]=i*8+0
        ft_layers[i*8+0,target_layer[2]]=i*8+7
        ft_layers[i*8+7,target_layer[4]]=i*8+4
        ft_layers[i*8+4,target_layer[4]]=i*8+7
        ft_layers[i*8+7,target_layer[6]]=i*8+5
        ft_layers[i*8+5,target_layer[6]]=i*8+7
        ft_layers[i*8+7,target_layer[8]]=i*8+6
        ft_layers[i*8+6,target_layer[8]]=i*8+7
def g5(ft_layers,target_layer=[]):
    for i in range(int(ft_layers.shape[0]/8)):
        ft_layers[i*8+7,target_layer[2]]=i*8+1
        ft_layers[i*8+1,target_layer[2]]=i*8+7
        ft_layers[i*8+7,target_layer[4]]=i*8+3
        ft_layers[i*8+3,target_layer[4]]=i*8+7
        ft_layers[i*8+7,target_layer[6]]=i*8+5
        ft_layers[i*8+5,target_layer[6]]=i*8+7
        ft_layers[i*8+7,target_layer[8]]=i*8+6
        ft_layers[i*8+6,target_layer[8]]=i*8+7
def g6(ft_layers,target_layer=[]):
    for i in range(int(ft_layers.shape[0]/8)):
        ft_layers[i*8+7,target_layer[2]]=i*8+2
        ft_layers[i*8+2,target_layer[2]]=i*8+7
        ft_layers[i*8+7,target_layer[4]]=i*8+3
        ft_layers[i*8+3,target_layer[4]]=i*8+7
        ft_layers[i*8+7,target_layer[6]]=i*8+4
        ft_layers[i*8+4,target_layer[6]]=i*8+7
        ft_layers[i*8+7,target_layer[8]]=i*8+5
        ft_layers[i*8+5,target_layer[8]]=i*8+7

def syndrome_circuit(ft_layers, target_layer=[]):
    """
    Constructs the syndrome circuit for the FT circuit.
    
    Parameters:
    ft_layers (np.ndarray): The ft_layers of the original circuit.
    target_layer (list): The target layer indices for the syndrome circuit.
    
    Returns:
    np.ndarray: The modified ft_layers with syndrome operations applied.
    """
    g1(ft_layers, target_layer[0:8])
    g2(ft_layers, target_layer[8:16])
    g3(ft_layers, target_layer[16:24])
    g4(ft_layers, target_layer[24:35])
    g5(ft_layers, target_layer[35:46])
    g6(ft_layers, target_layer[46:57])
    return ft_layers

def initialize_ft_circuit(ft_layers):
    g1(ft_layers, list(range(0,8)))
    g2(ft_layers, list(range(8,16)))
    g3(ft_layers, list(range(16,24)))
    return ft_layers
def FT_circuit_func( layers,period):
    layers=layers.T
    origin_depth=layers.shape[-1]
    origin_width=layers.shape[0]
    # Calculate the depth and width of the FT circuit
    # The depth is calculated based on the period and the original depth
    # 25 is the depth for initalize the FT circuit
    ft_depth=int(25+np.ceil(origin_depth/period)*(3*8+3*11+1)+origin_depth)
    ft_width=int(origin_width*8)
    ft_layers=-1*np.ones((ft_width,ft_depth),dtype=int)
    # Initialize the FT circuit layers
    ft_layers = initialize_ft_circuit(ft_layers)
    interval = 25
    for i in range(origin_depth):
        for j in range(origin_width):
            for k in range(7):
                if layers[j,i] != -1:
                    # Map the original layer to the FT layer
                    ft_layers[8*j+k,i+interval]=layers[j,i]*8+k
        # Apply the syndrome circuit to the FT layers
        if (i+1) % period == 0:
            ft_layers = syndrome_circuit(ft_layers, list(range(i+interval+1, i+interval+1+58+1)))
            interval += 58
    if origin_depth % period != 0:
        ft_layers = syndrome_circuit(ft_layers, list(range(origin_depth+ interval, origin_depth+ interval+58+1)))
    return (ft_layers.T)


num_qubit=3
period=3


def main():
    file_path = f"C:/Users/Butch/Desktop/OneDrive - Stony Brook University/ICDCS_2025/qft_circuits/qft_circuit({num_qubit}qubits).txt"
    # The layout of the circuit in layers in the transposed circuit
    layers=Circuit(file_path).layers
    ft_layers=FT_circuit_func( layers, 5)
    print(layers)
    print(ft_layers)
    print("ft_shape",ft_layers.shape)
    print("origin_shape",layers.shape)
    np.savetxt("ft_layers_output.csv", ft_layers, fmt='%d', delimiter=",")
if __name__ == "__main__":
    main()