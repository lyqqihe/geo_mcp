import json
import os
import pandas as pd
import numpy as np
from scipy.stats import norm
from sklearn.metrics.pairwise import haversine_distances
from typing import Dict, List, Optional, Any, Union


def hotspot_analysis_getis_ord_gi_star(file_path: str, 
                                       lat_col: str, 
                                       lon_col: str, 
                                       value_col: str, 
                                       distance_threshold: float = 1000.0) -> str:
    """
    基于Getis-Ord Gi*的热点分析。
    
    Args:
        file_path: 数据文件路径（csv/xls/xlsx）
        lat_col: 纬度字段名
        lon_col: 经度字段名
        value_col: 参与分析的数值字段名
        distance_threshold: 邻域距离（米），可选范围如1000、5000、10000等，默认1000米。
                            越大则邻域更广，热点更易聚集。
                            
    Returns:
        JSON字符串，包含每个点的Gi*、Z分数、p值、热点/冷点标签等，并显示实际使用的邻域距离
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

        # 检查字段
        for col in [lat_col, lon_col, value_col]:
            if col not in df.columns:
                return json.dumps({
                    "status": "failure",
                    "info": f"缺少字段: {col}"
                }, ensure_ascii=False, indent=2)

        coords = df[[lat_col, lon_col]].values
        values = df[value_col].values.astype(float)
        n = len(df)
        
        # 经纬度转弧度
        coords_rad = np.radians(coords)
        # 计算球面距离（单位：米）
        dists = haversine_distances(coords_rad, coords_rad) * 6371000  # 地球半径
        
        # 权重矩阵
        if distance_threshold is None and "distance" in df.columns:
            distance_arr = df["distance"].values.astype(float)
            wij = np.zeros((n, n), dtype=int)
            for i in range(n):
                wij[i] = (dists[i] <= distance_arr[i]).astype(int)
            used_distance = "variable (from data)"
        else:
            if distance_threshold is None:
                distance_threshold = 1000.0  # 默认值
            wij = (dists <= distance_threshold).astype(int)
            used_distance = float(distance_threshold)
        
        np.fill_diagonal(wij, 0)
        
        # 计算Gi*
        sum_wij = wij.sum(axis=1)
        xj = values
        xj_sum = np.sum(xj)
        xj2_sum = np.sum(xj ** 2)
        mean_x = xj_sum / n
        s = np.sqrt((xj2_sum / n) - mean_x ** 2)
        
        results = []
        for i in range(n):
            wij_i = wij[i]
            sum_wij_i = sum_wij[i]
            num = np.sum(wij_i * xj)
            denom = s * np.sqrt((n * np.sum(wij_i ** 2) - sum_wij_i ** 2) / (n - 1))
            
            if denom == 0:
                gi_star = 0
                z_score = 0
                p_value = 1
            else:
                gi_star = (num - mean_x * sum_wij_i) / denom
                z_score = gi_star
                p_value = 2 * (1 - norm.cdf(abs(z_score)))
            
            # 使用更严格的显著性水平
            if z_score > 2.58:  # 99% 置信水平
                label = "hotspot"
            elif z_score < -2.58:
                label = "coldspot"
            else:
                label = "not significant"
                
            results.append({
                "index": int(i),
                "latitude": float(coords[i][0]),
                "longitude": float(coords[i][1]),
                "value": float(xj[i]),
                "gi_star": float(gi_star),
                "z_score": float(z_score),
                "p_value": float(p_value),
                "label": label,
                "neighbors": int(sum_wij_i)  # 添加邻域点数量
            })
            
        return json.dumps({
            "status": "success",
            "count": n,
            "distance_threshold": used_distance,
            "results": results
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "failure",
            "info": f"热点分析出错: {str(e)}"
        }, ensure_ascii=False, indent=2) 