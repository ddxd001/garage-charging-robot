#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仿真引擎模块

本模块是整个仿真系统的核心，负责协调各个组件：
- 机器人模型：全向轮底盘运动学
- 控制器：路径跟踪控制算法
- 路径规划器：生成参考路径
- 性能评估：计算控制性能指标
- 状态机：管理任务流程(可选)

仿真流程：
    1. 初始化机器人、控制器和路径
    2. 循环执行：计算控制量 -> 更新状态
    3. 记录数据：位置、速度、误差等
    4. 评估性能：计算各项指标

作者：车库机器人团队
版本：1.3.0
日期：2026-03
"""

import numpy as np
from typing import List, Optional
from .config import SimulationConfig
from .chassis import OmniDirectionalRobot
from .controller import OmniPathTrackingController
from .path_planner import PathPlanner
from .metrics import PerformanceMetrics, MetricsCalculator
from .state_machine import ChargingRobotStateMachine, RobotState


class SimulationData:
    """
    Container for simulation data history.
    
    Stores all time-series data generated during simulation for later analysis
    and visualization.
    """
    
    def __init__(self) -> None:
        """Initialize empty data containers."""
        self.time: List[float] = []
        self.x: List[float] = []
        self.y: List[float] = []
        self.yaw: List[float] = []
        self.vx: List[float] = []
        self.vy: List[float] = []
        self.omega: List[float] = []
        self.wheel_velocities: List[np.ndarray] = []
        self.tracking_error: List[float] = []
        self.states: List[str] = []  # State at each timestep
    
    def append(
        self,
        t: float,
        x: float,
        y: float,
        yaw: float,
        vx: float,
        vy: float,
        omega: float,
        wheel_vel: np.ndarray,
        error: float,
        state: str = "UNKNOWN"
    ) -> None:
        """
        Append a new data point to the history.
        
        Args:
            t: Time (s)
            x: X position (m)
            y: Y position (m)
            yaw: Heading angle (rad)
            vx: X velocity in robot frame (m/s)
            vy: Y velocity in robot frame (m/s)
            omega: Angular velocity (rad/s)
            wheel_vel: Array of wheel velocities (rad/s)
            error: Tracking error (m)
            state: Current robot state
        """
        self.time.append(t)
        self.x.append(x)
        self.y.append(y)
        self.yaw.append(yaw)
        self.vx.append(vx)
        self.vy.append(vy)
        self.omega.append(omega)
        self.wheel_velocities.append(wheel_vel.copy())
        self.tracking_error.append(error)
        self.states.append(state)
    
    def get_statistics(self) -> dict:
        """
        Compute statistics from the simulation data.
        
        Returns:
            dict: Dictionary containing statistical metrics
        """
        if not self.tracking_error:
            return {}
        
        return {
            'mean_error': np.mean(self.tracking_error),
            'max_error': np.max(self.tracking_error),
            'min_error': np.min(self.tracking_error),
            'std_error': np.std(self.tracking_error),
            'final_x': self.x[-1] if self.x else 0.0,
            'final_y': self.y[-1] if self.y else 0.0,
            'final_yaw': self.yaw[-1] if self.yaw else 0.0,
            'total_time': self.time[-1] if self.time else 0.0,
        }


class Simulator:
    """
    Main simulation engine with state machine.
    
    Coordinates the robot, controller, path planner, and state machine to run
    the charging task simulation and collect data.
    
    Attributes:
        config (SimulationConfig): Simulation configuration
        robot (OmniDirectionalRobot): Robot instance
        controller (OmniPathTrackingController): Controller instance
        path (np.ndarray): Reference path
        data (SimulationData): Collected simulation data
        metrics (PerformanceMetrics): Performance evaluation metrics
        state_machine (ChargingRobotStateMachine): Task state machine
    """
    
    def __init__(self, config: SimulationConfig, use_state_machine: bool = False) -> None:
        """
        Initialize the simulator.
        
        Args:
            config: Simulation configuration object
            use_state_machine: Whether to use state machine for task flow
            
        Raises:
            ValueError: If configuration is invalid
        """
        if not isinstance(config, SimulationConfig):
            raise ValueError(f"config must be SimulationConfig, got {type(config)}")
        
        self.config = config
        self.use_state_machine = use_state_machine
        
        # Create robot
        self.robot = OmniDirectionalRobot(
            x=config.init_x,
            y=config.init_y,
            yaw=config.init_yaw,
            robot_radius=config.robot_radius,
            wheel_radius=config.wheel_radius
        )
        
        # Create controller
        self.controller = OmniPathTrackingController(
            look_ahead_distance=config.look_ahead_distance,
            position_gain=config.position_gain,
            heading_gain=config.heading_gain
        )
        
        # Generate reference path
        try:
            self.path = PathPlanner.generate_path(config.path_type)
            PathPlanner.validate_path(self.path)
        except Exception as e:
            raise ValueError(f"Failed to generate valid path: {str(e)}")
        
        # Initialize data storage
        self.data = SimulationData()
        
        # Performance metrics (calculated after simulation)
        self.metrics: Optional[PerformanceMetrics] = None
        
        # State machine (optional)
        self.state_machine: Optional[ChargingRobotStateMachine] = None
        if use_state_machine:
            self.state_machine = ChargingRobotStateMachine(
                pre_dock_distance=0.5,
                dock_position_tolerance=0.05,
                dock_heading_tolerance=5.0,
                docking_duration=2.0
            )
        
        # Simulation state
        self._is_running = False
        self._goal_reached = False
    
    def run(self, verbose: bool = True) -> SimulationData:
        """
        Run the simulation.
        
        Args:
            verbose: Whether to print progress information
            
        Returns:
            SimulationData: Collected simulation data
            
        Raises:
            RuntimeError: If simulation encounters an error
        """
        try:
            self._is_running = True
            self._goal_reached = False
            
            # Calculate number of simulation steps
            num_steps = int(self.config.total_time / self.config.dt)
            
            if verbose:
                self._print_header()
            
            # Start state machine if enabled
            if self.state_machine:
                self.state_machine.start_task(0.0)
            
            # Main simulation loop
            for step in range(num_steps):
                t = step * self.config.dt
                
                # Get current state
                x, y, yaw = self.robot.get_state()
                
                # Calculate distances and errors
                goal_dist = self._calculate_goal_distance(x, y)
                tracking_error = self._calculate_tracking_error(x, y)
                heading_error = self._calculate_heading_error(x, y, yaw)
                
                # Update state machine if enabled
                current_state_name = "NORMAL"
                velocity_scale = 1.0
                
                if self.state_machine:
                    self.state_machine.update(t, goal_dist, tracking_error, heading_error)
                    current_state_name = self.state_machine.get_state_name()
                    velocity_scale = self.state_machine.get_max_velocity_scale()
                    
                    # Check if task is complete
                    if self.state_machine.is_task_complete():
                        if verbose:
                            print(f"\nTask completed at time: {t:.2f} s")
                        self._goal_reached = True
                        break
                else:
                    # Original goal check without state machine
                    if goal_dist < self.config.goal_threshold:
                        if verbose:
                            print(f"\nGoal reached at time: {t:.2f} s")
                        self._goal_reached = True
                        break
                
                # Compute control commands
                try:
                    vx, vy, omega = self.controller.compute_control(
                        x, y, yaw, self.path, self.config.max_linear_vel
                    )
                except Exception as e:
                    raise RuntimeError(f"Controller error at t={t:.2f}s: {str(e)}")
                
                # Apply velocity scaling based on state
                vx *= velocity_scale
                vy *= velocity_scale
                
                # Limit angular velocity
                omega = np.clip(omega, -self.config.max_angular_vel, self.config.max_angular_vel)
                
                # Update robot state
                try:
                    self.robot.update(vx, vy, omega, self.config.dt)
                except Exception as e:
                    raise RuntimeError(f"Robot update error at t={t:.2f}s: {str(e)}")
                
                # Get wheel velocities
                wheel_velocities = self.robot.get_wheel_velocities()
                
                # Record data
                self.data.append(t, x, y, yaw, vx, vy, omega, wheel_velocities, 
                               tracking_error, current_state_name)
                
                # Print progress
                if verbose and step % 50 == 0:
                    self._print_progress(t, x, y, yaw, vx, vy, tracking_error, current_state_name)
            
            # Calculate performance metrics after simulation
            self.metrics = MetricsCalculator.calculate_metrics(
                time_history=self.data.time,
                x_history=self.data.x,
                y_history=self.data.y,
                yaw_history=self.data.yaw,
                error_history=self.data.tracking_error,
                reference_path=self.path,
                goal_reached=self._goal_reached,
                goal_threshold=self.config.goal_threshold
            )
            
            if verbose:
                self._print_summary()
                if self.state_machine:
                    self.state_machine.print_state_log()
            
            self._is_running = False
            return self.data
            
        except Exception as e:
            self._is_running = False
            raise RuntimeError(f"Simulation failed: {str(e)}")
    
    def _calculate_goal_distance(self, x: float, y: float) -> float:
        """Calculate distance to the goal point."""
        goal_x, goal_y = self.path[-1]
        return np.sqrt((x - goal_x)**2 + (y - goal_y)**2)
    
    def _calculate_tracking_error(self, x: float, y: float) -> float:
        """Calculate minimum distance to the reference path."""
        distances = np.sqrt((self.path[:, 0] - x)**2 + (self.path[:, 1] - y)**2)
        return np.min(distances)
    
    def _calculate_heading_error(self, x: float, y: float, yaw: float) -> float:
        """Calculate heading error in degrees."""
        # Find closest point on path
        distances = np.sqrt((self.path[:, 0] - x)**2 + (self.path[:, 1] - y)**2)
        closest_idx = np.argmin(distances)
        
        # Find next point for desired heading
        next_idx = min(closest_idx + 5, len(self.path) - 1)
        
        # Calculate desired heading
        dx = self.path[next_idx, 0] - self.path[closest_idx, 0]
        dy = self.path[next_idx, 1] - self.path[closest_idx, 1]
        
        if dx != 0 or dy != 0:
            desired_yaw = np.arctan2(dy, dx)
            error = desired_yaw - yaw
            error = np.arctan2(np.sin(error), np.cos(error))
            return np.degrees(error)
        return 0.0
    
    def _print_header(self) -> None:
        """Print simulation header."""
        print("=" * 70)
        print("Starting Simulation...")
        if self.state_machine:
            print("Mode: State Machine Enabled")
        print(f"Total time: {self.config.total_time} s")
        print(f"Time step: {self.config.dt} s")
        print(f"Path points: {len(self.path)}")
        print(f"Path type: {self.config.path_type}")
        print("=" * 70)
    
    def _print_progress(
        self,
        t: float,
        x: float,
        y: float,
        yaw: float,
        vx: float,
        vy: float,
        error: float,
        state: str = "NORMAL"
    ) -> None:
        """Print simulation progress."""
        vel_total = np.sqrt(vx**2 + vy**2)
        state_str = f"[{state}]" if self.state_machine else ""
        print(f"Time: {t:6.2f} s {state_str:<20} | Pos: ({x:6.2f}, {y:6.2f}) | "
              f"Heading: {np.degrees(yaw):6.1f}° | "
              f"Vel: {vel_total:5.2f} m/s | Error: {error:6.3f} m")
    
    def _print_summary(self) -> None:
        """Print simulation summary."""
        stats = self.data.get_statistics()
        
        print("=" * 70)
        print("Simulation Complete!")
        print(f"Final position: ({stats['final_x']:.2f}, {stats['final_y']:.2f})")
        print(f"Final heading: {np.degrees(stats['final_yaw']):.1f}°")
        print(f"Total time: {stats['total_time']:.2f} s")
        print(f"Mean tracking error: {stats['mean_error']:.3f} m")
        print(f"Max tracking error: {stats['max_error']:.3f} m")
        print(f"Goal reached: {'Yes' if self._goal_reached else 'No'}")
        print("=" * 70)
    
    def get_performance_metrics(self) -> Optional[PerformanceMetrics]:
        """Get calculated performance metrics."""
        return self.metrics
    
    def print_performance_summary(self) -> None:
        """Print detailed performance metrics summary."""
        if self.metrics is None:
            print("Warning: Performance metrics not calculated. Run simulation first.")
            return
        
        MetricsCalculator.print_summary(self.metrics)
    
    def save_metrics_to_csv(self, filepath: str, append: bool = False) -> None:
        """Save performance metrics to CSV file."""
        if self.metrics is None:
            raise ValueError("Performance metrics not calculated. Run simulation first.")
        
        MetricsCalculator.save_to_csv(self.metrics, filepath, append)
    
    def get_state_machine(self) -> Optional[ChargingRobotStateMachine]:
        """Get state machine instance."""
        return self.state_machine
    
    def reset(self) -> None:
        """Reset the simulation to initial state."""
        self.robot.reset(
            self.config.init_x,
            self.config.init_y,
            self.config.init_yaw
        )
        self.controller.reset()
        self.data = SimulationData()
        self.metrics = None
        if self.state_machine:
            self.state_machine.reset()
        self._is_running = False
        self._goal_reached = False
    
    @property
    def is_running(self) -> bool:
        """Check if simulation is currently running."""
        return self._is_running
    
    @property
    def goal_reached(self) -> bool:
        """Check if goal was reached."""
        return self._goal_reached
