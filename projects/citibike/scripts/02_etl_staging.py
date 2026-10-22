import duckdb
import pandas as pd
from pathlib import Path

# 1. 设定路径
raw_dir = Path("projects/citibike/data/raw")
staging_dir = Path("projects/citibike/data/staging")
quarantine_dir = Path("projects/citibike/data/quarantine")

staging_dir.mkdir(parents=True, exist_ok=True)
quarantine_dir.mkdir(parents=True, exist_ok=True)

print("=" * 20, "开始执行 Citi Bike Staging 清洗与数据分流", "=" * 20)

# 2. 读取原始批次数据（利用 DuckDB 直接高性能全量扫描 raw 下的所有 CSV）
raw_files = str(raw_dir / "*.csv")

raw_df = duckdb.sql(f"""
    SELECT *,
           filename AS source_file
    FROM read_csv_auto('{raw_files}', filename=true)
""").df()

total_raw_rows = len(raw_df)
print(f"原始批次读取总行数: {total_raw_rows:,} 行")

# 3. 转换时间字段并计算时长（秒）
raw_df["start_time"] = pd.to_datetime(raw_df["started_at"], errors="coerce")
raw_df["end_time"] = pd.to_datetime(raw_df["ended_at"], errors="coerce")
raw_df["duration_sec"] = (raw_df["end_time"] - raw_df["start_time"]).dt.total_seconds()

# 4. 定义数据质量清洗规则（识别脏数据）
# 规则 A: 主键为空
cond_null_id = raw_df["ride_id"].isna()

# 规则 B: 时间解析失败
cond_invalid_time = raw_df["start_time"].isna() | raw_df["end_time"].isna()

# 规则 C: 负时长（时间倒挂）
cond_negative_duration = raw_df["duration_sec"] < 0

# 规则 D: 极短行程（少于 60 秒，通常为开锁后立刻锁车的误操作）
cond_too_short = (raw_df["duration_sec"] >= 0) & (raw_df["duration_sec"] < 60)

# 规则 E: 极长行程（超过 24 小时 = 86400 秒，属于丢车或未成功关锁异常）
cond_too_long = raw_df["duration_sec"] > 86400

# 综合异常标记
is_invalid = cond_null_id | cond_invalid_time | cond_negative_duration | cond_too_short | cond_too_long

# 5. 数据分流：隔离区 (Quarantine) 与合规清洗区 (Staging)
df_quarantine = raw_df[is_invalid].copy()
df_staging = raw_df[~is_invalid].copy()

# 为隔离数据标注异常原因
df_quarantine["reject_reason"] = "UNKNOWN"
df_quarantine.loc[cond_null_id, "reject_reason"] = "NULL_RIDE_ID"
df_quarantine.loc[cond_invalid_time, "reject_reason"] = "INVALID_TIMESTAMP"
df_quarantine.loc[cond_negative_duration, "reject_reason"] = "NEGATIVE_DURATION"
df_quarantine.loc[cond_too_short, "reject_reason"] = "DURATION_UNDER_60S"
df_quarantine.loc[cond_too_long, "reject_reason"] = "DURATION_OVER_24H"

# 对 staging 数据填充缺失站点名称为 'UNKNOWN'
df_staging["start_station_name"] = df_staging["start_station_name"].fillna("UNKNOWN")
df_staging["end_station_name"] = df_staging["end_station_name"].fillna("UNKNOWN")
df_staging["duration_min"] = (df_staging["duration_sec"] / 60.0).round(2)

# 6. 保存落盘
# 合规数据利用 DuckDB 原生引擎导出为高性能 Parquet（无需额外安装 pyarrow）
staging_parquet = (staging_dir / "trips_staging.parquet").as_posix()
duckdb.sql(f"COPY df_staging TO '{staging_parquet}' (FORMAT PARQUET)")

# 异常数据写入 quarantine 隔离区 (CSV 格式便于排查)
quarantine_file = quarantine_dir / "trips_quarantine.csv"
df_quarantine.to_csv(quarantine_file, index=False)

# 7. 严格的行数守恒对账检查
staging_rows = len(df_staging)
quarantine_rows = len(df_quarantine)

print("\n" + "=" * 20, "ETL Staging 质量与行数对账报告", "=" * 20)
print(f"原始输入总行数: {total_raw_rows:,}")
print(f"合规入模 (Staging) 行数: {staging_rows:,} (占比: {staging_rows/total_raw_rows*100:.2f}%)")
print(f"异常隔离 (Quarantine) 行数: {quarantine_rows:,} (占比: {quarantine_rows/total_raw_rows*100:.2f}%)")
print(f"行数平衡验证: {total_raw_rows} == {staging_rows} + {quarantine_rows} -> {total_raw_rows == staging_rows + quarantine_rows}")

print("\n隔离区异常原因分布:")
print(df_quarantine["reject_reason"].value_counts().to_string())
