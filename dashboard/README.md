# 看板数据与重建说明

这里放的是**已核对的聚合表**，用于在 Power BI Desktop 中从零新建看板，不再修改旧 PBIX。

## Olist

导入：

- olists_kpi_summary.csv（注意：实际文件名是 olist_kpi_summary.csv）
- olist_monthly.csv
- olist_late_distribution.csv
- olist_seller_top20.csv

建议 3 页：

1. 经营总览
   - 卡片：订单量 96,478；商品金额 13,221,498.11 雷亚尔；运费 2,202,965.54。
   - 折线：olist_monthly 的 orders / gmv。
   - 环图：状态分布（可用原 status_summary.csv）。
2. 履约时效
   - 卡片：平均送达 12.56 天。
   - 环图：晚到 6,534（6.77%）/ 非晚到 89,936。
   - 柱图：olist_late_distribution 的晚到天数分箱。
3. 商家贡献
   - 条形图：olist_seller_top20 的商品金额 Top 10。
   - 表格：Top 20 商家编号、金额、订单数。

关键口径：

- 晚到率分母是 96,470 笔可计算耗时的已送达订单，不是 99,441。
- 平均送达 12.56 天；不要用旧 PBIX 的 12.50/7.47% 口径。
- 商品金额不是平台收入/利润。

## Citi Bike

导入：

- citi_kpi_summary.csv
- citi_station_top.csv
- citi_hourly.csv

建议 2 页：

1. 站点潮汐
   - 卡片：271,904 原始行；271,814 入模；90 隔离；278 站点。
   - 条形图：citi_station_top 按方向分组的净流入/净流出 Top 10。
   - 表格：站点、借出、还入、净流入。
2. 24 小时用户规律
   - 折线：citi_hourly 的 小时 / 骑行单量 / 用户类型。
   - 环图：车辆类型。
   - 柱图：用户类型 / 平均时长。

关键口径：

- 净流入是“还入 - 借出”的行程计数差，不是车辆库存。
- 90 行隔离全部是 >24h 异常；其他规则本批次未命中。
- 2025-03 有一条跨月行程，其余为 2025-04～06。

## 重要

- 不要再用脚本直接改 PBIX；PBIX 有 SecurityBindings，改报告定义会损坏。
- 在 Power BI Desktop 里新建、保存、截图；截图放 screenshots/。
