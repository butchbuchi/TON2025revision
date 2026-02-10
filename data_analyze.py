import pandas as pd
import glob

qpu_limit=25
circuit_type="QFT"
dir=f"C:/Users/Butch/Desktop/OneDrive - Stony Brook University/TON/NFT_perform_evals/parallel_processing_Data_trans/{circuit_type}/PGGL/{qpu_limit}_cap/2_extra_space"
max_path=f"{dir}/max.csv"
min_path=f"{dir}/min.csv"
average_path=f"{dir}/average.csv"
std_path=f"{dir}/std.csv"

dfs=[]
for run_id in range(18):
    df=pd.read_csv(f"{dir}/{run_id}.csv")
    df['run_id']=run_id
    dfs.append(df)  


all_data = pd.concat(dfs, ignore_index=True)

min_rows=all_data.loc[all_data.groupby("circuit_size")["y_local_reg"].idxmin()]
min_rows.to_csv(min_path, index=False)

max_rows=all_data.loc[all_data.groupby("circuit_size")["y_local_reg"].idxmax()]
max_rows.to_csv(max_path, index=False)

cols_to_avg = ["y_local_reg", "telegate_cost", "teledata_cost", "num_qpu", "time"]
mean_df = all_data.groupby("circuit_size", as_index=False)[cols_to_avg].mean()
mean_df.rename(columns={col: f"mean_{col}" for col in cols_to_avg}, inplace=True)
mean_df.to_csv(average_path, index=False)
std_df = all_data.groupby("circuit_size", as_index=False)[cols_to_avg].std()
std_df.rename(columns={col: f"std_{col}" for col in cols_to_avg}, inplace=True)
std_df.to_csv(std_path, index=False)



# import pandas as pd
# import os

# qpu_limit = 5
# dir = f"C:/Users/Butch/Desktop/OneDrive - Stony Brook University/ICDCS_2025/Camare_ready/Comprehensive_perform_evals/Data/QFT/Telegate"
# max_path = f"{dir}/QFT_{qpu_limit}_limitQPU_max.csv"
# min_path = f"{dir}/QFT_{qpu_limit}_limitQPU_min.csv"
# average_path = f"{dir}/QFT_{qpu_limit}_limitQPU_average.csv"
# std_path = f"{dir}/QFT_{qpu_limit}_limitQPU_std.csv"

# # 指定 CSV 的正确列名
# column_names = ["circuit_size", "y_local_reg", "time",  "num_qpu"]

# dfs = []

# for run_id in range(1,11):
#     csv_path = f"{dir}/QFT_{qpu_limit}_limitQPU({run_id}).csv"
#     try:
#         # 加载数据，不带标题
#         df = pd.read_csv(csv_path, header=None)
#         if df.shape[1] != len(column_names):
#             raise ValueError(f"Unexpected number of columns in {csv_path}")
#         df.columns = column_names
#         df["run_id"] = run_id
#         dfs.append(df)
#     except Exception as e:
#         print(f"⚠️ Failed to process {csv_path}: {e}")

# # 合并所有数据
# all_data = pd.concat(dfs, ignore_index=True)

# # 最小值行（按 y_local_reg）
# min_rows = all_data.loc[all_data.groupby("circuit_size")["y_local_reg"].idxmin()]
# min_rows.to_csv(min_path, index=False)

# # 最大值行（按 y_local_reg）
# max_rows = all_data.loc[all_data.groupby("circuit_size")["y_local_reg"].idxmax()]
# max_rows.to_csv(max_path, index=False)

# # 平均值
# cols_to_avg = ["y_local_reg", "time",  "num_qpu"]
# mean_df = all_data.groupby("circuit_size", as_index=False)[cols_to_avg].mean()
# mean_df.rename(columns={col: f"mean_{col}" for col in cols_to_avg}, inplace=True)
# mean_df.to_csv(average_path, index=False)

# # 标准差
# std_df = all_data.groupby("circuit_size", as_index=False)[cols_to_avg].std()
# std_df.rename(columns={col: f"std_{col}" for col in cols_to_avg}, inplace=True)
# std_df.to_csv(std_path, index=False)

# print("✅ All processing completed.")
