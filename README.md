# 数据项目：Olist 履约分析与 Citi Bike 运营 ETL

两个本地可复现的数据项目，覆盖数据质量检查、DuckDB SQL、三层 ETL、业务指标与 Power BI 报表。

## 项目

| 项目 | 内容 | 技术栈 |
|---|---|---|
| [Olist 电商履约与经营分析](projects/olist/) | 9.9 万订单、11.2 万明细；履约时效、晚到率、状态/月度/商家汇总 | Python/Pandas、DuckDB、Power BI |
| [Citi Bike 运营 ETL 与集市](projects/citibike/) | 2025-04～06 三层 ETL；质量隔离、站点潮汐、分时用户集市 | Python、DuckDB、Parquet、Power BI |

## 数据与代码边界

- **原始数据不放入仓库**：Olist 原始 CSV、Citi Bike 原始 ZIP/CSV、Staging Parquet、Quarantine 明细均不公开镜像。
- 仓库只保留可公开的代码、聚合后的业务集市表和说明。原始数据按来源许可本地保管。
- 数据来源、版本与许可说明见 [NOTICE.md](NOTICE.md)。
- 两个项目均为个人学习/作品项目，AI 辅助生成和排查代码；关键指标与汇总用 SQL/Pandas 对账，未验证的部分在项目 README 中标注。
- 已核对的看板聚合表在 [dashboard/](dashboard/)；Power BI 看板需在 Desktop 中从这些表重建，仓库不存放损坏/旧的 PBIX。

## 快速运行

要求 Python 3.10+，安装依赖：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Olist：先按项目 README 下载官方原始数据，再运行：

```powershell
.\.venv\Scripts\python.exe projects/olist/scripts/01_inspect_data.py
```

Citi Bike：

```powershell
.\.venv\Scripts\python.exe projects/citibike/scripts/01_download_raw.py
.\.venv\Scripts\python.exe projects/citibike/scripts/02_etl_staging.py
.\.venv\Scripts\python.exe projects/citibike/scripts/03_etl_mart.py
```

## 口径与限制

- Olist 金额为已送达订单商品金额（price）合计，不含运费，不是平台营业收入、利润或落袋现金；6.77% 晚到率是“实际收货日 > 预计送达日”的项目口径，不是平台 SLA。
- Citi Bike 净流入为“还入 - 借出”的行程计数差，不等于车辆库存或调度效果；无用户 ID/历史库存，不做留存、缺车率或调度因果。
- 看板截图见 [screenshots/](screenshots/)；PBIX 与原始数据不放入仓库，本地 Power BI 文件仅用于面试演示。

