import json
from typing import Any, List
from geopy.distance import geodesic
from shapely.geometry import Point, Polygon
from shapely.geometry.polygon import orient
from mcp.server.fastmcp import FastMCP
import os
import pandas as pd
import numpy as np
from scipy.spatial import distance_matrix
from scipy.stats import norm
import httpx

# 初始化 MCP 服务器
mcp = FastMCP("SpatialAnalysisServer")

try:
    import yaml
    def load_config():
        with open('config.yaml', 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    config = load_config()
except ImportError:
    config = None
    print("[警告] 未安装PyYAML，部分API功能不可用。请先 pip install pyyaml")
except Exception as e:
    config = None
    print(f"[警告] 读取config.yaml失败: {e}")

@mcp.tool()
async def calculate_geodesic_distance(coordinates_json: str) -> str:
    """
    计算两个地理坐标点之间的测地线距离（考虑地球曲率）
    
    Args:
        coordinates_json: 坐标数据，支持两种格式：
                         1. JSON格式：{"point1": [latitude1, longitude1], "point2": [latitude2, longitude2]}
                         2. 简化格式："纬度_经度,纬度_经度"，例如："39.90923_116.397428,31.23039_121.473702"
                         其中latitude为纬度，longitude为经度
        
    Returns:
        包含距离信息的JSON字符串
    """
    # 判断输入格式类型（JSON格式或简化字符串格式）
    if coordinates_json.startswith("{") and coordinates_json.endswith("}"):
        # JSON格式处理
        try:
            # 解析JSON数据
            data = json.loads(coordinates_json)
            
            # 检查输入格式
            if "point1" not in data or "point2" not in data:
                return json.dumps({
                    "status": "failure",
                    "info": "输入数据缺少'point1'或'point2'字段",
                    "input": coordinates_json
                }, ensure_ascii=False, indent=2)
                
            point1 = data["point1"]
            point2 = data["point2"]
            
            # 验证坐标格式
            if not isinstance(point1, list) or len(point1) != 2 or not isinstance(point2, list) or len(point2) != 2:
                return json.dumps({
                    "status": "failure",
                    "info": "坐标格式错误，应为[latitude, longitude]",
                    "input": coordinates_json
                }, ensure_ascii=False, indent=2)
            
            # 计算距离
            distance = geodesic(point1, point2)
            
            # 格式化结果
            formatted_result = {
                "status": "success",
                "distance_km": round(distance.kilometers, 2),  # 距离（公里），保留2位小数
                "distance_m": round(distance.meters, 2),       # 距离（米），保留2位小数
                "point1": point1,
                "point2": point2,
                "input_format": "json"
            }
            
            return json.dumps(formatted_result, ensure_ascii=False, indent=2)
            
        except json.JSONDecodeError:
            return json.dumps({
                "status": "failure",
                "info": "无效的JSON格式",
                "input": coordinates_json
            }, ensure_ascii=False, indent=2)
    else:
        # 简化字符串格式处理
        try:
            # 解析简化格式的坐标
            parts = coordinates_json.split(',')
            if len(parts) != 2:
                return json.dumps({
                    "status": "failure",
                    "info": "坐标格式错误，应为'纬度_经度,纬度_经度'",
                    "input": coordinates_json
                }, ensure_ascii=False, indent=2)
            
            # 解析第一个坐标点
            try:
                lat1, lon1 = parts[0].split('_')
                point1 = [float(lat1), float(lon1)]
            except ValueError:
                return json.dumps({
                    "status": "failure",
                    "info": "第一个坐标点格式错误，应为'纬度_经度'",
                    "input": parts[0]
                }, ensure_ascii=False, indent=2)
            
            # 解析第二个坐标点
            try:
                lat2, lon2 = parts[1].split('_')
                point2 = [float(lat2), float(lon2)]
            except ValueError:
                return json.dumps({
                    "status": "failure",
                    "info": "第二个坐标点格式错误，应为'纬度_经度'",
                    "input": parts[1]
                }, ensure_ascii=False, indent=2)
            
            # 计算距离
            distance = geodesic(point1, point2)
            
            # 格式化结果
            formatted_result = {
                "status": "success",
                "distance_km": round(distance.kilometers, 2),  # 距离（公里），保留2位小数
                "distance_m": round(distance.meters, 2),       # 距离（米），保留2位小数
                "point1": {
                    "latitude": point1[0],
                    "longitude": point1[1],
                    "formatted": f"{point1[0]}_{point1[1]}"
                },
                "point2": {
                    "latitude": point2[0],
                    "longitude": point2[1],
                    "formatted": f"{point2[0]}_{point2[1]}"
                },
                "input_format": "simple"
            }
            
            return json.dumps(formatted_result, ensure_ascii=False, indent=2)
        
        except Exception as e:
            return json.dumps({
                "status": "failure",
                "info": f"计算距离时出错: {str(e)}",
                "input": coordinates_json
            }, ensure_ascii=False, indent=2)


@mcp.tool()
async def read_table_file(file_path: str, nrows: int = 5) -> str:
    """
    读取CSV或Excel文件的前几行数据，用户只需输入文件路径。
    Args:
        file_path: 文件路径，支持csv、xls、xlsx
        nrows: 返回前几行，默认5行
    Returns:
        包含字段名和前几行数据的JSON字符串
    """
    import os
    import pandas as pd

    if not os.path.exists(file_path):
        return json.dumps({
            "status": "failure",
            "info": f"文件不存在: {file_path}"
        }, ensure_ascii=False, indent=2)

    try:
        if file_path.lower().endswith('.csv'):
            df = pd.read_csv(file_path, nrows=nrows)
            file_type = "csv"
        elif file_path.lower().endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file_path, nrows=nrows)
            file_type = "excel"
        else:
            return json.dumps({
                "status": "failure",
                "info": "仅支持csv、xls、xlsx文件"
            }, ensure_ascii=False, indent=2)

        result = {
            "status": "success",
            "file_type": file_type,
            "columns": df.columns.tolist(),
            "preview": df.fillna("").astype(str).values.tolist()
        }
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "failure",
            "info": f"读取文件时出错: {str(e)}"
        }, ensure_ascii=False, indent=2)


@mcp.tool()
async def analyze_distance_distribution(file_path: str, distance_col: str = "distance") -> str:
    """
    分析距离列的分布情况
    Args:
        file_path: 数据文件路径（csv/xls/xlsx）
        distance_col: 距离字段名，默认为"distance"
    Returns:
        JSON字符串，包含距离分布的统计信息
    """
    if not os.path.exists(file_path):
        return json.dumps({
            "status": "failure",
            "info": f"文件不存在: {file_path}"
        }, ensure_ascii=False, indent=2)

    try:
        if file_path.lower().endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.lower().endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file_path)
        else:
            return json.dumps({
                "status": "failure",
                "info": "仅支持csv、xls、xlsx文件"
            }, ensure_ascii=False, indent=2)

        if distance_col not in df.columns:
            return json.dumps({
                "status": "failure",
                "info": f"缺少距离字段: {distance_col}"
            }, ensure_ascii=False, indent=2)

        distances = df[distance_col].astype(float)
        
        # 计算基本统计量
        stats = {
            "count": len(distances),
            "mean": float(distances.mean()),
            "std": float(distances.std()),
            "min": float(distances.min()),
            "max": float(distances.max()),
            "median": float(distances.median()),
            "q1": float(distances.quantile(0.25)),
            "q3": float(distances.quantile(0.75)),
            "percentiles": {
                "10": float(distances.quantile(0.1)),
                "25": float(distances.quantile(0.25)),
                "50": float(distances.quantile(0.5)),
                "75": float(distances.quantile(0.75)),
                "90": float(distances.quantile(0.9))
            }
        }
        
        # 计算距离区间分布
        bins = [0, 100, 500, 1000, 2000, 5000, float('inf')]
        labels = ['0-100m', '100-500m', '500-1000m', '1-2km', '2-5km', '>5km']
        distance_ranges = pd.cut(distances, bins=bins, labels=labels)
        range_counts = distance_ranges.value_counts().to_dict()
        
        return json.dumps({
            "status": "success",
            "statistics": stats,
            "distance_ranges": range_counts
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "failure",
            "info": f"分析距离分布时出错: {str(e)}"
        }, ensure_ascii=False, indent=2)


@mcp.tool()
async def hotspot_analysis_getis_ord_gi_star(file_path: str, lat_col: str, lon_col: str, value_col: str, distance_threshold: float = None) -> str:
    """
    基于Getis-Ord Gi*的热点分析。
    Args:
        file_path: 数据文件路径（csv/xls/xlsx）
        lat_col: 纬度字段名
        lon_col: 经度字段名
        value_col: 参与分析的数值字段名
        distance_threshold: 邻域距离（米），如果为None则使用数据中的distance列
    Returns:
        JSON字符串，包含每个点的Gi*、Z分数、p值、热点/冷点标签等
    """
    if not os.path.exists(file_path):
        return json.dumps({
            "status": "failure",
            "info": f"文件不存在: {file_path}"
        }, ensure_ascii=False, indent=2)

    try:
        if file_path.lower().endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.lower().endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file_path)
        else:
            return json.dumps({
                "status": "failure",
                "info": "仅支持csv、xls、xlsx文件"
            }, ensure_ascii=False, indent=2)

        # 检查字段
        for col in [lat_col, lon_col, value_col]:
            if col not in df.columns:
                return json.dumps({
                    "status": "failure",
                    "info": f"缺少字段: {col}"
                }, ensure_ascii=False, indent=2)

        coords = df[[lat_col, lon_col]].values
        values = df[value_col].values.astype(float)
        n = len(df)
        
        # 经纬度转弧度
        coords_rad = np.radians(coords)
        # 计算球面距离（单位：米）
        from sklearn.metrics.pairwise import haversine_distances
        dists = haversine_distances(coords_rad, coords_rad) * 6371000  # 地球半径
        
        # 权重矩阵
        if distance_threshold is None and "distance" in df.columns:
            distance_arr = df["distance"].values.astype(float)
            wij = np.zeros((n, n), dtype=int)
            for i in range(n):
                wij[i] = (dists[i] <= distance_arr[i]).astype(int)
        else:
            if distance_threshold is None:
                distance_threshold = 1000.0  # 默认值
            wij = (dists <= distance_threshold).astype(int)
        
        np.fill_diagonal(wij, 0)
        
        # 计算Gi*
        sum_wij = wij.sum(axis=1)
        xj = values
        xj_sum = np.sum(xj)
        xj2_sum = np.sum(xj ** 2)
        mean_x = xj_sum / n
        s = np.sqrt((xj2_sum / n) - mean_x ** 2)
        
        results = []
        for i in range(n):
            wij_i = wij[i]
            sum_wij_i = sum_wij[i]
            num = np.sum(wij_i * xj)
            denom = s * np.sqrt((n * np.sum(wij_i ** 2) - sum_wij_i ** 2) / (n - 1))
            
            if denom == 0:
                gi_star = 0
                z_score = 0
                p_value = 1
            else:
                gi_star = (num - mean_x * sum_wij_i) / denom
                z_score = gi_star
                p_value = 2 * (1 - norm.cdf(abs(z_score)))
            
            # 使用更严格的显著性水平
            if z_score > 2.58:  # 99% 置信水平
                label = "hotspot"
            elif z_score < -2.58:
                label = "coldspot"
            else:
                label = "not significant"
                
            results.append({
                "index": int(i),
                "latitude": float(coords[i][0]),
                "longitude": float(coords[i][1]),
                "value": float(xj[i]),
                "gi_star": float(gi_star),
                "z_score": float(z_score),
                "p_value": float(p_value),
                "label": label,
                "neighbors": int(sum_wij_i)  # 添加邻域点数量
            })
            
        return json.dumps({
            "status": "success",
            "count": n,
            "distance_threshold": float(distance_threshold) if distance_threshold is not None else "variable",
            "results": results
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "failure",
            "info": f"热点分析出错: {str(e)}"
        }, ensure_ascii=False, indent=2)


@mcp.tool()
async def search_nearby_poi(location: str, keywords: str = "", poi_type: str = "", radius: int = 5000, page: int = 1, offset: int = 20) -> str:
    """
    使用高德地图API搜索周边POI
    """
    if not config or 'api' not in config or 'gaode_key' not in config['api']:
        return json.dumps({"status": "failure", "info": "高德API配置缺失或PyYAML未安装"}, ensure_ascii=False, indent=2)
    params = {
        'key': config['api']['gaode_key'],
        'location': location,
        'radius': radius,
        'page': page,
        'offset': offset,
        'extensions': 'all',
        'sortrule': 'distance'
    }
    if keywords:
        params['keywords'] = keywords
    if poi_type:
        params['types'] = poi_type
    base_url = "https://restapi.amap.com/v3/place/around"
    async with httpx.AsyncClient() as client:
        response = await client.get(url=base_url, params=params)
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == '1':
                formatted_result = {
                    "status": "success",
                    "count": result.get('count', '0'),
                    "pois": result.get('pois', []),
                    "center": location,
                    "radius": radius,
                    "search_query": {
                        "keywords": keywords,
                        "poi_type": poi_type
                    }
                }
                return json.dumps(formatted_result, ensure_ascii=False, indent=2)
            else:
                error_result = {
                    "status": "failure",
                    "info": result.get('info', '未知错误'),
                    "infocode": result.get('infocode', ''),
                    "search_query": {
                        "location": location,
                        "keywords": keywords,
                        "poi_type": poi_type,
                        "radius": radius
                    }
                }
                return json.dumps(error_result, ensure_ascii=False, indent=2)
        else:
            return json.dumps({
                "status": "failure",
                "info": f"HTTP错误: {response.status_code}",
                "search_query": {
                    "location": location,
                    "keywords": keywords,
                    "poi_type": poi_type,
                    "radius": radius
                }
            }, ensure_ascii=False, indent=2)


@mcp.tool()
async def geocode_address(address: str, city: str = "") -> str:
    """
    使用高德地图API将地址转换为坐标
    """
    if not config or 'api' not in config or 'gaode_key' not in config['api']:
        return json.dumps({"status": "failure", "info": "高德API配置缺失或PyYAML未安装"}, ensure_ascii=False, indent=2)
    params = {
        'key': config['api']['gaode_key'],
        'address': address,
    }
    if city:
        params['city'] = city
    base_url = "https://restapi.amap.com/v3/geocode/geo"
    async with httpx.AsyncClient() as client:
        response = await client.get(url=base_url, params=params)
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == '1' and result.get('geocodes', []):
                first_result = result['geocodes'][0]
                formatted_result = {
                    "status": "success",
                    "original_address": address,
                    "formatted_address": first_result.get('formatted_address', ''),
                    "location": first_result.get('location', ''),
                    "level": first_result.get('level', ''),
                    "city": first_result.get('city', ''),
                    "district": first_result.get('district', ''),
                    "adcode": first_result.get('adcode', '')
                }
                return json.dumps(formatted_result, ensure_ascii=False, indent=2)
            else:
                error_result = {
                    "status": "failure",
                    "info": result.get('info', '未知错误'),
                    "infocode": result.get('infocode', ''),
                    "query_address": address
                }
                return json.dumps(error_result, ensure_ascii=False, indent=2)
        else:
            return json.dumps({
                "status": "failure",
                "info": f"HTTP错误: {response.status_code}",
                "query_address": address
            }, ensure_ascii=False, indent=2)


@mcp.tool()
async def calculate_route_distance(origin: str, destination: str, mode: str = "driving") -> str:
    """
    使用高德地图API计算两地之间的路线距离
    """
    if not config or 'api' not in config or 'gaode_key' not in config['api']:
        return json.dumps({"status": "failure", "info": "高德API配置缺失或PyYAML未安装"}, ensure_ascii=False, indent=2)
    valid_modes = ["driving", "walking", "bicycling", "transit"]
    if mode not in valid_modes:
        return json.dumps({
            "status": "failure",
            "info": f"无效的mode参数: {mode}。有效值为: {', '.join(valid_modes)}",
            "query": {
                "origin": origin,
                "destination": destination,
                "mode": mode
            }
        }, ensure_ascii=False, indent=2)
    if mode == "driving":
        base_url = "https://restapi.amap.com/v3/direction/driving"
    elif mode == "walking":
        base_url = "https://restapi.amap.com/v3/direction/walking"
    elif mode == "bicycling":
        base_url = "https://restapi.amap.com/v4/direction/bicycling"
    elif mode == "transit":
        base_url = "https://restapi.amap.com/v3/direction/transit/integrated"
    params = {
        'key': config['api']['gaode_key'],
        'origin': origin,
        'destination': destination,
        'extensions': 'base'
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url=base_url, params=params)
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == '1':
                if mode == "driving":
                    route = result.get('route', {})
                    paths = route.get('paths', [])
                    if paths:
                        first_path = paths[0]
                        formatted_result = {
                            "status": "success",
                            "mode": mode,
                            "origin": origin,
                            "destination": destination,
                            "distance": first_path.get('distance', '0'),
                            "duration": first_path.get('duration', '0'),
                            "tolls": first_path.get('tolls', '0'),
                            "toll_distance": first_path.get('toll_distance', '0')
                        }
                        return json.dumps(formatted_result, ensure_ascii=False, indent=2)
                elif mode in ["walking", "bicycling"]:
                    route = result.get('route', {})
                    paths = route.get('paths', [])
                    if paths:
                        first_path = paths[0]
                        formatted_result = {
                            "status": "success",
                            "mode": mode,
                            "origin": origin,
                            "destination": destination,
                            "distance": first_path.get('distance', '0'),
                            "duration": first_path.get('duration', '0')
                        }
                        return json.dumps(formatted_result, ensure_ascii=False, indent=2)
                elif mode == "transit":
                    route = result.get('route', {})
                    formatted_result = {
                        "status": "success",
                        "mode": mode,
                        "origin": origin,
                        "destination": destination,
                        "distance": route.get('distance', '0'),
                        "taxi_cost": route.get('taxi_cost', '0'),
                        "transits": route.get('transits', [])
                    }
                    return json.dumps(formatted_result, ensure_ascii=False, indent=2)
            error_result = {
                "status": "failure",
                "info": result.get('info', '未知错误'),
                "infocode": result.get('infocode', ''),
                "query": {
                    "origin": origin,
                    "destination": destination,
                    "mode": mode
                }
            }
            return json.dumps(error_result, ensure_ascii=False, indent=2)
        else:
            return json.dumps({
                "status": "failure",
                "info": f"HTTP错误: {response.status_code}",
                "query": {
                    "origin": origin,
                    "destination": destination,
                    "mode": mode
                }
            }, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    mcp.run(transport='stdio')
    