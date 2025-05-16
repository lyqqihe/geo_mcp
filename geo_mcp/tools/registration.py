from mcp.server.fastmcp import FastMCP
from typing import Dict, Any, Callable, List, Optional
import logging
import inspect
import importlib


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('geo_mcp.tools')


class GeoMCPServer:
    """
    地理空间数据分析MCP服务器管理类
    """
    
    def __init__(self, server_name: str = "GeoSpatialAnalysisServer"):
        """
        初始化MCP服务器
        
        Args:
            server_name: 服务器名称
        """
        self.server_name = server_name
        self.mcp = FastMCP(server_name)
        self.registered_tools: Dict[str, Dict[str, Any]] = {}
        
    def register_tool(self, func: Callable) -> Callable:
        """
        注册工具函数
        
        Args:
            func: 要注册的函数
            
        Returns:
            注册后的函数
        """
        try:
            # 获取函数信息
            func_name = func.__name__
            func_doc = func.__doc__ or ""
            func_sig = inspect.signature(func)
            
            # 注册到MCP
            self.mcp.tool()(func)
            
            # 记录已注册的工具
            self.registered_tools[func_name] = {
                "name": func_name,
                "doc": func_doc,
                "signature": str(func_sig),
                "module": func.__module__
            }
            
            logger.info(f"工具注册成功: {func_name}")
            return func
        except Exception as e:
            logger.error(f"工具注册失败 {func.__name__}: {str(e)}")
            return func
            
    def auto_register_from_module(self, module_path: str) -> List[str]:
        """
        从模块自动注册所有工具函数
        
        Args:
            module_path: 模块路径，例如 "geo_mcp.core.geo_distance"
            
        Returns:
            已注册工具的名称列表
        """
        try:
            module = importlib.import_module(module_path)
            registered = []
            
            for name, obj in inspect.getmembers(module):
                # 只注册公共函数，跳过私有函数和内置函数
                if (inspect.isfunction(obj) and 
                    not name.startswith('_') and 
                    obj.__module__ == module_path):
                    self.register_tool(obj)
                    registered.append(name)
                    
            return registered
        except Exception as e:
            logger.error(f"从模块自动注册工具失败 {module_path}: {str(e)}")
            return []
            
    def get_registered_tools(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有已注册的工具信息
        
        Returns:
            已注册工具的信息字典
        """
        return self.registered_tools
        
    def run(self, transport: str = 'stdio') -> None:
        """
        运行MCP服务器
        
        Args:
            transport: 传输方式，默认为'stdio'
        """
        try:
            logger.info(f"正在启动 {self.server_name} MCP服务器")
            logger.info(f"已注册 {len(self.registered_tools)} 个工具")
            self.mcp.run(transport=transport)
        except Exception as e:
            logger.error(f"MCP服务器运行失败: {str(e)}")
            
    def shutdown(self) -> None:
        """
        关闭MCP服务器
        """
        try:
            # MCP服务器关闭相关操作
            logger.info(f"正在关闭 {self.server_name} MCP服务器")
        except Exception as e:
            logger.error(f"MCP服务器关闭失败: {str(e)}")
            
    def __str__(self) -> str:
        return f"GeoMCPServer(name={self.server_name}, tools={len(self.registered_tools)})" 