import json
import os
import pandas as pd
import numpy as np
from typing import Dict, Optional, Any


def read_table_file(file_path: str, nrows: int = 5) -> str:
    """
    读取CSV或Excel文件的前几行数据，用户只需输入文件路径。
    
    Args:
        file_path: 文件路径，支持csv、xls、xlsx
        nrows: 返回前几行，默认5行
        
    Returns:
        包含字段名和前几行数据的JSON字符串
    """
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


def analyze_distance_distribution(file_path: str, distance_col: str = "distance") -> str:
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