import pandas as pd

orders = pd.read_csv(
    "projects/olist/data/raw/olist_orders_dataset.csv",
    dtype={"order_id": "string"},
)
items = pd.read_csv(
    "projects/olist/data/raw/olist_order_items_dataset.csv",
    dtype={"order_id": "string"},
)

print("订单表行列数：", orders.shape)
print("不同订单编号数：", orders["order_id"].nunique())
print("订单编号缺失数：", orders["order_id"].isna().sum())
print("订单编号重复数：", orders.duplicated(subset=["order_id"]).sum())
# 查看所有列名；tolist() 将列名转成列表，方便打印
print(orders.columns.tolist())

# 查看前三条记录，不改变原表
print(orders.head(3))

# 明细条数、列数，以及涉及多少笔不同订单
print("明细表行列数：", items.shape)
print("明细表中不同订单数：", items["order_id"].nunique())
print("明细表中不同商家数：", items["seller_id"].nunique())

# 同时选出两列，分别统计缺失数量
print("明细编号字段的缺失数：")
print(items[["order_id", "order_item_id"]].isna().sum())

# 把订单编号和明细序号组合起来，检查重复
print("重复明细数：",
      items.duplicated(subset=["order_id", "order_item_id"]).sum())
# 判断订单表中的每个订单编号，是否出现在明细表里
has_items = orders["order_id"].isin(items["order_id"])

# 取出没有找到明细的订单
orders_without_items = orders[~has_items]

print("没有明细的订单数：", len(orders_without_items))
print("这些订单的状态分布：")
print(orders_without_items["order_status"].value_counts(dropna=False))

has_order = items["order_id"].isin(orders["order_id"])
items_without_orders = items[~has_order]
print("没有订单的明细数：",len(items_without_orders))
print("全部订单状态分布：")
print(orders["order_status"].value_counts(dropna=False))

# 选出状态为“已送达”的订单，建立独立工作副本
delivered_orders = orders[
    orders["order_status"] == "delivered"
].copy()

# 本次要检查的三个时间字段
time_cols = [
    "order_purchase_timestamp",       # 下单时间
    "order_delivered_customer_date",  # 实际送达时间
    "order_estimated_delivery_date",  # 预计送达日期
]

print("已送达订单数：", len(delivered_orders))
print("已送达订单的关键时间缺失数：")
print(delivered_orders[time_cols].isna().sum())


# 1. 取出原来的下单时间列
purchase_raw = delivered_orders["order_purchase_timestamp"]

# 2. 把日期文字转换成日期时间，结果放进新变量
purchase_time = pd.to_datetime(purchase_raw, errors="coerce")

# 3. 查看转换前后的类型
print("转换前类型：", purchase_raw.dtype)
print("转换后类型：", purchase_time.dtype)

# 4. 检查转换过程新增了多少个缺失值
print("新增无法解析数量：",
      purchase_time.isna().sum() - purchase_raw.isna().sum())
arrival_raw = delivered_orders["order_delivered_customer_date"]
arrival_time = pd.to_datetime(arrival_raw, errors="coerce")

print("送达时间新增解析失败：",
      arrival_time.isna().sum() - arrival_raw.isna().sum())

delivery_duration = arrival_time - purchase_time
delivery_days = delivery_duration.dt.total_seconds() / 86400

print("前5笔耗时（天）：")
print(delivery_days.head(5))

print("耗时无法计算的订单数：", delivery_days.isna().sum())
print("耗时为负的订单数：", (delivery_days < 0).sum())


import duckdb

# 把已有的耗时列准备成一张单列表，供SQL读取
duration_data = pd.DataFrame({"delivery_days": delivery_days})

result = duckdb.sql("""
    SELECT
        COUNT(*) AS sample_orders,
ROUND(AVG(delivery_days), 2) AS avg_days,
ROUND(MEDIAN(delivery_days), 2) AS median_days,
ROUND(QUANTILE_CONT(delivery_days, 0.9), 2) AS p90_days,
ROUND(MAX(delivery_days), 2) AS max_days
    FROM duration_data
    WHERE delivery_days IS NOT NULL
      AND delivery_days >= 0
""").df()

print(result)


# 把已经算好的耗时，放回内存中的订单工作表
delivered_orders["delivery_days"] = delivery_days

slowest_orders = duckdb.sql("""
    SELECT
        order_id AS "订单编号",
        order_purchase_timestamp AS "下单时间",
        order_delivered_customer_date AS "收货时间",
        ROUND(delivery_days, 2) AS "耗时天数"
    FROM delivered_orders
    WHERE delivery_days IS NOT NULL
      AND delivery_days >= 0
    ORDER BY delivered_orders.delivery_days DESC, order_id
    LIMIT 5
""").df()

# 完整显示这5笔记录
print(slowest_orders.to_string(index=False))


long_wait_summary = duckdb.sql("""
    SELECT
        COUNT(*) AS sample_orders,
        SUM(CASE WHEN delivery_days > 30
                 THEN 1 ELSE 0 END) AS over_30_orders,
        ROUND(100.0 * AVG(
            CASE WHEN delivery_days > 30
                 THEN 1 ELSE 0 END
        ), 2) AS over_30_pct
    FROM delivered_orders
    WHERE delivery_days IS NOT NULL
      AND delivery_days >= 0
""").df()

print(long_wait_summary)

# 转换预计送达日期，检查有没有新增解析失败
estimated_raw = delivered_orders["order_estimated_delivery_date"]
estimated_time = pd.to_datetime(estimated_raw, errors="coerce")

print("预计日期新增解析失败：",
      estimated_time.isna().sum() - estimated_raw.isna().sum())

# 实际收货日期、预计送达日期
delivered_orders["arrival_date"] = arrival_time.dt.date
delivered_orders["estimated_date"] = estimated_time.dt.date


late_summary = duckdb.sql("""
    SELECT
        COUNT(*) AS sample_orders,
        SUM(CASE WHEN arrival_date > estimated_date
                 THEN 1 ELSE 0 END) AS late_orders,
        ROUND(100.0 * AVG(
            CASE WHEN arrival_date > estimated_date
                 THEN 1 ELSE 0 END
        ), 2) AS late_pct
    FROM delivered_orders
    WHERE delivery_days IS NOT NULL
      AND delivery_days >= 0
      AND arrival_date IS NOT NULL
      AND estimated_date IS NOT NULL
""").df()

print(late_summary)


late_severity = duckdb.sql("""
    SELECT
        COUNT(*) AS late_orders,
        ROUND(AVG(
            date_diff('day', estimated_date, arrival_date)
        ), 2) AS avg_late_days,
        MEDIAN(
            date_diff('day', estimated_date, arrival_date)
        ) AS median_late_days
    FROM delivered_orders
    WHERE delivery_days IS NOT NULL
      AND delivery_days >= 0
      AND arrival_date IS NOT NULL
      AND estimated_date IS NOT NULL
      AND arrival_date > estimated_date
""").df()

print(late_severity)


# 取出商品金额和运费两列
money = items[["price", "freight_value"]]

print("金额字段类型：")
print(money.dtypes)

# 每个字段分别统计，整理成一张检查表
money_check = pd.DataFrame({
    "缺失数": money.isna().sum(),
    "负数数": (money < 0).sum(),
    "零值数": (money == 0).sum(),
    "最小值": money.min(),
    "中位数": money.median(),
    "最大值": money.max(),
})

print(money_check.to_string())


print("商家编号缺失数：", items["seller_id"].isna().sum())

# 按订单编号，把属于同一订单的明细汇总
order_items_summary = duckdb.sql("""
    SELECT
        order_id,
        COUNT(*) AS item_count,
        COUNT(DISTINCT seller_id) AS seller_count,
        SUM(price) AS item_amount,
        SUM(freight_value) AS freight_amount
    FROM items
    GROUP BY order_id
    ORDER BY order_id
""").df()

print(order_items_summary.head(5).round(2).to_string(index=False))

# 检查汇总后，条数和金额有没有丢失或重复
print("汇总订单数：", len(order_items_summary))
print("重复订单编号数：",
      order_items_summary.duplicated(subset=["order_id"]).sum())
print("明细条数合计：", order_items_summary["item_count"].sum())

print("商品金额对账（原明细、汇总后）：",
      round(items["price"].sum(), 2),
      round(order_items_summary["item_amount"].sum(), 2))

print("运费对账（原明细、汇总后）：",
      round(items["freight_value"].sum(), 2),
      round(order_items_summary["freight_amount"].sum(), 2))


order_analysis = duckdb.sql("""
    SELECT
        o.*,
        s.item_count,
        s.seller_count,
        s.item_amount,
        s.freight_amount
    FROM orders AS o
    LEFT JOIN order_items_summary AS s
        ON o.order_id = s.order_id
""").df()

# 以下是检查模板，运行后看中文结果即可
print("连接后订单数：", len(order_analysis))
print("重复订单编号数：", order_analysis["order_id"].duplicated().sum())
print("没有明细的订单数：", order_analysis["item_count"].isna().sum())
print("商品金额合计：", round(order_analysis["item_amount"].sum(), 2))
print("运费合计：", round(order_analysis["freight_amount"].sum(), 2))


# 按订单状态，统计订单数及对应金额
status_summary = duckdb.sql("""
    SELECT
        order_status AS "订单状态",
        COUNT(*) AS "订单数",
        COUNT(item_count) AS "有明细订单数",
        ROUND(SUM(item_amount), 2) AS "商品金额",
        ROUND(SUM(freight_amount), 2) AS "运费"
    FROM order_analysis
    GROUP BY order_status
    ORDER BY COUNT(*) DESC
""").df()

# 订单占比 = 该状态订单数 ÷ 全部订单数 × 100
status_summary["订单占比%"] = (
    status_summary["订单数"] / len(order_analysis) * 100
).round(2)

print(status_summary.to_string(index=False))


# 按下单月份，汇总最终已送达订单的经营指标
# 月份按下单时间归属，不表示订单在下单当月完成送达。
monthly_summary = duckdb.sql("""
    SELECT
        SUBSTR(order_purchase_timestamp, 1, 7) AS "下单月份",
        COUNT(*) AS "已送达订单数",
        ROUND(SUM(item_amount), 2) AS "商品金额",
        ROUND(SUM(freight_amount), 2) AS "运费",
        ROUND(AVG(item_amount), 2) AS "平均每单商品金额"
    FROM order_analysis
    WHERE order_status = 'delivered'
    GROUP BY SUBSTR(order_purchase_timestamp, 1, 7)
    ORDER BY "下单月份"
""").df()

print("按下单月份汇总最终已送达订单：")
print(monthly_summary.to_string(index=False))


# 商家贡献：只汇总最终已送达订单中，属于该商家的商品明细金额。
# 同一订单可能包含多个商家，因此“涉及订单数”不能跨商家直接相加。
seller_summary = duckdb.sql("""
    SELECT
        i.seller_id AS "商家编号",
        COUNT(DISTINCT i.order_id) AS "涉及订单数",
        COUNT(*) AS "商品明细数",
        ROUND(SUM(i.price), 2) AS "商品金额",
        ROUND(SUM(i.freight_value), 2) AS "运费"
    FROM items AS i
    INNER JOIN orders AS o
        ON i.order_id = o.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY i.seller_id
    ORDER BY "商品金额" DESC, "商家编号"
""").df()

# 完整结果保留在seller_summary中，屏幕先展示金额前10名。
print("商品金额前10的商家（仅最终已送达订单的明细）：")
print(seller_summary.head(10).to_string(index=False))


# 将已计算的经营分析表保存为CSV，供Power BI读取或对账。
# 只更新下列4个生成文件；重复运行替换同名结果，不追加行，不改raw原文件。
from pathlib import Path

export_dir = Path("projects/olist/data/processed")
export_dir.mkdir(parents=True, exist_ok=True)

export_tables = {
    "order_analysis": order_analysis,
    "status_summary": status_summary,
    "monthly_summary": monthly_summary,
    "seller_summary": seller_summary,
}

for name, table in export_tables.items():
    output_file = export_dir / f"{name}.csv"
    table.to_csv(output_file, index=False, encoding="utf-8-sig")
    print(f"已导出 {name}.csv：{len(table)} 行")
