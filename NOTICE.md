# 数据来源与使用边界

## Olist

- 数据：Olist 公开电商订单/商品明细数据；本地原始 CSV 由用户获取，来源为 Olist 官方公开仓库（用户确认；确切下载 URL、版本和许可对应关系仍待补核）。
- 本仓库只包含代码和聚合后的业务汇总表，不包含原始订单/明细 CSV。
- 金额为已送达订单商品金额（price）合计，不含运费；不是平台营业收入、利润或落袋现金。
- 6.77% 为项目口径“实际收货日 > 预计送达日”的晚到率，不是平台 SLA。

## Citi Bike

- 数据：Citi Bike / Jersey City 2025-04～06 官方行程数据，下载入口为 https://s3.amazonaws.com/tripdata/。
- 数据共享政策：https://citibikenyc.com/data-sharing-policy
- 本仓库不镜像原始 ZIP/CSV、Staging Parquet 或 Quarantine 明细；只保留聚合后的 mart CSV。
- 净流入为“还入 - 借出”的行程计数差，不等于车辆库存或调度效果。

## 代码

- 代码为个人学习/作品项目，AI 辅助生成和排查；关键指标与汇总用 SQL/Pandas 对账。
- 未附代码许可证；如需复用，请先与作者确认。
- 不使用或公开原单位内部数据、密码、Token 或个人信息。
