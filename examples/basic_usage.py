#!/usr/bin/env python3
"""
GeoMCP基本使用示例
"""
import asyncio
import json
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from geo_mcp.core.geo_distance import calculate_geodesic_distance
from geo_mcp.core.data_processing import read_table_file, analyze_distance_distribution
from geo_mcp.core.spatial_analysis import hotspot_analysis_getis_ord_gi_star


async def demo_distance_calculation():
    """测地线距离计算示例"""
    print("\n=== 测地线距离计算示例 ===")
    
    # 使用简化格式
    simple_coords = "39.90923_116.397428,31.23039_121.473702"
    print(f"计算北京-上海距离（简化格式）: {simple_coords}")
    result = calculate_geodesic_distance(simple_coords)
    print(json.dumps(json.loads(result), indent=2, ensure_ascii=False))
    
    # 使用JSON格式
    json_coords = json.dumps({
        "point1": [39.90923, 116.397428],
        "point2": [31.23039, 121.473702]
    })
    print(f"\n计算北京-上海距离（JSON格式）: {json_coords}")
    result = calculate_geodesic_distance(json_coords)
    print(json.dumps(json.loads(result), indent=2, ensure_ascii=False))


async def demo_file_operations():
    """文件操作示例"""
    print("\n=== 文件操作示例 ===")
    
    # 读取文件示例
    file_path = os.path.join("geo_mcp", "data", "geo_hotspot_data.csv")
    if os.path.exists(file_path):
        print(f"读取文件: {file_path}")
        result = read_table_file(file_path, nrows=3)
        print(json.dumps(json.loads(result), indent=2, ensure_ascii=False))
    else:
        print(f"文件不存在: {file_path}")


async def demo_hotspot_analysis():
    """热点分析示例"""
    print("\n=== 热点分析示例 ===")
    
    # 热点分析示例
    file_path = os.path.join("geo_mcp", "data", "geo_hotspot_data.csv")
    if os.path.exists(file_path):
        print(f"对文件进行热点分析: {file_path}")
        result = hotspot_analysis_getis_ord_gi_star(
            file_path, 
            lat_col="latitude", 
            lon_col="longitude", 
            value_col="value", 
            distance_threshold=1000
        )
        result_json = json.loads(result)
        # 仅打印前3个结果和摘要信息，避免输出过多
        if result_json["status"] == "success":
            summary = {
                "status": result_json["status"],
                "count": result_json["count"],
                "distance_threshold": result_json["distance_threshold"],
                "results": result_json["results"][:3],
                "result_count": len(result_json["results"]),
                "note": "仅显示前3个结果..."
            }
            print(json.dumps(summary, indent=2, ensure_ascii=False))
        else:
            print(result)
    else:
        print(f"文件不存在: {file_path}")


async def main():
    """主函数"""
    print("GeoMCP 基本功能演示")
    
    # 运行演示
    await demo_distance_calculation()
    await demo_file_operations()
    await demo_hotspot_analysis()


if __name__ == "__main__":
    # 确保示例目录存在
    os.makedirs("examples", exist_ok=True)
    # 运行主函数
    asyncio.run(main()) 