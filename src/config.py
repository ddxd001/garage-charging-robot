#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置参数模块

本模块定义了车库充电机器人仿真系统的所有配置参数，包括：
- 时间参数：仿真步长、总时长
- 机器人物理参数：尺寸、速度限制
- 控制器参数：增益、前视距离
- 初始状态：位置、姿态
- 路径规划参数：路径类型
- 可视化参数：图表设置

作者：车库机器人团队
版本：1.3.0
日期：2026-03
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SimulationConfig:
    """
    仿真配置参数类
    
    使用数据类(dataclass)封装所有仿真参数，便于参数管理和传递。
    所有参数都有默认值，可根据实际需求进行调整。
    
    参数分类：
        - 时间参数：控制仿真的时间步长和总时长
        - 机器人参数：定义机器人的物理特性
        - 控制器参数：路径跟踪控制器的增益和阈值
        - 初始状态：机器人的起始位置和姿态
        - 路径参数：参考路径的类型和生成方式
        - 可视化参数：结果图表的显示和保存设置
    """
    
    # ==================== 时间参数 ====================
    dt: float = 0.05
    """仿真时间步长(秒)，影响仿真精度和计算速度"""
    
    total_time: float = 30.0
    """仿真总时长(秒)，足够机器人完成路径跟踪任务"""
    
    # ==================== 机器人物理参数 ====================
    robot_radius: float = 0.25
    """机器人中心到车轮中心的距离(米)，用于运动学逆解计算"""
    
    wheel_radius: float = 0.05
    """全向轮半径(米)，用于将角速度转换为线速度"""
    
    max_wheel_vel: float = 10.0
    """车轮最大角速度(rad/s)，物理限制"""
    
    max_linear_vel: float = 0.5
    """机器人最大线速度(m/s)，用于速度限制"""
    
    max_angular_vel: float = 1.0
    """机器人最大角速度(rad/s)，用于转向速度限制"""
    
    # ==================== 控制器参数 ====================
    look_ahead_distance: float = 0.8
    """前视距离(米)，控制路径跟踪的平滑度，越大越平滑但可能切弯"""
    
    goal_threshold: float = 0.1
    """到位判断阈值(米)，小于此距离认为到达目标点"""
    
    position_gain: float = 1.5
    """位置控制比例增益，影响位置误差的响应速度"""
    
    heading_gain: float = 2.0
    """航向控制比例增益，影响航向误差的响应速度"""
    
    # ==================== 初始状态参数 ====================
    init_x: float = 0.0
    """初始X坐标(米)，机器人起始位置的横坐标"""
    
    init_y: float = 0.0
    """初始Y坐标(米)，机器人起始位置的纵坐标"""
    
    init_yaw: float = 0.0
    """初始航向角(弧度)，机器人起始朝向，0表示沿X轴正方向"""
    
    # ==================== 路径规划参数 ====================
    path_type: str = "L_shape"
    """参考路径类型：'straight'(直线)、'circle'(圆形)、'L_shape'(L形)"""
    
    # ==================== 可视化参数 ====================
    save_plot: bool = True
    """是否保存结果图表"""
    
    plot_filename: str = "simulation_results.png"
    """保存的图表文件名"""
    
    plot_dpi: int = 150
    """图表分辨率(DPI)，越高越清晰但文件越大"""
    
    show_plot: bool = True
    """是否显示图表窗口"""
    
    def __post_init__(self) -> None:
        """
        初始化后的参数验证
        
        在数据类初始化完成后自动调用，用于验证参数的合法性。
        
        异常:
            ValueError: 当参数不合法时抛出
        """
        self._validate_parameters()
    
    def _validate_parameters(self) -> None:
        """
        验证所有配置参数的合法性
        
        检查各参数是否在合理范围内，确保仿真能够正常运行。
        
        异常:
            ValueError: 当参数超出有效范围时抛出
        """
        # 时间参数验证
        if self.dt <= 0:
            raise ValueError(f"时间步长必须为正数，当前值: {self.dt}")
        if self.total_time <= 0:
            raise ValueError(f"总时长必须为正数，当前值: {self.total_time}")
        if self.dt > self.total_time:
            raise ValueError(f"Time step ({self.dt}) cannot exceed total time ({self.total_time})")
        
        # Physical parameters
        if self.robot_radius <= 0:
            raise ValueError(f"Robot radius must be positive, got {self.robot_radius}")
        if self.wheel_radius <= 0:
            raise ValueError(f"Wheel radius must be positive, got {self.wheel_radius}")
        if self.max_wheel_vel <= 0:
            raise ValueError(f"Max wheel velocity must be positive, got {self.max_wheel_vel}")
        if self.max_linear_vel <= 0:
            raise ValueError(f"Max linear velocity must be positive, got {self.max_linear_vel}")
        if self.max_angular_vel <= 0:
            raise ValueError(f"Max angular velocity must be positive, got {self.max_angular_vel}")
        
        # Controller parameters
        if self.look_ahead_distance <= 0:
            raise ValueError(f"Look-ahead distance must be positive, got {self.look_ahead_distance}")
        if self.goal_threshold <= 0:
            raise ValueError(f"Goal threshold must be positive, got {self.goal_threshold}")
        if self.position_gain <= 0:
            raise ValueError(f"Position gain must be positive, got {self.position_gain}")
        if self.heading_gain <= 0:
            raise ValueError(f"Heading gain must be positive, got {self.heading_gain}")
        
        # Path type
        valid_path_types = ["straight", "circle", "L_shape"]
        if self.path_type not in valid_path_types:
            raise ValueError(f"Invalid path type '{self.path_type}'. Must be one of {valid_path_types}")
        
        # Visualization
        if self.plot_dpi <= 0:
            raise ValueError(f"Plot DPI must be positive, got {self.plot_dpi}")
    
    def summary(self) -> str:
        """
        Generate a summary string of the configuration.
        
        Returns:
            str: Formatted configuration summary
        """
        return f"""
Simulation Configuration Summary:
{'=' * 50}
Time Parameters:
  - Time step: {self.dt} s
  - Total time: {self.total_time} s
  
Robot Parameters:
  - Robot radius: {self.robot_radius} m
  - Wheel radius: {self.wheel_radius} m
  - Max linear velocity: {self.max_linear_vel} m/s
  - Max angular velocity: {self.max_angular_vel} rad/s
  
Controller Parameters:
  - Look-ahead distance: {self.look_ahead_distance} m
  - Goal threshold: {self.goal_threshold} m
  - Position gain: {self.position_gain}
  - Heading gain: {self.heading_gain}
  
Initial State:
  - Position: ({self.init_x}, {self.init_y})
  - Heading: {self.init_yaw} rad
  
Path: {self.path_type}
{'=' * 50}
"""
