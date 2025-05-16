import json
from typing import Dict, List, Tuple, Union, Any
from geopy.distance import geodesic


def calculate_geodesic_distance(coordinates_json: str) -> str:
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