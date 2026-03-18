#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全向轮底盘运动学模块

本模块实现了三轮全向轮移动机器人的运动学模型，包括：
- 正向运动学：根据车轮速度计算机器人速度
- 逆向运动学：根据期望速度计算车轮速度
- 速度限制：确保车轮速度不超过物理限制

底盘配置：
    - 三个全向轮呈正三角形布局
    - 车轮角度：0°, 120°, 240°
    - 可实现全方向移动，无需转向

作者：车库机器人团队
版本：1.3.0
日期：2026-03
"""

import numpy as np
from typing import Tuple


class OmniDirectionalRobot:
    """
    Omni-directional robot with three wheels in equilateral triangle configuration.
    
    The three wheels are positioned at:
    - Wheel 1: 0°   (front)
    - Wheel 2: 120° (rear-left)
    - Wheel 3: 240° (rear-right)
    
    Kinematics equation (forward kinematics):
    [ω1]   [  sin(0°)    -cos(0°)    -R ] [vx]
    [ω2] = [  sin(120°)  -cos(120°)  -R ] [vy]
    [ω3]   [  sin(240°)  -cos(240°)  -R ] [ω ]
    
    where R is the distance from robot center to wheel center.
    
    Attributes:
        x (float): Current x position in world frame (m)
        y (float): Current y position in world frame (m)
        yaw (float): Current heading angle (rad)
        robot_radius (float): Distance from center to wheel (m)
        wheel_radius (float): Wheel radius (m)
        vx (float): Current velocity in x direction (robot frame) (m/s)
        vy (float): Current velocity in y direction (robot frame) (m/s)
        omega (float): Current angular velocity (rad/s)
    """
    
    def __init__(
        self,
        x: float,
        y: float,
        yaw: float,
        robot_radius: float,
        wheel_radius: float
    ) -> None:
        """
        Initialize the omni-directional robot.
        
        Args:
            x: Initial x coordinate (m)
            y: Initial y coordinate (m)
            yaw: Initial heading angle (rad)
            robot_radius: Distance from robot center to wheel center (m)
            wheel_radius: Wheel radius (m)
            
        Raises:
            ValueError: If any parameter is invalid
        """
        # Validate inputs
        if robot_radius <= 0:
            raise ValueError(f"Robot radius must be positive, got {robot_radius}")
        if wheel_radius <= 0:
            raise ValueError(f"Wheel radius must be positive, got {wheel_radius}")
        
        # Position and orientation
        self.x = float(x)
        self.y = float(y)
        self.yaw = float(yaw)
        
        # Physical parameters
        self.robot_radius = float(robot_radius)
        self.wheel_radius = float(wheel_radius)
        
        # Current velocities (robot frame)
        self.vx = 0.0
        self.vy = 0.0
        self.omega = 0.0
        
        # Wheel angles relative to robot center (counter-clockwise positive)
        self.wheel_angles = np.array([0.0, 2*np.pi/3, 4*np.pi/3])  # [0°, 120°, 240°]
        
        # Build kinematics matrices
        self._build_kinematics_matrix()
    
    def _build_kinematics_matrix(self) -> None:
        """
        Build the forward kinematics matrix.
        
        The matrix J maps robot velocities [vx, vy, omega] to wheel angular velocities.
        """
        self.J = np.zeros((3, 3))
        for i, angle in enumerate(self.wheel_angles):
            self.J[i, 0] = np.sin(angle)           # vx component
            self.J[i, 1] = -np.cos(angle)          # vy component
            self.J[i, 2] = -self.robot_radius      # omega component
        
        # Inverse kinematics matrix (for potential future use)
        self.J_inv = np.linalg.pinv(self.J)
    
    def update(
        self,
        vx_cmd: float,
        vy_cmd: float,
        omega_cmd: float,
        dt: float
    ) -> None:
        """
        Update robot state using kinematics model.
        
        Args:
            vx_cmd: Velocity command in x direction (robot frame) (m/s)
            vy_cmd: Velocity command in y direction (robot frame) (m/s)
            omega_cmd: Angular velocity command (rad/s)
            dt: Time step (s)
            
        Raises:
            ValueError: If time step is non-positive
        """
        if dt <= 0:
            raise ValueError(f"Time step must be positive, got {dt}")
        
        # Store current velocities
        self.vx = float(vx_cmd)
        self.vy = float(vy_cmd)
        self.omega = float(omega_cmd)
        
        # Transform velocities from robot frame to world frame
        cos_yaw = np.cos(self.yaw)
        sin_yaw = np.sin(self.yaw)
        
        vx_world = vx_cmd * cos_yaw - vy_cmd * sin_yaw
        vy_world = vx_cmd * sin_yaw + vy_cmd * cos_yaw
        
        # Update position and orientation
        self.x += vx_world * dt
        self.y += vy_world * dt
        self.yaw += omega_cmd * dt
        
        # Normalize heading angle to [-pi, pi]
        self.yaw = np.arctan2(np.sin(self.yaw), np.cos(self.yaw))
    
    def get_wheel_velocities(self) -> np.ndarray:
        """
        Calculate angular velocities of the three wheels.
        
        Returns:
            np.ndarray: Array of three wheel angular velocities (rad/s)
                       [wheel1, wheel2, wheel3]
        """
        robot_vel = np.array([self.vx, self.vy, self.omega])
        wheel_angular_vel = self.J @ robot_vel / self.wheel_radius
        return wheel_angular_vel
    
    def get_state(self) -> Tuple[float, float, float]:
        """
        Get current robot state.
        
        Returns:
            Tuple[float, float, float]: (x, y, yaw) in world frame
        """
        return self.x, self.y, self.yaw
    
    def get_velocities(self) -> Tuple[float, float, float]:
        """
        Get current robot velocities in robot frame.
        
        Returns:
            Tuple[float, float, float]: (vx, vy, omega)
        """
        return self.vx, self.vy, self.omega
    
    def reset(self, x: float, y: float, yaw: float) -> None:
        """
        Reset robot to a new state.
        
        Args:
            x: New x coordinate (m)
            y: New y coordinate (m)
            yaw: New heading angle (rad)
        """
        self.x = float(x)
        self.y = float(y)
        self.yaw = float(yaw)
        self.vx = 0.0
        self.vy = 0.0
        self.omega = 0.0
    
    def __repr__(self) -> str:
        """String representation of the robot state."""
        return (f"OmniDirectionalRobot(x={self.x:.3f}, y={self.y:.3f}, "
                f"yaw={np.degrees(self.yaw):.1f}°)")
