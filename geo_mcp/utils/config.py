import os
import yaml
import logging
from typing import Dict, Any, Optional


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('geo_mcp.config')


def load_config(config_path: str = 'config.yaml') -> Dict[str, Any]:
    """
    加载配置文件
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        包含配置信息的字典
    """
    try:
        if not os.path.exists(config_path):
            logger.warning(f"配置文件不存在: {config_path}")
            return _get_default_config()
            
        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
            
        if config is None:
            logger.warning(f"配置文件为空: {config_path}")
            return _get_default_config()
            
        return config
    except Exception as e:
        logger.error(f"加载配置文件时出错: {str(e)}")
        return _get_default_config()


def _get_default_config() -> Dict[str, Any]:
    """
    获取默认配置
    
    Returns:
        默认配置字典
    """
    return {
        "api": {
            "gaode_key": "",
            "base_url": "",
            "model": "default"
        },
        "spatial": {
            "default_crs": "EPSG:4326",
            "distance_unit": "km"
        },
        "debug": {
            "enabled": False,
            "log_level": "info"
        }
    }


def get_api_key(config: Dict[str, Any], api_name: str) -> Optional[str]:
    """
    从配置中获取API密钥
    
    Args:
        config: 配置字典
        api_name: API名称
        
    Returns:
        API密钥，如果不存在则返回None
    """
    try:
        if 'api' not in config:
            return None
            
        key_name = f"{api_name}_key"
        if key_name in config['api']:
            return config['api'][key_name]
            
        return None
    except Exception:
        return None


def set_config_value(config: Dict[str, Any], key_path: str, value: Any) -> Dict[str, Any]:
    """
    设置配置值
    
    Args:
        config: 配置字典
        key_path: 键路径，格式如 "api.gaode_key"
        value: 要设置的值
        
    Returns:
        更新后的配置字典
    """
    if not key_path:
        return config
        
    keys = key_path.split('.')
    current = config
    
    # 遍历路径中的所有键，除了最后一个
    for i, key in enumerate(keys[:-1]):
        if key not in current:
            current[key] = {}
        current = current[key]
    
    # 设置最后一个键的值
    current[keys[-1]] = value
    
    return config


def save_config(config: Dict[str, Any], config_path: str = 'config.yaml') -> bool:
    """
    保存配置到文件
    
    Args:
        config: 配置字典
        config_path: 配置文件路径
        
    Returns:
        是否保存成功
    """
    try:
        with open(config_path, 'w', encoding='utf-8') as file:
            yaml.dump(config, file, allow_unicode=True, default_flow_style=False)
        return True
    except Exception as e:
        logger.error(f"保存配置文件时出错: {str(e)}")
        return False 