import csv
import random

# 生成的数据点数量
num_points = 100

# 经纬度范围（示例范围：近似中国部分地区）
lon_min, lon_max = 110, 130
lat_min, lat_max = 30, 50

# 热点区域中心（可设置多个簇）
hotspot_centers = [
    (115, 32),
    (117, 33.5),
    (112, 31.5)
]
hotspot_radius = 0.5  # 每个簇的半径（度），约50km

# 普通区域人口数量范围
population_min, population_max = 1000, 10000
# 热点区域人口数量范围
hotspot_population_min, hotspot_population_max = 50000, 100000

# 领域距离（单位：米），热点分析建议统一较小
fixed_distance = 1000  # 1km

# 生成数据
hotspot_points = int(num_points * 0.3)
normal_points = num_points - hotspot_points

data = []
# 生成热点簇内的点
for _ in range(hotspot_points):
    center = random.choice(hotspot_centers)
    # 在中心附近生成点（高斯分布更聚集）
    lon = random.gauss(center[0], hotspot_radius/3)
    lat = random.gauss(center[1], hotspot_radius/3)
    population = random.randint(hotspot_population_min, hotspot_population_max)
    distance = fixed_distance
    data.append([lon, lat, population, distance])

# 生成普通区域的点
for _ in range(normal_points):
    lon = random.uniform(lon_min, lon_max)
    lat = random.uniform(lat_min, lat_max)
    population = random.randint(population_min, population_max)
    distance = fixed_distance
    data.append([lon, lat, population, distance])

# 保存为 CSV 文件
filename = 'geo_hotspot_data.csv'
with open(filename, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    # 写入表头
    writer.writerow(['longitude', 'latitude', 'population', 'distance'])
    # 写入数据
    writer.writerows(data)

print(f"数据已成功保存到 {filename}")
    