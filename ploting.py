import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoLocator
from mpl_toolkits.axes_grid1.inset_locator import inset_axes, mark_inset
from matplotlib.ticker import MultipleLocator
import matplotlib.patches as patches
import seaborn as sns
import os
import numpy as np
def parallel_processing_plotting():

    # === 参数 ===
    base_dir = r"C:/Users/Butch/OneDrive - Stony Brook University/TON/NFT_perform_evals/parallel_processing_Data_notrans/QFT/PGGL/5_cap"
    target_circuit_size = 100
    num_runs = 18

    # === 读取数据 ===
    values = []
    for run_id in range(num_runs):
        file_path = os.path.join(base_dir, f"{run_id}.csv")
        df = pd.read_csv(file_path)
        val = df[df["circuit_size"] == target_circuit_size]["y_local_reg"].values[0]
        values.append(val)

    # === 统计信息 ===
    mean_val = np.mean(values)
    min_val = np.min(values)
    max_val = np.max(values)

    # === 绘图 ===
    plt.figure(figsize=(12,5))
    sns.set_theme(style="whitegrid")

    # 横向 stripplot
    sns.stripplot(x=[min_val], orient="h", jitter=0.3, size=20,
                color="#8ECFC9", edgecolor="white", linewidth=0.5)
    sns.stripplot(x=[max_val], orient="h", jitter=10000000, size=20,
                color="#FFBE7A", edgecolor="white", linewidth=0.5)
    sns.stripplot(x=[value for value in values if value != min_val and value != max_val], orient="h", jitter=0.3, size=20,
                color="#FA7F6F", edgecolor="white", linewidth=0.5)

    # 隐藏 y 轴
    plt.yticks([])

    # 设置标题和标签
    # plt.title("PGGL Cost Distribution for Circuit Size = 100", fontsize=13, weight='bold')
    plt.xlabel("#Entanglement", fontsize=28)


    # === 设置横轴刻度：1700, 1705, 1710, ..., 1754, 1760 ===
    xticks = [1700,1705]+list(range(1710, 1755, 20)) + [1754, 1760]
    xticks = sorted(set(xticks))  # 去重 + 排序
    plt.xticks(ticks=xticks, fontsize=27)

    plt.tight_layout()
    plt.show()

def comprehensive_comparison_plotting(circuit_type="Rd",qpu_limit=5):
    import pandas as pd
    import matplotlib.pyplot as plt

    # 文件路径和 QPU 限制
    filepath_ours = f"C:/Users/Butch/OneDrive - Stony Brook University/TON/NFT_perform_evals/parallel_processing_Data_trans/{circuit_type}/PGGL/{qpu_limit}_cap/1_extra_space/min.csv"
    if circuit_type == "QFT":
        filepath_SA = f"C:/Users/Butch/OneDrive - Stony Brook University/ICDCS_2025/Camare_ready/Comprehensive_perform_evals/Data/QFT/Telegate/QFT_{qpu_limit}_limitQPU_min.csv"
        filepath_stitch =f"C:/Users/Butch/OneDrive - Stony Brook University/ICDCS_2025/baseline_code/stitch_final_plots/stitch_{qpu_limit}QPU_limit.csv"
        filepath_gatecover=rf"C:\Users\Butch\Desktop\TON2025revision\gate_cover_evals\qft\{qpu_limit}_cap\results.csv"
    if circuit_type == "Rd":
        filepath_SA = f"C:/Users/Butch/OneDrive - Stony Brook University/ICDCS_2025/Camare_ready/Comprehensive_perform_evals/Data/{circuit_type}/Telegate/Rd({qpu_limit})_Telegate.csv"
        filepath_stitch =f"C:/Users/Butch/OneDrive - Stony Brook University/ICDCS_2025/Camare_ready/Comprehensive_perform_evals/Data/Rd/ZS/Rd({qpu_limit})_ZS.csv"
        filepath_gatecover=rf"C:\Users\Butch\Desktop\TON2025revision\gate_cover_evals\random\{qpu_limit}_cap\results.csv"
    # 数据加载./
    x = list(range(30, 101, 10))
    stitch_cost = pd.read_csv(filepath_stitch)['stitch']
    gatecover_cost=pd.read_csv(filepath_gatecover)['total_epr']
    ours_cost = pd.read_csv(filepath_ours)['y_local_reg']
    if circuit_type == "QFT":
        SA_cost = pd.read_csv(filepath_SA)['y_local_reg']
    else:
        SA_cost = pd.read_csv(filepath_SA)['cost']

    # 设置柱状图的宽度
    bar_width = 2.5

    # 绘制柱状图
    plt.figure(figsize=(10, 6))

    # 绘制柱子
    # PG-GL（left）
    ours_x = [i - 1.1*bar_width for i in x]
    plt.bar(ours_x, ours_cost, width=bar_width, label="CPG-BP", color='#FF1F5B',hatch='/',edgecolor='white')
    # plt.vlines(ours_x, ours_min, ours_max, colors='black', linewidth=1.5)

    # Teledata-ZS（mid）
    stitch_x = x
    plt.bar(stitch_x, stitch_cost, width=bar_width, label="Teledata-ZS", color='#FFC61E', alpha=1,hatch='.',edgecolor='white')
    # plt.vlines(stitch_x, stitch_min, stitch_max, colors='black', linewidth=1.5)

    #gatecover
    gatecover_x = [i + 2.2*bar_width for i in x]
    plt.bar(gatecover_x, gatecover_cost, width=bar_width, label="GateCover", color='#8ECFC9', alpha=1,hatch='x',edgecolor='white')
    
    # Telegate-SA（right）
    sa_x = [i + 1.1*bar_width for i in x]
    plt.bar(sa_x, SA_cost, width=bar_width, label="Telegate-SA", color='#009ADE', alpha=1,hatch='\\',edgecolor='white')
    # plt.vlines(sa_x, SA_min, SA_max, colors='black', linewidth=1.5)  # 浮动线

    
    # 坐标轴标签和图例E
    plt.xlabel('Circuit Width', fontsize=28)
    plt.ylabel('#Entanglement', fontsize=28)
    plt.legend(loc='upper left',bbox_to_anchor=(0, 1.01), borderaxespad=0,fontsize=24, framealpha=0, edgecolor='none', labelspacing=0.25)

    # # 设置y轴为对数刻度
    # plt.yscale('log')

    # 刻度和网格
    plt.xticks(x, fontsize=27)  # 设置X轴刻度
    plt.yticks(fontsize=27)     # 设置Y轴刻度
    plt.grid(alpha=0.6, linestyle=':', linewidth=0.75)

    # 显示图形
    plt.tight_layout()
    plt.show()
    # 保存图形
    # output_dir = f"C:/Users/Butch/OneDrive - Stony Brook University/TON/paper_fig/comprehensive_comparison/{circuit_type}"
    # os.makedirs(output_dir, exist_ok=True)
    # output_file = f"{output_dir}/{circuit_type}_{qpu_limit}_limitQPU_comparison.svg"    
    # plt.savefig(output_file, dpi=300, bbox_inches='tight')
    # print(f"Figure saved to {output_file}")

def comparative_ratio_plot(circuit_type="Rd", trans="trans",qpu_limit=5,Performance_Gain_mode=True):
    import pandas as pd
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MultipleLocator, FormatStrFormatter


    # 文件路径
    filepath_ours = f"C:/Users/Butch/OneDrive - Stony Brook University/TON/NFT_perform_evals/parallel_processing_Data_{trans}/{circuit_type}/PGGL/{qpu_limit}_cap/1_extra_space/min.csv"
    
    if circuit_type == "QFT":
        filepath_random=f"C:/Users/Butch/OneDrive - Stony Brook University/TON/NFT_perform_evals/Data_random/QFT/{qpu_limit}_cap.csv"
        filepath_SA = f"C:/Users/Butch/OneDrive - Stony Brook University/ICDCS_2025/Camare_ready/Comprehensive_perform_evals/Data/QFT/Telegate/QFT_{qpu_limit}_limitQPU_min.csv"
        filepath_stitch = f"C:/Users/Butch/OneDrive - Stony Brook University/ICDCS_2025/baseline_code/stitch_final_plots/stitch_{qpu_limit}QPU_limit.csv"
        filepath_gatecover=rf"C:\Users\Butch\Desktop\TON2025revision\gate_cover_evals\qft\{qpu_limit}_cap\results.csv"
        filepath_CGplusLABUBU=rf"C:\Users\Butch\Desktop\TON2025revision\NFT_perform_evals\Data\qft\PGGL\{qpu_limit}_cap\4.csv"
    else:
        filepath_random=f"C:/Users/Butch/OneDrive - Stony Brook University/TON/NFT_perform_evals/Data_random/Rd/{qpu_limit}_cap.csv"
        filepath_SA = f"C:/Users/Butch/OneDrive - Stony Brook University/ICDCS_2025/Camare_ready/Comprehensive_perform_evals/Data/{circuit_type}/Telegate/Rd({qpu_limit})_Telegate.csv"
        filepath_stitch = f"C:/Users/Butch/OneDrive - Stony Brook University/ICDCS_2025/Camare_ready/Comprehensive_perform_evals/Data/Rd/ZS/Rd({qpu_limit})_ZS.csv"
        filepath_gatecover=rf"C:\Users\Butch\Desktop\TON2025revision\gate_cover_evals\random\{qpu_limit}_cap\results.csv"
        filepath_CGplusLABUBU=rf"C:\Users\Butch\Desktop\TON2025revision\NFT_perform_evals\Data\Rd\PGGL\{qpu_limit}_cap\4.csv"

    # 加载数据
    x = list(range(30, 101, 10))  # circuit width
    ours_cost = pd.read_csv(filepath_ours)['y_local_reg']
    random_cost = pd.read_csv(filepath_random)['y_local_reg'] 
    stitch_cost = pd.read_csv(filepath_stitch)['stitch']
    gatecover_cost=pd.read_csv(filepath_gatecover)['total_epr']
    SA_cost = pd.read_csv(filepath_SA)['y_local_reg'] if circuit_type == "QFT" else pd.read_csv(filepath_SA)['cost']
    CGplusLABUBU_cost = pd.read_csv(filepath_CGplusLABUBU)['y_local_reg'] 

    if Performance_Gain_mode:
        # 计算相对比值
        eps = 1e-8
        # ours_ratio = [o / (r if r > eps else eps) for o, r in zip(ours_cost, random_cost)]
        zs_ratio = [(z-o )*100/ z for z, o in zip( stitch_cost,ours_cost)]
        sa_ratio = [(s-o)*100 / s for s, o in zip(SA_cost,ours_cost)]
        random_ratio = [(r-o)*100 / r for r, o in zip(random_cost,ours_cost)]
        gatecover_ratio = [(g-o)*100 / g for g, o in zip(gatecover_cost,ours_cost)]
        CGplusLABUBU_cost_ratio = [(c-o)*100 / c for c, o in zip(CGplusLABUBU_cost,ours_cost)]
            # 主图：折线图（比值）
        fig, ax1 = plt.subplots(figsize=(10, 6))

        ax1.plot(x, sa_ratio, marker='o', label='vs Telegate-SA', linewidth=3, markersize=10, color='#009ADE',zorder=10)
        ax1.plot(x, random_ratio, marker='^', label='vs Telegate-RD', linewidth=3, markersize=10, color='#FF1F5B',zorder=10)
        ax1.plot(x, zs_ratio, marker='s', label='vs Teledata-ZS', linewidth=3, markersize=10, color='#FFC61E',zorder=10)
        ax1.plot(x, gatecover_ratio, marker='x', label='vs GC', linewidth=3, markersize=10, color='#8ECFC9',zorder=10)
        ax1.plot(x, CGplusLABUBU_cost_ratio, marker='d', label='vs GC+LABUBU', linewidth=3, markersize=10, color='#BE88DC',zorder=10)
        


        ax1.set_xlabel("Circuit Width", fontsize=28)
        # ax1.set_ylabel(r"Performance Gain (\%)""\n"
        #                r"$\frac{\mathrm{Bchmk} - \mathrm{Labubu}}{\mathrm{Bchmk}}$", fontsize=28)
        ax1.set_ylabel("Relative Improvement(%)", fontsize=28)
        ax1.tick_params(axis='y', labelsize=27)
        ax1.set_xticks(x)
        ax1.set_xticklabels(x, fontsize=27)
        ax1.grid(alpha=0.6, linestyle=':', linewidth=0.75)
        ax1.set_ylim(-20,80)

        # 第二 y 轴：柱状图（ours_cost）
        ax2 = ax1.twinx()
        bar_width = 4
        offset_x = [xi - 0.7*bar_width for xi in x]  # 与折线错开一点
        ax2.bar(offset_x, ours_cost, width=bar_width,color='#B3876A', alpha=0.4, label='Labubu', edgecolor='black',  zorder=0)
        ax2.set_ylabel("#Entanglement", fontsize=24)
        ax2.tick_params(axis='y', labelsize=22)
        

        ax2.set_ylim(0, max(ours_cost) * 1.1)
        ax2.yaxis.set_major_locator(AutoLocator())    # if circuit_type == "Rd":

 
        # 合并图例
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        lg1=ax1.legend(lines1[0:3] , labels1[0:3] ,
                loc='upper left',bbox_to_anchor=(-0.03, 1.05),
                ncol=1, fontsize=22, framealpha=0, edgecolor='none',labelspacing=0.1)
        leg2=ax1.legend(lines1[3:5] , labels1[3:5] ,
                loc='upper left',bbox_to_anchor=(-0.02, 0.72),
                ncol=1, fontsize=22, framealpha=0, edgecolor='none',labelspacing=0.1)
        ax1.add_artist(lg1)
        ax2.legend(lines2 , labels2 ,
                loc='upper left',bbox_to_anchor=(0.55, 1.03),
                ncol=1, fontsize=22, framealpha=0, edgecolor='none',labelspacing=0.5)
        

    else:
        # 计算相对比值
        eps = 1e-8
        # ours_ratio = [o / (r if r > eps else eps) for o, r in zip(ours_cost, random_cost)]
        zs_ratio = [z / (o if o > eps else eps) for z, o in zip( stitch_cost,ours_cost)]
        sa_ratio = [s / (o if o > eps else eps) for s, o in zip(SA_cost,ours_cost)]
        random_ratio = [r / (o if o > eps else eps) for r, o in zip(random_cost,ours_cost)]

            # 主图：折线图（比值）
        fig, ax1 = plt.subplots(figsize=(10, 6))

        ax1.plot(x, sa_ratio, marker='o', label='Telegate-SA / CPG-BP', linewidth=3, markersize=10, color='#009ADE',zorder=10)
        ax1.plot(x, random_ratio, marker='^', label='Telegate-RD / CPG-BP', linewidth=3, markersize=10, color='#FF1F5B',zorder=10)
        ax1.plot(x, zs_ratio, marker='s', label='Teledata-ZS / CPG-BP', linewidth=3, markersize=10, color='#FFC61E',zorder=10)

        ax1.axhline(y=1.0, linestyle='--', color='gray', linewidth=1.5)
        ax1.text(x[0], 1.05, "CPG-BP Baseline", fontsize=16, color='gray')

        ax1.set_xlabel("Circuit Width", fontsize=28)
        ax1.set_ylabel("Relative Overhead", fontsize=28)
        ax1.tick_params(axis='y', labelsize=27)
        ax1.set_xticks(x)
        ax1.set_xticklabels(x, fontsize=27)
        ax1.grid(alpha=0.6, linestyle=':', linewidth=0.75)
        

        # 第二 y 轴：柱状图（ours_cost）
        ax2 = ax1.twinx()
        bar_width = 4
        offset_x = [xi - 0.7*bar_width for xi in x]  # 与折线错开一点
        ax2.bar(offset_x, ours_cost, width=bar_width,color='#B3876A', alpha=0.4, label='CPG-BP (Absolute)', edgecolor='black',  zorder=0)
        ax2.set_ylabel("#Entanglement (CPG-BP)", fontsize=24)
        ax2.tick_params(axis='y', labelsize=22)
        
        ax2.set_ylim(0, max(ours_cost) * 1.1)
        ax2.yaxis.set_major_locator(MultipleLocator(2000))    # if circuit_type == "Rd":

        if circuit_type == "Rd":  
            # 合并图例
            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax1.legend(lines1 + lines2, labels1 + labels2,
                    loc='upper left',bbox_to_anchor=(0, 1),
                    ncol=1, fontsize=22, framealpha=0, edgecolor='none',labelspacing=0.2)
        else:
            ax1.legend(loc='upper left', bbox_to_anchor=(0.195, 0.98), fontsize=22,framealpha=0, edgecolor='none',labelspacing=0.2)
            ax2.legend(loc='upper left', bbox_to_anchor=(-0.03, 0.55), fontsize=22,framealpha=0, edgecolor='none',labelspacing=0.2)

    plt.tight_layout()
    save_path = f"paper_fig/comprehensive_comparison/ratio_plot/{circuit_type}/comparison_ratio_{circuit_type}_{qpu_limit}.svg"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"Saved to: {save_path}")
    plt.show()





    # # 绘图
    # plt.figure(figsize=(10, 6))
    # plt.plot(x, sa_ratio, marker='o', label='CPG-BP/Telegate-SA', linewidth=3, markersize=10, color='#009ADE')
    # plt.plot(x, random_ratio, marker='^', label='CPG-BP/Telegate-RD', linewidth=3, markersize=10, color='#FF1F5B')
    # plt.plot(x, zs_ratio, marker='s', label='CPG-BP/Teledata-ZS', linewidth=3, markersize=10, color='#FFC61E')


    # # 坐标轴和图例
    # plt.xlabel("Circuit Width", fontsize=28)
    # plt.ylabel("Relative Overhead", fontsize=28)
    # plt.xticks(x, fontsize=27)
    # plt.yticks(fontsize=27)
    # plt.grid(alpha=0.6, linestyle=':', linewidth=0.75)
    # # plt.legend(loc='upper left',bbox_to_anchor=(0.4, 0.48), borderaxespad=0,fontsize=24, framealpha=0, edgecolor='none', labelspacing=0.25)
    # plt.legend(loc='best', fontsize=24, framealpha=0, edgecolor='none')

    # # 横线参考线
    # plt.axhline(y=1.0, linestyle='--', color='gray', linewidth=1.5)
    # plt.text(x[0], 1.05, "CPG-BP Baseline", fontsize=16, color='gray')

    # # plt.ylim(0, 0.2)

    # plt.tight_layout()
    # # plt.show()

    # # 可选保存
    # plt.savefig(f"C:/Users/Butch/OneDrive - Stony Brook University/TON/paper_fig/comprehensive_comparison/ratio_plot/{circuit_type}/comparison_ratio_{circuit_type}_{qpu_limit}.svg", dpi=300, bbox_inches='tight')


# Bar chart: CPG-BP with/without extra-space initialization
def extra_space_initialization_plot():
    import matplotlib.pyplot as plt
    import numpy as np

    num_qubit=25
    circuit_type="QFT"
    zero_extra_filepath=f"C:/Users/Butch/OneDrive - Stony Brook University/TON/NFT_perform_evals/parallel_processing_Data_trans/{circuit_type}/PGGL/{num_qubit}_cap/0_extra_space/min.csv"
    one_extra_filepath=f"C:/Users/Butch/OneDrive - Stony Brook University/TON/NFT_perform_evals/parallel_processing_Data_trans/{circuit_type}/PGGL/{num_qubit}_cap/1_extra_space/min.csv"
    two_extra_filepath=f"C:/Users/Butch/OneDrive - Stony Brook University/TON/NFT_perform_evals/parallel_processing_Data_trans/{circuit_type}/PGGL/{num_qubit}_cap/2_extra_space/min.csv"
    # 数据
    circuit_size = [30, 40, 50, 60, 70, 80, 90, 100]

    cpg_bp_one_extra_space = pd.read_csv(one_extra_filepath)['y_local_reg']
    cpg_bp_no_extra_space = pd.read_csv(zero_extra_filepath)['y_local_reg']
    cpg_bp_two_extra_space = pd.read_csv(two_extra_filepath)['y_local_reg']
    x = np.arange(len(circuit_size))  # label positions
    width = 0.25

    fig, ax1 = plt.subplots(figsize=(10, 7)) 

    # 绘制柱状图
    offset = width + 0.03
    bars1 = ax1.bar(x -offset, cpg_bp_no_extra_space, width, label='0-idle qubit initialization', color='#FF1F5B', hatch='/', edgecolor='white')
    bars2 = ax1.bar(x , cpg_bp_one_extra_space, width, label='1-idle qubit initialization', color='#FFC61E', hatch='.', edgecolor='white')
   
    bar3s3 = ax1.bar(x + offset, cpg_bp_two_extra_space, width, label='2-idle qubit initialization', color='#009ADE', hatch='\\', edgecolor='white')

    # 设置标签与样式
    ax1.set_ylabel('#Entanglement', fontsize=26)
    ax1.set_xlabel('Circuit Width', fontsize=26)
    ax1.set_xticks(x)
    ax1.set_xticklabels(circuit_size, fontsize=25)
    ax1.tick_params(axis='y', labelsize=25)
    ax1.grid(alpha=1, linestyle=':', linewidth=0.75)
    plt.legend(fontsize=22, framealpha=0, edgecolor='none')

    # plt.tight_layout()
    plt.show()


def tele_ratio():
        # Telegate/Teledata ratio
    qpu_limit=5
    filepath=f"C:/Users/Butch/OneDrive - Stony Brook University/TON/NFT_perform_evals/parallel_processing_Data_trans/Rd/PGGL/5_cap/1_extra_space/min.csv"
    x=list(range(30,101,10))
    telegate_cost=pd.read_csv(filepath)['telegate_cost']
    teledata_cost=pd.read_csv(filepath)['y_local_reg']

    ratio=[]
    for i in range(0,8):
        ratio.append(telegate_cost[i]/teledata_cost[i])
    plt.figure(figsize=(10, 7))  # 或其他你想要的尺寸

    plt.plot(x,ratio,marker='.',markersize=18,label=f"RD, L={qpu_limit}",linestyle='-',color='#AF58BA',alpha=1,linewidth=3)


    qpu_limit=15
    filepath=f"C:/Users/Butch/OneDrive - Stony Brook University/TON/NFT_perform_evals/parallel_processing_Data_trans/Rd/PGGL/15_cap/1_extra_space/min.csv"
    x=list(range(30,101,10))
    telegate_cost=pd.read_csv(filepath)['telegate_cost']
    teledata_cost=pd.read_csv(filepath)['y_local_reg']

    ratio=[]
    for i in range(0,8):
        ratio.append(telegate_cost[i]/teledata_cost[i])

    plt.plot(x,ratio,marker='o',markersize=18,label=f"RD, L={qpu_limit}",linestyle='-',color='#FFC61E',alpha=1,linewidth=3)


    qpu_limit=25
    filepath=f"C:/Users/Butch/OneDrive - Stony Brook University/TON/NFT_perform_evals/parallel_processing_Data_trans/Rd/PGGL/25_cap/1_extra_space/min.csv"
    x=list(range(30,101,10))
    telegate_cost=pd.read_csv(filepath)['telegate_cost']
    teledata_cost=pd.read_csv(filepath)['y_local_reg']

    ratio=[]
    for i in range(0,8):
        ratio.append(telegate_cost[i]/teledata_cost[i])

    plt.plot(x,ratio,marker='*',markersize=18,label=f"RD, L={qpu_limit}",linestyle='-',color='#F28522',alpha=1,linewidth=3)


    qpu_limit=5
    filepath=f"C:/Users/Butch/OneDrive - Stony Brook University/TON/NFT_perform_evals/parallel_processing_Data_trans/QFT/PGGL/5_cap/1_extra_space/min.csv"
    x=list(range(30,101,10))
    telegate_cost=pd.read_csv(filepath)['telegate_cost']
    teledata_cost=pd.read_csv(filepath)['y_local_reg']

    ratio=[]
    for i in range(0,8):
        ratio.append(telegate_cost[i]/teledata_cost[i])

    plt.plot(x,ratio,marker='s',markersize=14,label=f"QFT, L={qpu_limit}",linestyle='-',color='#FF1F5B',alpha=1,linewidth=3)

    qpu_limit=15
    filepath="C:/Users/Butch/OneDrive - Stony Brook University/TON/NFT_perform_evals/parallel_processing_Data_trans/QFT/PGGL/15_cap/1_extra_space/min.csv"
    x=list(range(30,101,10))
    telegate_cost=pd.read_csv(filepath)['telegate_cost']
    teledata_cost=pd.read_csv(filepath)['y_local_reg']

    ratio=[]
    for i in range(0,8):
        ratio.append(telegate_cost[i]/teledata_cost[i])

    plt.plot(x,ratio,marker='+',markersize=26,label=f"QFT, L={qpu_limit}",linestyle='-',color='#00CD6C',alpha=1,linewidth=3)

    qpu_limit=25
    filepath=f"C:/Users/Butch/OneDrive - Stony Brook University/TON/NFT_perform_evals/parallel_processing_Data_trans/QFT/PGGL/25_cap/1_extra_space/min.csv"
    x=list(range(30,101,10))
    telegate_cost=pd.read_csv(filepath)['telegate_cost']
    teledata_cost=pd.read_csv(filepath)['y_local_reg']

    ratio=[]
    for i in range(0,8):
        ratio.append(telegate_cost[i]/teledata_cost[i])

    plt.plot(x,ratio,marker='x',markersize=26,label=f"QFT, L={qpu_limit}",linestyle='-',color='#009ADE',alpha=1,linewidth=3)

    plt.tick_params(axis='x', labelsize=25)  
    plt.tick_params(axis='y', labelsize=25)  

    plt.xlabel('Circuit Width', fontsize=26)
    plt.ylabel('Tele-ratio', fontsize=26)
    plt.legend(loc='lower right', bbox_to_anchor=(0.95, 0.07), fontsize=22, framealpha=0, edgecolor='none')
    plt.grid(alpha=1,linestyle=':',linewidth=0.75)
    plt.show()

def iterative_progress():
    from matplotlib.ticker import FuncFormatter
        # training progress
    # file_path_with="experiment_plots/Controlled Experiment/qft/nash_localgate_regularization_v2/training_progress/with_trick_qft_circuit_100qubits.csv"
    # file_path_without="experiment_plots/Controlled Experiment/qft/nash_localgate_regularization_v2/training_progress/without_trick_qft_circuit_100qubits.csv"
    file_path="C:/Users/Butch/OneDrive - Stony Brook University/TON/FT_perform_evals/Data_trans/Rd/iterative_progress/156_cap/training_156_60_200period_1000epochs_100GL_start_point.csv"
    # file_path="C:/Users/Butch/OneDrive - Stony Brook University/TON/NFT_perform_evals/Data_trans/QFT/iterative_progress/25_cap/training_25_100_50period_1000epochs_100GL_start_point_notrans.csv"
    # 数据读取
    x = pd.read_csv(file_path)['iteration']
    y_with = pd.read_csv(file_path)['PGGL_cost']
    y_without = pd.read_csv(file_path)['PG_cost']

    # 创建主图
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(x, y_with, label=f"Labubu", linestyle='-', color='#00CD6C', alpha=1,linewidth=2)
    ax.plot(x, y_without, label=f"Labu-CPG", linestyle='-', color='#AF58BA', alpha=1,linewidth=2)
    ax.set_xlim(0, 999)
    ax.set_ylim(16900,20000)
    ax.tick_params(axis='x', labelsize=27)  # 设置 x 轴刻度标签字体大小
    ax.tick_params(axis='y', labelsize=27)  # 设置 y 轴刻度标签字体大小
    ax.set_xlabel("Iteration",fontsize=28)
    ax.set_ylabel("#Entanglement",fontsize=28)
    ax.grid(alpha=0.5, linestyle=':', linewidth=0.75)
    # 添加主刻度和次刻度
    # ax.xaxis.set_major_locator(MultipleLocator(100))  # 主刻度间隔 100
    # ax.xaxis.set_minor_locator(MultipleLocator(20))   # 次刻度间隔 20
    # ax.yaxis.set_major_locator(MultipleLocator(20))   # 主刻度间隔 50
    # ax.yaxis.set_minor_locator(MultipleLocator(10))   # 次刻度间隔 10
    ax.xaxis.set_major_locator(MultipleLocator(100))  # 主刻度间隔 100
    ax.xaxis.set_minor_locator(MultipleLocator(20))   # 次刻度间隔 20
    ax.yaxis.set_major_locator(MultipleLocator(500))   # 主刻度间隔 50
    ax.yaxis.set_minor_locator(MultipleLocator(100))   # 次刻度间隔 10

    # 添加主次网格
    ax.grid(which='major', alpha=0.7, linestyle='-', linewidth=0.75)  # 主刻度网格
    ax.grid(which='minor', alpha=0.3, linestyle=':', linewidth=0.5)  # 次

    # x_start=240
    # delta_x=30
    # y_start=432
    # delta_y=6
    # # 在主图中添加矩形框以标注放大区域
    # rect = patches.Rectangle((x_start,y_start), delta_x, delta_y, linewidth=1.5, edgecolor='#FFC61E', facecolor='none', linestyle='--')
    # ax.add_patch(rect)

    # # 插入放大图
    # ax_inset = inset_axes(ax, width="45%", height="45%", loc='upper right')  # 放大子图
    # ax_inset.plot(x, y_with, linestyle='-', color='#00CD6C', alpha=1,linewidth=2)
    # ax_inset.plot(x, y_without, linestyle='-', color='#AF58BA', alpha=1,linewidth=2)

    # # 设置放大图范围
    # ax_inset.set_xlim(x_start,x_start+delta_x)  # 放大横轴区间
    # ax_inset.set_ylim(y_start,y_start+delta_y)  # 放大纵轴区间
    # ax_inset.tick_params(axis='x', labelsize=18)  # 设置 x 轴刻度标签字体大小
    # ax_inset.tick_params(axis='y', labelsize=18)  # 设置 y 轴刻度标签字体大小
    # ax_inset.grid(alpha=0.5, linestyle=':', linewidth=0.75)
    # # 设置次刻度间隔
    # ax_inset.xaxis.set_minor_locator(MultipleLocator(5))  # 横轴次刻度每隔 5
    # ax_inset.yaxis.set_minor_locator(MultipleLocator(1))  # 纵轴次刻度每隔 1
    
    # # 显示次刻度网格
    # ax_inset.grid(which='minor', alpha=0.3, linestyle=':', linewidth=0.5)  # 次刻度网格样式
    # ax_inset.grid(which='major', alpha=0.5, linestyle='-', linewidth=0.75) 

    # # 添加标记线连接主图和放大图
    # mark_inset(ax, ax_inset, loc1=2, loc2=4, color='#FFC61E', linestyle='--', linewidth=1.5)

    # 显示图像
    plt.tight_layout()
    ax.legend(fontsize=21, loc='lower left', bbox_to_anchor=(0.25,0.75),framealpha=0.5)
    # ax.legend(fontsize=22, loc='lower left', bbox_to_anchor=(-0.012, -0.022),framealpha=0.5)
    plt.show()

def running_time():
        #plot for time evaluation
    qpu_limit=25
    filepath_stitch=f"C:/Users/Butch/OneDrive - Stony Brook University/ICDCS_2025/baseline_code/stitch_final_plots/stitch_{qpu_limit}QPU_limit.csv"
    filepath_ours=f"C:/Users/Butch/OneDrive - Stony Brook University/ICDCS_2025/experiment_plots/Controlled Experiment/qft/nash_localgate_regularization_v2_average_final_plots/qft_{qpu_limit}_limitQPU.csv"
    x=list(range(30,101,10))
    stitch_cost=pd.read_csv(filepath_stitch)['time']
    ours_cost=pd.read_csv(filepath_ours)['time']
    plt.figure(figsize=(10, 7)) 
    plt.plot(x,stitch_cost,marker='.',markersize=18,label=f"Teledata-ZS, L={qpu_limit}",linestyle='-',color='#009ADE',alpha=0.85,linewidth=3)
    plt.plot(x,ours_cost,marker='^',markersize=18,label=f"Labubu, L={qpu_limit}",linestyle='-',color='#FF1F5B',alpha=0.85,linewidth=3)

    plt.tick_params(axis='x', labelsize=25)  
    plt.tick_params(axis='y', labelsize=25)  

    plt.xlabel('Circuit Width', fontsize=26)
    plt.ylabel('Time(s)', fontsize=26)
    plt.legend(fontsize=22, framealpha=0, edgecolor='none')
    plt.grid(alpha=1,linestyle=':',linewidth=0.75)
    # plt.tight_layout()
    # plt.subplots_adjust(left=0.15)  
    plt.show()



import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

def trans_comparison(qpu_limit=25):
    # 文件路径
    base = "C:/Users/Butch/OneDrive - Stony Brook University/TON/NFT_perform_evals"
    fp_trans_min  = f"{base}/parallel_processing_Data_trans/QFT/PGGL/{qpu_limit}_cap/1_extra_space/min.csv"
    fp_trans_max  = f"{base}/parallel_processing_Data_trans/QFT/PGGL/{qpu_limit}_cap/1_extra_space/max.csv"
    fp_not_min    = f"{base}/parallel_processing_Data_notrans/QFT/PGGL/{qpu_limit}_cap/1_extra_space/min.csv"
    fp_not_max    = f"{base}/parallel_processing_Data_notrans/QFT/PGGL/{qpu_limit}_cap/1_extra_space/max.csv"

    # 读取并按尺寸排序，避免顺序混乱
    df_tmin = pd.read_csv(fp_trans_min).sort_values("circuit_size")
    df_tmax = pd.read_csv(fp_trans_max).sort_values("circuit_size")
    df_nmin = pd.read_csv(fp_not_min).sort_values("circuit_size")
    df_nmax = pd.read_csv(fp_not_max).sort_values("circuit_size")

    x = df_tmin["circuit_size"].to_numpy()
    t_min = df_tmin["y_local_reg"].to_numpy()
    t_max = df_tmax["y_local_reg"].to_numpy()
    n_min = df_nmin["y_local_reg"].to_numpy()
    n_max = df_nmax["y_local_reg"].to_numpy()

    # 仅向上误差：上误差=max-min，下误差=0
    t_up = np.clip(t_max - t_min, 0, None)
    n_up = np.clip(n_max - n_min, 0, None)
    t_yerr = np.vstack([np.zeros_like(t_up), t_up])  # [下误差, 上误差]
    n_yerr = np.vstack([np.zeros_like(n_up), n_up])

    # 画图
    fig, ax = plt.subplots(figsize=(10,6))
    width = 0.36
    idx = np.arange(len(x))

    # 柱：最小值
    ax.bar(idx - width/2, t_min, width=width,color="#FFBE7A", edgecolor="black", label="Labu update")
    ax.bar(idx + width/2, n_min, width=width, color="#82B0D2",edgecolor="black", label="Cowi update")

    # 误差线：只从柱顶往上到 max
    ax.errorbar(idx - width/2, t_min, yerr=t_yerr, fmt="none", ecolor="black", elinewidth=1.8, capsize=7)
    ax.errorbar(idx + width/2, n_min, yerr=n_yerr, fmt="none", ecolor="black", elinewidth=1.8, capsize=7)

    # 轴与样式
    ax.set_xlabel("Circuit Width", fontsize=28)
    ax.set_ylabel("#Entanglement", fontsize=28)
    # ax.set_title(f"Min (bars) with Max (upper error)  —  QPU limit = {qpu_limit}", fontsize=13)
    ax.set_xticks(idx)
    ax.set_xticklabels(x)
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    # 获取已有的 legend 元素
    handles, labels = ax.get_legend_handles_labels()
    # 加入我们自定义的误差线说明
    err_handle = Line2D([0],[0], color="black", linewidth=1.2, marker=None)
    handles.append(err_handle)
    labels.append("Upper error = max - min")
    ax.grid(alpha=1, linestyle=':', linewidth=0.75)
    # 明确传 handles 和 labels
    ax.legend(handles, labels, loc="best",fontsize=22, framealpha=0, edgecolor='none')
    ax.tick_params(axis='x', labelsize=27)  
    ax.tick_params(axis='y', labelsize=27)  
    plt.tight_layout()
    plt.show()




if __name__ == "__main__":
    # parallel_processing_plotting()
    # comprehensive_comparison_plotting(circuit_type="Rd",qpu_limit=5)
    # comprehensive_comparison_plotting(circuit_type="Rd",qpu_limit=25)
    # comparative_ratio_plot(circuit_type="QFT", qpu_limit=15)
    # tele_ratio()

    # comparative_ratio_plot("Rd","trans",5)
    # iterative_progress()
    # extra_space_initialization_plot()
    # running_time()
    comparative_ratio_plot("Rd","trans",5,Performance_Gain_mode=True)