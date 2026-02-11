import os
import pandas as pd
import matplotlib.pyplot as plt

dirs = [

    r"C:\Users\Butch\Desktop\TON2025revision\NFT_perform_evals\parallel_processing_Data_trans\Rd\PGGL\5_cap\1_extra_space",
    r"C:\Users\Butch\Desktop\TON2025revision\NFT_perform_evals\parallel_processing_Data_trans\Rd\PGGL\15_cap\1_extra_space",
    r"C:\Users\Butch\Desktop\TON2025revision\NFT_perform_evals\parallel_processing_Data_trans\Rd\PGGL\25_cap\1_extra_space",
     r"C:\Users\Butch\Desktop\TON2025revision\NFT_perform_evals\parallel_processing_Data_trans\QFT\PGGL\5_cap\1_extra_space",
    r"C:\Users\Butch\Desktop\TON2025revision\NFT_perform_evals\parallel_processing_Data_trans\QFT\PGGL\15_cap\1_extra_space",
    r"C:\Users\Butch\Desktop\TON2025revision\NFT_perform_evals\parallel_processing_Data_trans\QFT\PGGL\25_cap\1_extra_space"
]

styles = [
    dict(marker='.', markersize=18, linestyle='-', color='#AF58BA', alpha=1, linewidth=3),
    dict(marker='o', markersize=18, linestyle='-', color='#FFC61E', alpha=1, linewidth=3),
    dict(marker='*', markersize=18, linestyle='-', color='#F28522', alpha=1, linewidth=3),
    dict(marker='s', markersize=18, linestyle='-', color='#FF1F5B', alpha=1, linewidth=3),
    dict(marker='+', markersize=18, linestyle='-', color='#00CD6C', alpha=1, linewidth=3),
    dict(marker='x', markersize=18, linestyle='-', color='#009ADE', alpha=1, linewidth=3),
]

def parse_label(folder: str) -> str:
    parts = folder.split(os.sep)
    circuit_type = parts[-4]          # QFT or Rd
    cap = parts[-2].replace("_cap", "")
    return f"{circuit_type}, L={cap}"

def read_two_col_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df.iloc[:, :2].copy()
    df.columns = ["circuit_size", "value"]
    return df

plt.figure(figsize=(10, 7)) 

for d, style in zip(dirs, styles):
    avg_path = os.path.join(d, "average.csv")
    std_path = os.path.join(d, "std.csv")

    df_mean = read_two_col_csv(avg_path).rename(columns={"value": "mean"})
    df_std  = read_two_col_csv(std_path).rename(columns={"value": "std"})

    df = pd.merge(df_mean, df_std, on="circuit_size", how="inner")
    df = df.sort_values("circuit_size")

    df["cv_pct"] = (df["std"] / df["mean"]) * 100

    plt.plot(
        df["circuit_size"],
        df["cv_pct"],
        label=parse_label(d),
        **style
    )

plt.xlabel("Width",fontsize=26)
plt.ylabel("CV (%)",fontsize=26)
plt.title("Coefficient of Variation (CV)")


plt.tick_params(axis='x', labelsize=25)  
plt.tick_params(axis='y', labelsize=25)  

plt.legend(loc='lower right', bbox_to_anchor=(0.95, 0.45), fontsize=22, framealpha=0, edgecolor='none')
plt.grid(alpha=1,linestyle=':',linewidth=0.75)
plt.savefig("cv_six_lines.png", dpi=300)
plt.show()