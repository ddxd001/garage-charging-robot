#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路径规划模块

本模块负责生成机器人的参考路径，支持多种路径类型：
- 直线路径：从起点到终点的直线
- 圆形路径：圆周运动轨迹
- L形路径：模拟车库场景的L形轨迹

路径表示：
    - 使用离散点序列表示路径
    - 点间距可配置，影响路径精度
    - 所有路径都是二维平面路径(x, y)

作者：车库机器人团队
版本：1.3.0
日期：2026-03
"""

import numpy as np
from typing import Optional


class PathPlanner:
    """
    Path planner for generating reference trajectories.
    
    Supports multiple path types suitable for garage charging scenarios:
    - Straight line paths
    - Circular paths
    - L-shaped paths (straight + turn + straight)
    """
    
    @staticmethod
    def generate_path(path_type: str = "L_shape") -> np.ndarray:
        """
        Generate a reference path based on the specified type.
        
        Args:
            path_type: Type of path to generate. Options:
                      - "straight": Straight line path
                      - "circle": Circular path
                      - "L_shape": L-shaped path (garage scenario)
        
        Returns:
            np.ndarray: Nx2 array where each row is [x, y] coordinate
            
        Raises:
            ValueError: If path_type is not recognized or path generation fails
        """
        if not isinstance(path_type, str):
            raise ValueError(f"path_type must be a string, got {type(path_type)}")
        
        path_type = path_type.lower()
        
        try:
            if path_type == "straight":
                path = PathPlanner._generate_straight_path()
            elif path_type == "circle":
                path = PathPlanner._generate_circular_path()
            elif path_type == "l_shape":
                path = PathPlanner._generate_l_shape_path()
            else:
                raise ValueError(
                    f"Unknown path type: '{path_type}'. "
                    f"Valid options: 'straight', 'circle', 'L_shape'"
                )
            
            # Validate generated path
            if path.size == 0:
                raise ValueError(f"Generated path is empty for type '{path_type}'")
            if path.shape[1] != 2:
                raise ValueError(f"Path must have 2 columns (x, y), got shape {path.shape}")
            
            return path
            
        except Exception as e:
            raise ValueError(f"Failed to generate path of type '{path_type}': {str(e)}")
    
    @staticmethod
    def _generate_straight_path(
        start: float = 0.0,
        end: float = 10.0,
        num_points: int = 100
    ) -> np.ndarray:
        """
        Generate a straight line path along the x-axis.
        
        Args:
            start: Starting x coordinate
            end: Ending x coordinate
            num_points: Number of waypoints
            
        Returns:
            np.ndarray: Nx2 path array
        """
        x = np.linspace(start, end, num_points)
        y = np.zeros_like(x)
        return np.column_stack([x, y])
    
    @staticmethod
    def _generate_circular_path(
        center_x: float = 3.0,
        center_y: float = 0.0,
        radius: float = 3.0,
        num_points: int = 200
    ) -> np.ndarray:
        """
        Generate a circular path.
        
        Args:
            center_x: Circle center x coordinate
            center_y: Circle center y coordinate
            radius: Circle radius
            num_points: Number of waypoints
            
        Returns:
            np.ndarray: Nx2 path array
        """
        theta = np.linspace(0, 2*np.pi, num_points)
        x = center_x + radius * np.cos(theta)
        y = center_y + radius * np.sin(theta)
        return np.column_stack([x, y])
    
    @staticmethod
    def _generate_l_shape_path(
        straight1_length: float = 5.0,
        turn_radius: float = 2.0,
        straight2_length: float = 4.0,
        points_per_segment: int = 50
    ) -> np.ndarray:
        """
        Generate an L-shaped path (garage scenario).
        
        The path consists of:
        1. Straight segment along x-axis
        2. 90-degree circular arc turn
        3. Straight segment along y-axis (to charging station)
        
        Args:
            straight1_length: Length of first straight segment
            turn_radius: Radius of the turning arc
            straight2_length: Length of second straight segment
            points_per_segment: Number of points per segment
            
        Returns:
            np.ndarray: Nx2 path array
        """
        # Segment 1: Straight along x-axis
        x1 = np.linspace(0, straight1_length, points_per_segment)
        y1 = np.zeros_like(x1)
        
        # Segment 2: 90-degree circular arc
        theta = np.linspace(0, np.pi/2, int(points_per_segment * 0.6))
        x2 = straight1_length + turn_radius * np.sin(theta)
        y2 = turn_radius * (1 - np.cos(theta))
        
        # Segment 3: Straight along y-axis
        y_start = y2[-1]
        y_end = y_start + straight2_length
        x3 = np.full(int(points_per_segment * 0.8), x2[-1])
        y3 = np.linspace(y_start, y_end, int(points_per_segment * 0.8))
        
        # Concatenate all segments
        x = np.concatenate([x1, x2, x3])
        y = np.concatenate([y1, y2, y3])
        
        return np.column_stack([x, y])
    
    @staticmethod
    def validate_path(path: np.ndarray) -> bool:
        """
        Validate that a path is properly formatted.
        
        Args:
            path: Path array to validate
            
        Returns:
            bool: True if path is valid
            
        Raises:
            ValueError: If path is invalid with detailed error message
        """
        if not isinstance(path, np.ndarray):
            raise ValueError(f"Path must be a numpy array, got {type(path)}")
        
        if path.ndim != 2:
            raise ValueError(f"Path must be 2D array, got {path.ndim}D")
        
        if path.shape[0] < 2:
            raise ValueError(f"Path must have at least 2 points, got {path.shape[0]}")
        
        if path.shape[1] != 2:
            raise ValueError(f"Path must have 2 columns (x, y), got {path.shape[1]}")
        
        if np.any(np.isnan(path)) or np.any(np.isinf(path)):
            raise ValueError("Path contains NaN or Inf values")
        
        return True
