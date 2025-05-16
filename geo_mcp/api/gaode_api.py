import json
import httpx
from typing import Dict, Optional, Any


async def search_nearby_poi(api_key: str,
                            location: str, 
                            keywords: str = "", 
                            poi_type: str = "", 
                            radius: int = 5000, 
                            page: int = 1, 
                            offset: int = 20) -> str:
    """
    使用高德地图API搜索周边POI
    
    Args:
        api_key: 高德地图API密钥
        location: 中心点坐标(经度,纬度)，如"116.473168,39.993015"
        keywords: 查询关键字，如"餐馆"、"学校"等
        poi_type: POI类型代码，如"050000"(餐饮服务)，详见高德POI分类编码表
        radius: 查询半径，单位:米，取值范围:0-50000
        page: 当前页数，默认为1
        offset: 每页记录数，默认为20，强烈建议不超过25
        
    Returns:
        附近POI信息的JSON字符串
    """
    params = {
        'key': api_key,
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


async def geocode_address(api_key: str, address: str, city: str = "") -> str:
    """
    使用高德地图API将地址转换为坐标
    
    Args:
        api_key: 高德地图API密钥
        address: 地址，如"北京市朝阳区阜通东大街6号"
        city: 指定查询的城市，可选值：城市中文、中文全拼、citycode、adcode
        
    Returns:
        地理编码结果的JSON字符串
    """
    params = {
        'key': api_key,
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


async def calculate_route_distance(api_key: str, 
                                  origin: str, 
                                  destination: str, 
                                  mode: str = "driving") -> str:
    """
    使用高德地图API计算两地之间的路线距离
    
    Args:
        api_key: 高德地图API密钥
        origin: 起点坐标，格式为"经度,纬度"，如"116.481028,39.989643"
        destination: 终点坐标，格式为"经度,纬度"，如"116.434446,39.90816"
        mode: 计算路径的模式，可选 "driving"(驾车), "walking"(步行), "bicycling"(骑行), "transit"(公交)
        
    Returns:
        路线距离计算结果的JSON字符串
    """
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
    
    # 定义base_url变量
    base_url = ""
    
    # 根据模式选择不同的API端点
    if mode == "driving":
        base_url = "https://restapi.amap.com/v3/direction/driving"
    elif mode == "walking":
        base_url = "https://restapi.amap.com/v3/direction/walking"
    elif mode == "bicycling":
        base_url = "https://restapi.amap.com/v4/direction/bicycling"
    elif mode == "transit":
        base_url = "https://restapi.amap.com/v3/direction/transit/integrated"
    
    params = {
        'key': api_key,
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