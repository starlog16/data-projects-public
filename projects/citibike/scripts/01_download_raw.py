import urllib.request
import zipfile
from pathlib import Path

# 1. 设定存储路径
raw_dir = Path("projects/citibike/data/raw")
raw_dir.mkdir(parents=True, exist_ok=True)

# 2. 官方数据源清单（Jersey City 2025年第二季度 4~6月）
files = [
    "JC-202504-citibike-tripdata.csv.zip",
    "JC-202505-citibike-tripdata.csv.zip",
    "JC-202506-citibike-tripdata.csv.zip",
]
base_url = "https://s3.amazonaws.com/tripdata/"

print("=" * 20, "开始下载 Citi Bike 官方批次数据", "=" * 20)

for filename in files:
    zip_path = raw_dir / filename
    url = base_url + filename
    
    # 下载 ZIP 包（若已存在则跳过重复下载）
    if not zip_path.exists():
        print(f"正在下载: {filename} ...")
        urllib.request.urlretrieve(url, zip_path)
        print(f"下载完成: {filename} ({zip_path.stat().st_size:,} 字节)")
    else:
        print(f"已存在跳过下载: {filename} ({zip_path.stat().st_size:,} 字节)")
        
    # 解压到 raw 目录
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for member in zip_ref.namelist():
            # 排除 Mac 系统隐藏文件
            if not member.startswith("__MACOSX"):
                zip_ref.extract(member, raw_dir)
                extracted_file = raw_dir / member
                print(f"  -> 解压出文件: {member} ({extracted_file.stat().st_size:,} 字节)")

print("\n" + "=" * 20, "批次数据解压就绪核验", "=" * 20)
for p in sorted(raw_dir.glob("*.csv")):
    print(f"原始数据文件: {p.name} | 大小: {p.stat().st_size:,} 字节")
