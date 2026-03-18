#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路径跟踪控制器模块

本模块实现了全向轮机器人的路径跟踪控制算法，采用位置-航向解耦控制策略：
- 位置控制：根据机器人到路径的距离生成速度指令
- 航向控制：根据期望朝向调整角速度
- 前视控制：在路径上选取前视点，引导机器人跟踪

控制特点：
    - 比例控制(P控制)，简单有效
    - 位置和航向独立控制，互不干扰
    - 可调节的控制增益，适应不同场景

作者：车库机器人团队
版本：1.3.0
日期：2026-03
"""

import numpy as np
from typing import Tuple


class OmniPathTrackingController:
    """
    Path tracking controller for omni-directional robots.
    
    This controller leverages the omni-directional capability to independently
    control x, y velocities and rotation. It uses:
    - Position error feedback for translational control
    - Heading error feedback for rotational control
    
    Attributes:
        look_ahead_distance (float): Distance to look ahead on path (m)
        position_gain (float): Proportional gain for position control
        heading_gain (float): Proportional gain for heading control
        target_idx (int): Current target waypoint index
    """
    
    def __init__(
        self,
        look_ahead_distance: float,
        position_gain: float,
        heading_gain: float
    ) -> None:
        """
        Initialize the path tracking controller.
        
        Args:
            look_ahead_distance: Look-ahead distance (m)
            position_gain: Proportional gain for position control
            heading_gain: Proportional gain for heading control
            
        Raises:
            ValueError: If any parameter is invalid
        """
        if look_ahead_distance <= 0:
            raise ValueError(f"Look-ahead distance must be positive, got {look_ahead_distance}")
        if position_gain <= 0:
            raise ValueError(f"Position gain must be positive, got {position_gain}")
        if heading_gain <= 0:
            raise ValueError(f"Heading gain must be positive, got {heading_gain}")
        
        self.look_ahead_distance = float(look_ahead_distance)
        self.position_gain = float(position_gain)
        self.heading_gain = float(heading_gain)
        self.target_idx = 0
    
    def find_target_point(
        self,
        robot_x: float,
        robot_y: float,
        path: np.ndarray
    ) -> Tuple[float, float, int]:
        """
        Find the look-ahead target point on the path.
        
        Searches along the path starting from the current target index to find
        the first point that is at least look_ahead_distance away from the robot.
        
        Args:
            robot_x: Current robot x coordinate
            robot_y: Current robot y coordinate
            path: Reference path as Nx2 array
            
        Returns:
            Tuple[float, float, int]: (target_x, target_y, target_index)
            
        Raises:
            ValueError: If path is invalid
        """
        if path.size == 0:
            raise ValueError("Path is empty")
        if path.shape[1] != 2:
            raise ValueError(f"Path must have 2 columns, got {path.shape[1]}")
        
        # Calculate distances from robot to all path points
        distances = np.sqrt((path[:, 0] - robot_x)**2 + (path[:, 1] - robot_y)**2)
        
        # Search from current target index onwards
        for i in range(self.target_idx, len(path)):
            if distances[i] >= self.look_ahead_distance:
                self.target_idx = i
                return path[i, 0], path[i, 1], i
        
        # If no point found, return path endpoint
        self.target_idx = len(path) - 1
        return path[-1, 0], path[-1, 1], len(path) - 1
    
    def compute_control(
        self,
        robot_x: float,
        robot_y: float,
        robot_yaw: float,
        path: np.ndarray,
        max_v: float
    ) -> Tuple[float, float, float]:
        """
        Compute control commands for the omni-directional robot.
        
        Args:
            robot_x: Robot x coordinate in world frame
            robot_y: Robot y coordinate in world frame
            robot_yaw: Robot heading angle (rad)
            path: Reference path as Nx2 array
            max_v: Maximum linear velocity (m/s)
            
        Returns:
            Tuple[float, float, float]: (vx, vy, omega) in robot frame
                - vx: velocity in robot's forward direction (m/s)
                - vy: velocity in robot's lateral direction (m/s)
                - omega: angular velocity (rad/s)
                
        Raises:
            ValueError: If inputs are invalid
        """
        if max_v <= 0:
            raise ValueError(f"Maximum velocity must be positive, got {max_v}")
        
        # Find target point
        target_x, target_y, _ = self.find_target_point(robot_x, robot_y, path)
        
        # Calculate position error in world frame
        error_x_world = target_x - robot_x
        error_y_world = target_y - robot_y
        
        # Transform error to robot frame
        cos_yaw = np.cos(robot_yaw)
        sin_yaw = np.sin(robot_yaw)
        
        error_x_robot = error_x_world * cos_yaw + error_y_world * sin_yaw
        error_y_robot = -error_x_world * sin_yaw + error_y_world * cos_yaw
        
        # Position control (proportional)
        vx = self.position_gain * error_x_robot
        vy = self.position_gain * error_y_robot
        
        # Limit velocity magnitude
        vel_magnitude = np.sqrt(vx**2 + vy**2)
        if vel_magnitude > max_v:
            scale = max_v / vel_magnitude
            vx *= scale
            vy *= scale
        
        # Heading control: compute desired heading (pointing to target)
        desired_yaw = np.arctan2(error_y_world, error_x_world)
        yaw_error = desired_yaw - robot_yaw
        
        # Normalize yaw error to [-pi, pi]
        yaw_error = np.arctan2(np.sin(yaw_error), np.cos(yaw_error))
        
        # Angular velocity control
        omega = self.heading_gain * yaw_error
        
        return vx, vy, omega
    
    def reset(self) -> None:
        """Reset the controller state."""
        self.target_idx = 0
    
    def __repr__(self) -> str:
        """String representation of the controller."""
        return (f"OmniPathTrackingController("
                f"look_ahead={self.look_ahead_distance:.2f}, "
                f"pos_gain={self.position_gain:.2f}, "
                f"heading_gain={self.heading_gain:.2f})")
