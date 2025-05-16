from fastapi import FastAPI, Request, Depends, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import asyncio
import json
import logging
import uuid
from contextlib import asynccontextmanager
from typing import Dict, List, Optional, Any, AsyncGenerator

# 导入核心功能
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
logger = logging.getLogger('sse_mcp.server')

# 存储SSE连接的客户端
clients: Dict[str, Dict[str, Any]] = {}

# 基本的MCP消息格式
def format_mcp_message(type_str: str, data: Any, event_id: Optional[str] = None) -> str:
    """
    格式化MCP消息为SSE格式
    
    Args:
        type_str: 消息类型
        data: 消息内容
        event_id: 事件ID (可选)
        
    Returns:
        格式化的SSE消息字符串
    """
    msg_id = event_id or str(uuid.uuid4())
    # 为SSE格式化消息
    message = f"id: {msg_id}\n"
    message += f"event: {type_str}\n"
    message += f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
    return message


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用程序生命周期管理
    """
    # 启动时的操作
    logger.info("正在初始化 SSE MCP 服务...")
    
    # 加载配置
    config = load_config()
    app.state.gaode_api_key = get_api_key(config, 'gaode')
    
    if app.state.gaode_api_key:
        logger.info("高德地图API密钥已加载")
    else:
        logger.warning("未找到高德API密钥，高德地图相关功能将不可用")
    
    yield
    
    # 关闭时的操作
    logger.info("正在关闭 SSE MCP 服务...")
    
    # 关闭所有SSE连接
    for client_id, client_info in list(clients.items()):
        logger.info(f"关闭客户端连接: {client_id}")
    
    clients.clear()


app = FastAPI(title="GeoMCP SSE Server", lifespan=lifespan)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境应该更具体
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def sse_generator(client_id: str) -> AsyncGenerator[str, None]:
    """
    SSE事件流生成器
    """
    # 发送连接成功消息
    yield format_mcp_message("connection", {"status": "connected", "client_id": client_id})
    
    # 保持连接
    while True:
        # 检查客户端是否已断开
        if client_id not in clients:
            logger.info(f"客户端已断开: {client_id}")
            break
        
        # 检查是否有待发送的消息
        client_info = clients[client_id]
        messages_queue = client_info.get("queue", [])
        
        if messages_queue:
            message = messages_queue.pop(0)
            yield message
        
        # 每5秒发送一次心跳消息
        if not messages_queue:
            yield format_mcp_message("heartbeat", {"timestamp": asyncio.get_event_loop().time()})
            await asyncio.sleep(5)


@app.get("/")
async def root():
    """
    服务根路由
    """
    return {
        "service": "GeoMCP SSE Server",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "sse": "/sse",
            "mcp_call": "/mcp_call"
        }
    }


@app.get("/sse")
async def sse_endpoint(request: Request) -> StreamingResponse:
    """
    SSE连接端点
    """
    client_id = str(uuid.uuid4())
    logger.info(f"新的SSE连接: {client_id}")
    
    clients[client_id] = {
        "connected_at": asyncio.get_event_loop().time(),
        "queue": []
    }
    
    return StreamingResponse(
        sse_generator(client_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.post("/mcp_call")
async def mcp_call(request: Request):
    """
    MCP调用端点
    """
    try:
        data = await request.json()
        function_name = data.get("function")
        params = data.get("params", {})
        client_id = data.get("client_id")
        
        if not function_name:
            raise HTTPException(status_code=400, detail="Missing function name")
        
        # 验证客户端ID
        if client_id and client_id not in clients:
            raise HTTPException(status_code=404, detail=f"Client ID not found: {client_id}")
        
        # 执行相应的MCP函数
        result = await execute_mcp_function(function_name, params)
        
        # 如果有客户端ID，则通过SSE发送结果
        if client_id:
            clients[client_id]["queue"].append(
                format_mcp_message("result", {
                    "function": function_name,
                    "result": result
                })
            )
            return {"status": "success", "message": "Result queued for SSE delivery"}
        else:
            # 否则直接返回结果
            return {"status": "success", "result": result}
    
    except Exception as e:
        logger.error(f"MCP调用错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def execute_mcp_function(function_name: str, params: Dict[str, Any]) -> Any:
    """
    执行MCP函数
    
    Args:
        function_name: 函数名
        params: 函数参数
        
    Returns:
        函数执行结果
    """
    logger.info(f"执行函数: {function_name}, 参数: {params}")
    
    try:
        # 地理空间分析函数
        if function_name == "calculate_geodesic_distance":
            # 同步函数，无需 await
            return calculate_geodesic_distance(params.get("coordinates_json", ""))
        
        elif function_name == "read_table_file":
            # 同步函数，无需 await
            return read_table_file(
                params.get("file_path", ""),
                params.get("nrows", 5)
            )
        
        elif function_name == "analyze_distance_distribution":
            # 同步函数，无需 await
            return analyze_distance_distribution(
                params.get("file_path", ""),
                params.get("distance_col", "distance")
            )
        
        elif function_name == "hotspot_analysis_getis_ord_gi_star":
            # 同步函数，无需 await
            return hotspot_analysis_getis_ord_gi_star(
                params.get("file_path", ""),
                params.get("lat_col", ""),
                params.get("lon_col", ""),
                params.get("value_col", ""),
                params.get("distance_threshold", 1000.0)
            )
        
        # 高德地图API函数（这些可能是真正的异步函数，保留 await）
        elif function_name == "search_nearby_poi":
            return await search_nearby_poi(
                app.state.gaode_api_key,
                params.get("location", ""),
                params.get("keywords", ""),
                params.get("poi_type", ""),
                params.get("radius", 5000),
                params.get("page", 1),
                params.get("offset", 20)
            )
        
        elif function_name == "geocode_address":
            return await geocode_address(
                app.state.gaode_api_key,
                params.get("address", ""),
                params.get("city", "")
            )
        
        elif function_name == "calculate_route_distance":
            return await calculate_route_distance(
                app.state.gaode_api_key,
                params.get("origin", ""),
                params.get("destination", ""),
                params.get("mode", "driving")
            )
        
        else:
            raise ValueError(f"未知的函数: {function_name}")
            
    except Exception as e:
        logger.error(f"函数执行错误 {function_name}: {str(e)}", exc_info=True)
        return json.dumps({
            "status": "failure",
            "info": f"函数执行错误: {str(e)}",
            "function": function_name
        }, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "sse_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 