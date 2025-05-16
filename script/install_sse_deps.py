#!/usr/bin/env python
"""
安装SSE MCP所需的依赖
===================

此脚本将安装运行SSE版GeoMCP所需的全部依赖。
"""

import subprocess
import sys
import os
import platform


def print_step(message):
    """打印步骤信息"""
    print("\n" + "=" * 60)
    print(f"  {message}")
    print("=" * 60)


def run_command(command):
    """运行shell命令"""
    print(f"执行: {' '.join(command)}")
    try:
        subprocess.run(command, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {e}")
        return False


def install_package(package_name):
    """安装Python包"""
    print(f"正在安装 {package_name}...")
    return run_command([sys.executable, "-m", "pip", "install", package_name])


def check_pip():
    """检查pip是否可用"""
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], check=True, stdout=subprocess.PIPE)
        return True
    except:
        print("未找到pip。请先安装pip: https://pip.pypa.io/en/stable/installation/")
        return False


def main():
    """主函数"""
    print_step("开始安装SSE MCP依赖")
    
    # 检查pip
    if not check_pip():
        sys.exit(1)
    
    print_step("安装FastAPI和Uvicorn")
    if not install_package("fastapi") or not install_package("uvicorn[standard]"):
        print("FastAPI或Uvicorn安装失败")
        sys.exit(1)
    
    print_step("安装SSE客户端依赖")
    if not install_package("requests") or not install_package("sseclient-py"):
        print("SSE客户端依赖安装失败")
        sys.exit(1)
    
    print_step("安装其他依赖")
    if not install_package("geopy") or not install_package("httpx"):
        print("地理空间依赖安装失败")
        sys.exit(1)
    
    if not install_package("pandas") or not install_package("numpy") or not install_package("scipy"):
        print("数据处理依赖安装失败")
        sys.exit(1)
    
    if not install_package("scikit-learn") or not install_package("pyyaml"):
        print("分析依赖安装失败")
        sys.exit(1)
    
    print_step("安装当前项目包")
    if os.path.exists("pyproject.toml"):
        if not run_command([sys.executable, "-m", "pip", "install", "-e", "."]):
            print("项目安装失败")
            sys.exit(1)
    
    print_step("安装完成!")
    print("\n所有依赖已成功安装。现在可以运行SSE MCP服务器了:")
    print("  python sse_server.py")
    print("\n或使用客户端进行测试:")
    print("  python sse_client_demo.py")


if __name__ == "__main__":
    main() 