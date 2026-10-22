# Citi Bike Jersey City 运营 ETL 与集市

## 数据范围

- Jersey City 2025-04～06 官方 Citi Bike 行程数据。
- 原始 271,904 行；Staging 271,814 行；Quarantine 90 行；271,814 + 90 = 271,904。
- 原始 ZIP/CSV、Staging Parquet、Quarantine 明细均不放入仓库；可由脚本下载/生成。

## 三层结构

```text
raw/        官方原始 CSV（本地）
  ↓
staging/    清洗后的 Parquet 明细（本地）
  ↓
mart/       面向业务的集市表（可公开聚合结果）
quarantine/ 被规则拦截的异常明细（本地）
```

## 质量规则

实现 5 类规则：

1. 主键缺失 `NULL_RIDE_ID`
2. 时间解析失败 `INVALID_TIMESTAMP`
3. 负时长 `NEGATIVE_DURATION`
4. 小于 60 秒 `DURATION_UNDER_60S`
5. 超过 24 小时 `DURATION_OVER_24H`

本批次实际隔离 90 行，全部为超过 24 小时异常；其余规则已实现，但本批次未命中。

## 集市输出

- `mart_station_flow.csv`：278 个站点的借出单量、还入单量、净流入量（还入 - 借出）。
- `mart_hourly_user_trends.csv`：289 行，按月份、小时、用户类型、车辆类型汇总骑行单量、平均时长、总时长。
- 分时集市骑行单量合计 271,814，与 Staging 一致。

## 主要结果

- 站点净流入最高：Grove St PATH +1,055；净流出最大：Oakland Ave -517（行程计数差，不等于车辆库存）。
- 会员平均骑行 8.07 分钟，散客 16.33 分钟。
- 两类用户都在 17–18 点达到骑行峰值；会员 8 点为次高峰，散客 14–16 点为午后次高峰。
- 分时表含 1 条 2025-03 跨月行程（按开始时间归月），其余为 2025-04～06。

## 运行

```powershell
.\.venv\Scripts\python.exe projects/citibike/scripts/01_download_raw.py
.\.venv\Scripts\python.exe projects/citibike/scripts/02_etl_staging.py
.\.venv\Scripts\python.exe projects/citibike/scripts/03_etl_mart.py
```

## 限制

- 无用户 ID、历史库存或实际调度记录；不做用户留存、缺车率或调度效果因果判断。
- 净流入是行程计数差，不是车辆库存。
- 5 类规则已实现，不代表每类规则在本批次都有命中；本批次 90 行全部是 >24h。
- 数据许可见 NOTICE.md；不要将原始/明细数据公开镜像。
