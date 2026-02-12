# import pandas as pd


# trans_type="trans"
# Circuit_type="Rd"
# limit_qpu=25
# num_qubit=100
# extra_space=1
# # ==== 修改这里 ====
# file_path = rf"NFT_perform_evals/Data_{trans_type}/{Circuit_type}/Buffer/{limit_qpu}_cap/circuit_size_{num_qubit}/{extra_space}_extra_space/0.csv"

# # 读取 CSV
# df = pd.read_csv(file_path)

# # 第二列是 Buffer_times
# buffer_times = df.iloc[:, 1]

# # 统计出现次数
# counts = buffer_times.value_counts().sort_index()

# # 计算占比
# proportions = buffer_times.value_counts(normalize=True).sort_index()

# # 合并结果
# result = pd.DataFrame({
#     "count": counts,
#     "proportion": proportions
# })

# print(result)









########################################################


import pandas as pd

trans_type="trans"
Circuit_type="Rd"
limit_qpu=25
num_qubit=100
extra_space=1

file_path = rf"NFT_perform_evals/Data_{trans_type}/{Circuit_type}/Buffer/{limit_qpu}_cap/circuit_size_{num_qubit}/{extra_space}_extra_space/0_1.csv"

df = pd.read_csv(file_path)

# 强制转成数值，非法变 NaN
buffer_times = pd.to_numeric(df.iloc[:, 1], errors="coerce")

total_all = len(buffer_times)

# ---------------------------
# 统计 NaN
# ---------------------------
nan_count = buffer_times.isna().sum()
nan_ratio = nan_count / total_all

print("=== NaN Statistics ===")
print(f"NaN count: {nan_count}")
print(f"NaN ratio: {nan_ratio:.6f}")

# ---------------------------
# 去除 NaN 后再统计
# ---------------------------
buffer_times = buffer_times.dropna()
total_valid = len(buffer_times)

# ---------------------------
# 分桶（拆出 500）
# ---------------------------
buckets = {
    "-1": (buffer_times == -1),
    "0": (buffer_times == 0),
    "1–2": (buffer_times.between(1, 2)),
    "3–5": (buffer_times.between(3, 5)),
    "6–10": (buffer_times.between(6, 10)),
    "11–499": (buffer_times.between(11, 499)),
    "500": (buffer_times == 500),
    "501+": (buffer_times >= 501),
}

counts = {k: v.sum() for k, v in buckets.items()}

# ✅ 归一化（使用有效样本数）
proportions = {k: counts[k] / total_valid for k in buckets}

result = pd.DataFrame({
    "count": counts,
    "proportion": proportions
})

order = ["-1", "0", "1–2", "3–5", "6–10", "11–499", "500", "501+"]
result = result.loc[order]

# ---------------------------
# 单独统计 1–499
# ---------------------------
count_1_499 = buffer_times.between(1, 499).sum()
ratio_1_499 = count_1_499 / total_valid

print("\n=== Bucketed Distribution (Normalized) ===")
print(result)

print("\n=== Overall 1–499 ===")
print(f"Count: {count_1_499}")
print(f"Proportion: {ratio_1_499:.6f}")

print("\n=== Check Sum (Should be 1) ===")
print("Sum of proportions:", result["proportion"].sum())



######################################################
# import pandas as pd

# # 读取
# df = pd.read_csv(file_path)
# buffer_times = df.iloc[:, 1]

# # 找到 NaN
# nan_mask = buffer_times.isna()

# nan_indices = buffer_times[nan_mask].index

# print("=== NaN Indices ===")
# print(nan_indices.tolist())

# print("\nTotal NaN count:", nan_mask.sum())