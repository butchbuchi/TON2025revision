import argparse
import multiprocessing
import PGGL
import random

def experiment_wrapper(args):
    return PGGL.experiment_qft_constant_limit(*args)

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description="Run PGGL experiment with custom parameters")
    parser.add_argument('--epochs',type=int, default=1000, help="Total running epochs")
    parser.add_argument('--circuit_type',type=str,default='QFT',choices=['QFT','Rd'],help='Type of quantum circuit')
    parser.add_argument('--FT_mode',action='store_true', help='Enable fault-tolerant mode')
    parser.add_argument('--PG_mode', action='store_true',help='Running with only PG')
    parser.add_argument('--trans',action='store_true',help='Enable layer-wise transition')
    parser.add_argument('--extra_space',type=int, default=1, help='Spare extra QPU space when initialization')
    parser.add_argument('--multi_process',action='store_true',help='Parallelly running programs.')
    args=parser.parse_args()
    for qpu_limit in range(25,24,-10):
    # for qpu_limit in range(156,157,1):
        mean=qpu_limit
        std_dev = 0
        num_qpu=300
        qpu_limit=[int(round(random.gauss(mean,std_dev))) for _ in range(num_qpu)]
        sorted_qpu_limit=sorted(qpu_limit,reverse=True)
        circuit_size=list(range(30,101,10))  # Circuit sizes from 30 to 100 with step 10
        # circuit_size=list(range(20,21,1))
        epochs=args.epochs
        FT_mode=args.FT_mode
        extra_space=args.extra_space
        circuit_type=args.circuit_type  
        multi_process=args.multi_process
        PG_mode=args.PG_mode
        trans=args.trans

        num_processes = multiprocessing.cpu_count() 
        if multi_process:
            num_runs = num_processes-2  # Reserve 2 processes for other tasks
        else: num_runs=1
        print(f"Number of processes: {num_runs}", flush=True)
        if num_runs>multiprocessing.cpu_count(): raise RuntimeError("No enough CPUs")
        args_list = []
        for run_id in range(num_runs):
            args_list.append((run_id,num_qpu,sorted_qpu_limit,random.randint(0,100000),circuit_size,epochs,False,1,False, circuit_type,PG_mode,FT_mode,50,100,extra_space,multi_process,trans))

        with multiprocessing.Pool(processes=num_processes) as pool:
            pool.map(experiment_wrapper, args_list)
    # if trans:trans_type="trans"
    # else: trans_type="notrans"

    # if FT_mode:print(f"All experiments completed. Files saved in FT_perform_evals/parallel_processing_Data_{trans_type}/{circuit_type}/PGGL/")
    # else:
    #     print(f"All experiments completed. Files saved in NFT_perform_evals/parallel_processing_Data_{trans_type}/{circuit_type}/PGGL/")