"""
JSON Serialization Utilities
Provides unified functions for cleaning and preparing data for JSON serialization
Handles numpy/pandas types and special float values (NaN, Infinity)
"""

import math
import numpy as np
import pandas as pd
from typing import Any


def clean_for_json(data: Any) -> Any:
    """
    Clean data for JSON serialization by converting numpy/pandas types to Python types
    
    Args:
        data: Data to clean (can be dict, list, numpy types, pandas types, etc.)
        
    Returns:
        Cleaned data with Python native types
    """
    if isinstance(data, dict):
        return {key: clean_for_json(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [clean_for_json(item) for item in data]
    elif isinstance(data, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(data)
    elif isinstance(data, (np.floating, np.float64, np.float32, np.float16)):
        return float(data)
    elif isinstance(data, np.ndarray):
        return data.tolist()
    elif pd.isna(data):
        return None
    else:
        return data


def clean_json_floats(obj: Any) -> Any:
    """
    Recursively clean NaN and Infinity values from nested dictionaries/lists
    for JSON serialization
    
    Args:
        obj: Object to clean (can be dict, list, float, etc.)
        
    Returns:
        Cleaned object with NaN/Infinity replaced by None
    """
    if isinstance(obj, dict):
        return {k: clean_json_floats(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_json_floats(item) for item in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    else:
        return obj
