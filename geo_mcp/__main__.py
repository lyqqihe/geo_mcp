import os
import sys
import logging
from geo_mcp.tools.registration import GeoMCPServer
from geo_mcp.core.geo_distance import calculate_geodesic_distance
from geo_mcp.core.data_processing import read_table_file, analyze_distance_distribution
from geo_mcp.core.spatial_analysis import hotspot_analysis_getis_ord_gi_star
from geo_mcp.utils.config import load_config, get_api_key
from geo_mcp.api.gaode_api import search_nearby_poi, geocode_address, calculate_route_distance


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('geo_mcp.main')


def create_mcp_server() -> GeoMCPServer:
    """
    创建并配置MCP服务器
    
    Returns:
        配置好的GeoMCPServer实例
    """
    # 创建服务器实例
    server = GeoMCPServer("GeoSpatialAnalysisServer")
    
    # 注册核心工具函数
    server.register_tool(calculate_geodesic_distance)
    server.register_tool(read_table_file)
    server.register_tool(analyze_distance_distribution)
    server.register_tool(hotspot_analysis_getis_ord_gi_star)
    
    # 加载配置
    config = load_config()
    gaode_api_key = get_api_key(config, 'gaode')
    
    # 如果有高德API密钥，创建和注册高德API相关工具
    if gaode_api_key:
        async def search_nearby_poi_wrapper(location, keywords="", poi_type="", radius=5000, page=1, offset=20):
            """使用高德地图API搜索周边POI"""
            return await search_nearby_poi(gaode_api_key, location, keywords, poi_type, radius, page, offset)
            
        async def geocode_address_wrapper(address, city=""):
            """使用高德地图API将地址转换为坐标"""
            return await geocode_address(gaode_api_key, address, city)
            
        async def calculate_route_distance_wrapper(origin, destination, mode="driving"):
            """使用高德地图API计算两地之间的路线距离"""
            return await calculate_route_distance(gaode_api_key, origin, destination, mode)
            
        # 注册高德API工具
        server.register_tool(search_nearby_poi_wrapper)
        server.register_tool(geocode_address_wrapper)
        server.register_tool(calculate_route_distance_wrapper)
    else:
        logger.warning("未找到高德API密钥，高德地图相关功能将不可用")
    
    return server


def main():
    """
    主程序入口
    """
    try:
        logger.info("正在初始化 GeoMCP 服务...")
        server = create_mcp_server()
        logger.info(f"已创建 MCP 服务器: {server}")
        
        # 注册工具数量提示
        tool_count = len(server.get_registered_tools())
        logger.info(f"共注册了 {tool_count} 个工具")
        
        # 运行服务器
        logger.info("正在启动 MCP 服务...")
        server.run()
    except KeyboardInterrupt:
        logger.info("接收到中断信号，正在关闭服务...")
    except Exception as e:
        logger.error(f"服务运行时错误: {str(e)}", exc_info=True)
    finally:
        logger.info("GeoMCP 服务已关闭")
        

if __name__ == "__main__":
    main() 