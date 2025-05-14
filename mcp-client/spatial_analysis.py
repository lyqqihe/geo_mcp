import httpx
import yaml
from mcp.server import FastMCP
import json
from urllib.parse import urlencode
from geopy.distance import geodesic  # 添加geopy库的导入

# 初始化 FastMCP 服务器
app = FastMCP('spatial-analysis')

# 加载配置文件
def load_config():
    with open('config.yaml', 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

config = load_config()


@app.tool()
async def search_nearby_poi(location: str, keywords: str = "", poi_type: str = "", radius: int = 5000, page: int = 1, offset: int = 20) -> str:
    """
    使用高德地图API搜索周边POI
    
    Args:
        location: 中心点坐标(经度,纬度)，如"116.473168,39.993015"
        keywords: 查询关键字，如"餐馆"、"学校"等
        poi_type: POI类型代码，如"050000"(餐饮服务)，详见高德POI分类编码表
        radius: 查询半径，单位:米，取值范围:0-50000
        page: 当前页数，默认为1
        offset: 每页记录数，默认为20，强烈建议不超过25
        
    Returns:
        附近POI信息的JSON字符串
    """
    # 构建参数
    params = {
        'key': config['api']['gaode_key'],
        'location': location,
        'radius': radius,
        'page': page,
        'offset': offset,
        'extensions': 'all',
        'sortrule': 'distance'  # 按距离排序
    }
    
    # 添加可选参数
    if keywords:
        params['keywords'] = keywords
    
    if poi_type:
        params['types'] = poi_type
    
    # 构建URL
    base_url = "https://restapi.amap.com/v3/place/around"
    
    # 发送请求
    async with httpx.AsyncClient() as client:
        response = await client.get(url=base_url, params=params)
        
        # 检查请求是否成功
        if response.status_code == 200:
            result = response.json()
            
            # 检查API返回的状态
            if result.get('status') == '1':
                # 格式化结果
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

@app.tool()
async def geocode_address(address: str, city: str = "") -> str:
    """
    使用高德地图API将地址转换为坐标
    
    Args:
        address: 地址，如"北京市朝阳区阜通东大街6号"
        city: 指定查询的城市，可选值：城市中文、中文全拼、citycode、adcode
        
    Returns:
        地理编码结果的JSON字符串
    """
    # 构建参数
    params = {
        'key': config['api']['gaode_key'],
        'address': address,
    }
    
    # 添加可选参数
    if city:
        params['city'] = city
    
    # 构建URL
    base_url = "https://restapi.amap.com/v3/geocode/geo"
    
    # 发送请求
    async with httpx.AsyncClient() as client:
        response = await client.get(url=base_url, params=params)
        
        # 检查请求是否成功
        if response.status_code == 200:
            result = response.json()
            
            # 检查API返回的状态
            if result.get('status') == '1' and result.get('geocodes', []):
                first_result = result['geocodes'][0]
                
                # 格式化结果
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

@app.tool()
async def calculate_route_distance(origin: str, destination: str, mode: str = "driving") -> str:
    """
    使用高德地图API计算两地之间的路线距离
    
    Args:
        origin: 起点坐标，格式为"经度,纬度"，如"116.481028,39.989643"
        destination: 终点坐标，格式为"经度,纬度"，如"116.434446,39.90816"
        mode: 计算路径的模式，可选 "driving"(驾车), "walking"(步行), "bicycling"(骑行), "transit"(公交)
        
    Returns:
        路线距离计算结果的JSON字符串
    """
    # 检查mode参数是否有效
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
    
    # 构建URL和参数
    if mode == "driving":
        base_url = "https://restapi.amap.com/v3/direction/driving"
    elif mode == "walking":
        base_url = "https://restapi.amap.com/v3/direction/walking"
    elif mode == "bicycling":
        base_url = "https://restapi.amap.com/v4/direction/bicycling"
    elif mode == "transit":
        base_url = "https://restapi.amap.com/v3/direction/transit/integrated"
    
    # 构建参数
    params = {
        'key': config['api']['gaode_key'],
        'origin': origin,
        'destination': destination,
        'extensions': 'base'
    }
    
    # 发送请求
    async with httpx.AsyncClient() as client:
        response = await client.get(url=base_url, params=params)
        
        # 检查请求是否成功
        if response.status_code == 200:
            result = response.json()
            
            # 检查API返回的状态
            if result.get('status') == '1':
                # 解析返回结果，不同模式返回的结构可能不同
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
                            "distance": first_path.get('distance', '0'),  # 单位:米
                            "duration": first_path.get('duration', '0'),  # 单位:秒
                            "tolls": first_path.get('tolls', '0'),  # 单位:元
                            "toll_distance": first_path.get('toll_distance', '0')  # 单位:米
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
                            "distance": first_path.get('distance', '0'),  # 单位:米
                            "duration": first_path.get('duration', '0')  # 单位:秒
                        }
                        return json.dumps(formatted_result, ensure_ascii=False, indent=2)
                elif mode == "transit":
                    route = result.get('route', {})
                    formatted_result = {
                        "status": "success",
                        "mode": mode,
                        "origin": origin,
                        "destination": destination,
                        "distance": route.get('distance', '0'),  # 单位:米
                        "taxi_cost": route.get('taxi_cost', '0'),  # 单位:元
                        "transits": route.get('transits', [])
                    }
                    return json.dumps(formatted_result, ensure_ascii=False, indent=2)
            
            # 如果没有获取到有效的路径信息
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

@app.tool()
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

if __name__ == "__main__":
    app.run(transport='stdio')
