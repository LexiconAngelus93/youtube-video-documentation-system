#!/usr/bin/env python3
"""
Configuration Utilities Module

This module provides simple utility functions for configuration management.
"""

import yaml
from pathlib import Path
from typing import Any, Dict

CONFIG_PATH = Path("config.yaml")

def load_config() -> Dict[str, Any]:
    """
    Load configuration from file.
    
    Returns:
        Configuration dictionary or empty dict if file doesn't exist
    """
    if CONFIG_PATH.exists():
        return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    return {}

def save_config(config: Dict[str, Any]) -> None:
    """
    Save configuration to file.
    
    Args:
        config: Configuration dictionary to save
    """
    CONFIG_PATH.write_text(
        yaml.dump(config, default_flow_style=False, sort_keys=False),
        encoding="utf-8"
    )

def get_nested(config: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    Get a nested configuration value using dot notation.
    
    Args:
        config: Configuration dictionary
        key: Configuration key (supports dot notation like "database.host")
        default: Default value if key not found
        
    Returns:
        Configuration value or default
    """
    for part in key.split("."):
        if not isinstance(config, dict) or part not in config:
            return default
        config = config[part]
    return config

def set_nested(config: Dict[str, Any], key: str, value: Any) -> None:
    """
    Set a nested configuration value using dot notation.
    
    Args:
        config: Configuration dictionary
        key: Configuration key (supports dot notation like "database.host")
        value: Value to set
    """
    parts = key.split(".")
    cur = config
    for part in parts[:-1]:
        cur = cur.setdefault(part, {})
    cur[parts[-1]] = value
