# GeoMCP SSE版 - 基于SSE的地理空间MCP服务

这是GeoMCP的SSE（Server-Sent Events）版本，使用FastAPI实现，可与大语言模型（如ChatGPT、Claude）无缝集成，支持实时地理空间数据分析。

## 功能特点

- **基于SSE的实时通信**：使用Server-Sent Events实现服务器到客户端的实时推送
- **完整的FastAPI后端**：高性能、易用的API服务器
- **丰富的用户界面**：包含完整的Web客户端界面
- **异步执行**：所有操作都是异步执行的，保证高并发性能
- **无需第三方MCP库**：不再依赖MCP库，只需FastAPI即可构建MCP应用
- **集成Context7**：基于Context7的文档，遵循规范构建
- **保留所有原始功能**：保留了原GeoMCP的所有核心功能

## 安装和依赖

### 依赖环境

- Python 3.8+
- FastAPI
- Uvicorn
- 以及原GeoMCP的所有依赖

### 安装步骤

```bash
# 安装FastAPI和Uvicorn
pip install fastapi uvicorn

# 安装其他依赖
pip install -e .
```

## 运行服务器

### 方法1：直接运行Python脚本

```bash
python sse_server.py
```

### 方法2：通过Uvicorn运行

```bash
uvicorn sse_server:app --reload --host 0.0.0.0 --port 8000
```

## 使用Web客户端

1. 启动SSE MCP服务器
2. 在浏览器中打开`sse_client.html`文件
3. 点击"连接服务器"按钮建立SSE连接
4. 使用各种地理空间功能

## 与大语言模型集成

### 通用API设计

SSE MCP服务器提供了两个主要端点：

- `/sse`：建立SSE连接
- `/mcp_call`：调用MCP函数

### 示例调用流程

1. 通过`/sse`端点建立SSE连接并获取`client_id`
2. 使用`/mcp_call`端点调用函数，并通过SSE接收结果

### Python调用示例

```python
import requests
import sseclient
import json
import threading
import asyncio

base_url = "http://localhost:8000"

# 建立SSE连接的函数
def listen_sse():
    sse_url = f"{base_url}/sse"
    headers = {'Accept': 'text/event-stream'}
    
    response = requests.get(sse_url, headers=headers, stream=True)
    client = sseclient.SSEClient(response)
    
    for event in client.events():
        print(f"事件: {event.event}")
        print(f"数据: {event.data}")
        
        # 如果是连接事件，则保存client_id
        if event.event == 'connection':
            data = json.loads(event.data)
            client_id = data.get('client_id')
            print(f"已获取客户端ID: {client_id}")
            
            # 调用MCP函数示例
            call_mcp_function(client_id, 'calculate_geodesic_distance', {
                'coordinates_json': '39.90923_116.397428,31.23039_121.473702'
            })

# 调用MCP函数
def call_mcp_function(client_id, function_name, params):
    url = f"{base_url}/mcp_call"
    data = {
        'function': function_name,
        'params': params,
        'client_id': client_id
    }
    
    response = requests.post(url, json=data)
    print(f"调用结果: {response.json()}")

# 启动一个线程监听SSE事件
thread = threading.Thread(target=listen_sse)
thread.daemon = True
thread.start()

# 保持主线程运行
try:
    while True:
        pass
except KeyboardInterrupt:
    print("程序已终止")
```

### JavaScript调用示例

```javascript
// 建立SSE连接
const eventSource = new EventSource('http://localhost:8000/sse');
let clientId = null;

// 处理连接事件
eventSource.addEventListener('connection', function(event) {
    const data = JSON.parse(event.data);
    clientId = data.client_id;
    console.log('已连接到服务器，客户端ID:', clientId);
    
    // 连接成功后调用函数示例
    callMcpFunction('calculate_geodesic_distance', {
        coordinates_json: '39.90923_116.397428,31.23039_121.473702'
    });
});

// 处理结果事件
eventSource.addEventListener('result', function(event) {
    const data = JSON.parse(event.data);
    console.log('收到结果:', data);
});

// 调用MCP函数
async function callMcpFunction(functionName, params) {
    const response = await fetch('http://localhost:8000/mcp_call', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            function: functionName,
            params: params,
            client_id: clientId
        })
    });
    
    const result = await response.json();
    console.log('调用响应:', result);
}
```

## API参考

### SSE事件类型

- `connection`：连接建立事件
- `heartbeat`：心跳事件（每5秒发送一次）
- `result`：函数调用结果事件

### MCP函数列表

#### 地理空间分析函数

- `calculate_geodesic_distance`：计算两点间的测地线距离
- `read_table_file`：读取并预览数据文件
- `analyze_distance_distribution`：分析距离分布
- `hotspot_analysis_getis_ord_gi_star`：执行热点分析

#### 高德地图API函数

- `search_nearby_poi`：搜索周边POI
- `geocode_address`：地址地理编码
- `calculate_route_distance`：计算路线距离

## 许可证

与原GeoMCP相同，采用MIT许可证。 