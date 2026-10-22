import duckdb
from pathlib import Path

# 1. 设定路径
staging_file = Path("projects/citibike/data/staging/trips_staging.parquet")
mart_dir = Path("projects/citibike/data/mart")
mart_dir.mkdir(parents=True, exist_ok=True)

print("=" * 20, "开始构建 Citi Bike Mart 数据集市（第二次分层）", "=" * 20)

# 2. 读取 Staging 清洗层数据（利用 DuckDB 直接极速查询 Parquet）
con = duckdb.connect()
con.execute(f"CREATE VIEW trips AS SELECT * FROM '{staging_file.as_posix()}'")

total_trips = con.execute("SELECT COUNT(*) FROM trips").fetchone()[0]
print(f"Staging 输入基准总行程数: {total_trips:,} 条\n")

# -------------------------------------------------------------------
# 集市表 1：站点周转与潮汐流向集市 (mart_station_flow)
# 核心指标：借车量(outflow)、还车量(inflow)、净流入差额(net_flow)
# -------------------------------------------------------------------
station_flow = con.execute("""
    WITH departures AS (
        SELECT start_station_name AS station_name,
               COUNT(*) AS departure_count
        FROM trips
        WHERE start_station_name != 'UNKNOWN'
        GROUP BY start_station_name
    ),
    arrivals AS (
        SELECT end_station_name AS station_name,
               COUNT(*) AS arrival_count
        FROM trips
        WHERE end_station_name != 'UNKNOWN'
        GROUP BY end_station_name
    )
    SELECT 
        COALESCE(d.station_name, a.station_name) AS "站点名称",
        COALESCE(d.departure_count, 0) AS "借出单量",
        COALESCE(a.arrival_count, 0) AS "还入单量",
        (COALESCE(a.arrival_count, 0) - COALESCE(d.departure_count, 0)) AS "净流入量(需调度)"
    FROM departures d
    FULL OUTER JOIN arrivals a ON d.station_name = a.station_name
    ORDER BY ABS("净流入量(需调度)") DESC
""").df()

flow_csv = mart_dir / "mart_station_flow.csv"
station_flow.to_csv(flow_csv, index=False, encoding="utf-8-sig")
print(f"1. 成功生成站点潮汐集市表: mart_station_flow.csv ({len(station_flow)} 个站点)")
print("   -> 潮汐失衡最严重的前 5 个站点预览:")
print(station_flow.head(5).to_string(index=False))


# -------------------------------------------------------------------
# 集市表 2：24小时分时与用户类型运营集市 (mart_hourly_user_trends)
# 核心维度：月份、小时、用户类型(member/casual)、车型
# 核心指标：行程单量、平均骑行时长(分钟)
# -------------------------------------------------------------------
hourly_trends = con.execute("""
    SELECT 
        strftime(start_time, '%Y-%m') AS "月份",
        EXTRACT(hour FROM start_time) AS "小时",
        CASE member_casual 
            WHEN 'member' THEN '注册会员' 
            WHEN 'casual' THEN '临时散客' 
            ELSE member_casual 
        END AS "用户类型",
        CASE rideable_type
            WHEN 'classic_bike' THEN '经典单车'
            WHEN 'electric_bike' THEN '电助力车'
            ELSE rideable_type
        END AS "车辆类型",
        COUNT(*) AS "骑行单量",
        ROUND(AVG(duration_min), 2) AS "平均时长(分)",
        ROUND(SUM(duration_min), 2) AS "总时长(分)"
    FROM trips
    GROUP BY 1, 2, 3, 4
    ORDER BY 1, 2, 3, 4
""").df()

trends_csv = mart_dir / "mart_hourly_user_trends.csv"
hourly_trends.to_csv(trends_csv, index=False, encoding="utf-8-sig")
print(f"\n2. 成功生成分时用户运营集市表: mart_hourly_user_trends.csv ({len(hourly_trends)} 行)")

# 3. 对账检查
trends_total_trips = hourly_trends["骑行单量"].sum()
print("\n" + "=" * 20, "Mart 集市行数一致性对账", "=" * 20)
print(f"Staging 总量: {total_trips:,} == 集市汇总总量: {trends_total_trips:,} -> {total_trips == trends_total_trips}")
