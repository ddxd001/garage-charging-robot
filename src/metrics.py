#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能评估模块

本模块用于计算和管理控制系统的性能指标，包括：
- 位置跟踪性能：平均误差、最大误差、最终误差
- 航向跟踪性能：平均航向误差、最大航向误差
- 路径效率：实际路径长度与参考路径长度的比值
- 时间性能：总时间、稳定时间

评估方法：
    - 基于仿真数据计算各项指标
    - 提供统一的性能评估接口
    - 支持CSV格式导出

作者：车库机器人团队
版本：1.3.0
日期：2026-03
"""

import numpy as np
import csv
from typing import Dict, Optional, List
from pathlib import Path
from dataclasses import dataclass, asdict


@dataclass
class PerformanceMetrics:
    """
    Container for control performance metrics.
    
    Physical Meanings:
    - mean_position_error: Average deviation from reference path (m)
      Indicates overall tracking accuracy
    
    - max_position_error: Maximum deviation from reference path (m)
      Indicates worst-case tracking performance
    
    - final_position_error: Distance from final position to goal (m)
      Indicates positioning accuracy at destination
    
    - mean_heading_error: Average heading deviation from desired direction (degrees)
      Indicates orientation tracking accuracy
    
    - max_heading_error: Maximum heading deviation (degrees)
      Indicates worst-case orientation error
    
    - total_simulation_time: Total time to complete the task (s)
      Indicates task completion efficiency
    
    - path_length: Total distance traveled by robot (m)
      Indicates path efficiency (compare with reference path length)
    
    - reference_path_length: Length of the reference path (m)
      Baseline for path efficiency comparison
    
    - path_efficiency: Ratio of actual path to reference path (%)
      100% means perfect path following, >100% means deviation
    
    - settling_time: Time to reach and stay within error threshold (s)
      Indicates convergence speed
    
    - steady_state_error: Average error in final 20% of trajectory (m)
      Indicates steady-state tracking performance
    """
    
    # Position metrics
    mean_position_error: float = 0.0
    max_position_error: float = 0.0
    final_position_error: float = 0.0
    steady_state_error: float = 0.0
    
    # Heading metrics
    mean_heading_error: float = 0.0
    max_heading_error: float = 0.0
    
    # Time metrics
    total_simulation_time: float = 0.0
    settling_time: float = 0.0
    
    # Path metrics
    path_length: float = 0.0
    reference_path_length: float = 0.0
    path_efficiency: float = 0.0
    
    # Additional info
    goal_reached: bool = False
    num_data_points: int = 0


class MetricsCalculator:
    """
    Calculator for control performance metrics.
    
    Computes various performance indicators from simulation data.
    """
    
    @staticmethod
    def calculate_metrics(
        time_history: List[float],
        x_history: List[float],
        y_history: List[float],
        yaw_history: List[float],
        error_history: List[float],
        reference_path: np.ndarray,
        goal_reached: bool,
        goal_threshold: float = 0.1
    ) -> PerformanceMetrics:
        """
        Calculate all performance metrics from simulation data.
        
        Args:
            time_history: Time series data (s)
            x_history: X position history (m)
            y_history: Y position history (m)
            yaw_history: Heading angle history (rad)
            error_history: Position error history (m)
            reference_path: Reference path as Nx2 array
            goal_reached: Whether goal was reached
            goal_threshold: Distance threshold for goal (m)
            
        Returns:
            PerformanceMetrics: Calculated metrics
        """
        metrics = PerformanceMetrics()
        
        if not time_history or not x_history:
            return metrics
        
        # Convert to numpy arrays for easier computation
        time_arr = np.array(time_history)
        x_arr = np.array(x_history)
        y_arr = np.array(y_history)
        yaw_arr = np.array(yaw_history)
        error_arr = np.array(error_history)
        
        # Basic info
        metrics.num_data_points = len(time_history)
        metrics.goal_reached = goal_reached
        
        # Position error metrics
        metrics.mean_position_error = float(np.mean(error_arr))
        metrics.max_position_error = float(np.max(error_arr))
        
        # Final position error
        goal_x, goal_y = reference_path[-1]
        metrics.final_position_error = float(
            np.sqrt((x_arr[-1] - goal_x)**2 + (y_arr[-1] - goal_y)**2)
        )
        
        # Steady-state error (last 20% of trajectory)
        steady_idx = int(0.8 * len(error_arr))
        if steady_idx < len(error_arr):
            metrics.steady_state_error = float(np.mean(error_arr[steady_idx:]))
        
        # Heading error metrics
        heading_errors = MetricsCalculator._calculate_heading_errors(
            x_arr, y_arr, yaw_arr, reference_path
        )
        metrics.mean_heading_error = float(np.mean(np.abs(heading_errors)))
        metrics.max_heading_error = float(np.max(np.abs(heading_errors)))
        
        # Time metrics
        metrics.total_simulation_time = float(time_arr[-1])
        metrics.settling_time = MetricsCalculator._calculate_settling_time(
            time_arr, error_arr, goal_threshold
        )
        
        # Path length metrics
        metrics.path_length = MetricsCalculator._calculate_path_length(x_arr, y_arr)
        metrics.reference_path_length = MetricsCalculator._calculate_path_length(
            reference_path[:, 0], reference_path[:, 1]
        )
        
        # Path efficiency (actual/reference * 100)
        # 100% = perfect following, >100% = longer path (deviation)
        if metrics.reference_path_length > 0:
            metrics.path_efficiency = float(
                (metrics.path_length / metrics.reference_path_length) * 100
            )
        
        return metrics
    
    @staticmethod
    def _calculate_heading_errors(
        x_arr: np.ndarray,
        y_arr: np.ndarray,
        yaw_arr: np.ndarray,
        reference_path: np.ndarray
    ) -> np.ndarray:
        """
        Calculate heading errors relative to desired direction.
        
        Args:
            x_arr: X positions
            y_arr: Y positions
            yaw_arr: Heading angles (rad)
            reference_path: Reference path
            
        Returns:
            np.ndarray: Heading errors in degrees
        """
        heading_errors = []
        
        for i in range(len(x_arr)):
            # Find closest point on reference path
            distances = np.sqrt(
                (reference_path[:, 0] - x_arr[i])**2 + 
                (reference_path[:, 1] - y_arr[i])**2
            )
            closest_idx = np.argmin(distances)
            
            # Find next point for desired heading
            next_idx = min(closest_idx + 5, len(reference_path) - 1)
            
            # Calculate desired heading
            dx = reference_path[next_idx, 0] - reference_path[closest_idx, 0]
            dy = reference_path[next_idx, 1] - reference_path[closest_idx, 1]
            
            if dx != 0 or dy != 0:
                desired_yaw = np.arctan2(dy, dx)
                error = desired_yaw - yaw_arr[i]
                # Normalize to [-pi, pi]
                error = np.arctan2(np.sin(error), np.cos(error))
                heading_errors.append(np.degrees(error))
            else:
                heading_errors.append(0.0)
        
        return np.array(heading_errors)
    
    @staticmethod
    def _calculate_settling_time(
        time_arr: np.ndarray,
        error_arr: np.ndarray,
        threshold: float
    ) -> float:
        """
        Calculate settling time (time to reach and stay within threshold).
        
        Args:
            time_arr: Time array
            error_arr: Error array
            threshold: Error threshold
            
        Returns:
            float: Settling time (s)
        """
        # Find first time error goes below threshold and stays there
        for i in range(len(error_arr)):
            if np.all(error_arr[i:] < threshold):
                return float(time_arr[i])
        
        # If never settles, return total time
        return float(time_arr[-1])
    
    @staticmethod
    def _calculate_path_length(x: np.ndarray, y: np.ndarray) -> float:
        """
        Calculate total path length.
        
        Args:
            x: X coordinates
            y: Y coordinates
            
        Returns:
            float: Total path length (m)
        """
        if len(x) < 2:
            return 0.0
        
        dx = np.diff(x)
        dy = np.diff(y)
        segments = np.sqrt(dx**2 + dy**2)
        return float(np.sum(segments))
    
    @staticmethod
    def print_summary(metrics: PerformanceMetrics, title: str = "PERFORMANCE METRICS") -> None:
        """
        Print a formatted summary of performance metrics.
        
        Args:
            metrics: Performance metrics object
            title: Title for the summary
        """
        print("\n" + "=" * 70)
        print(f"{title:^70}")
        print("=" * 70)
        
        print("\n📍 Position Tracking Performance:")
        print(f"  • Mean position error:        {metrics.mean_position_error:8.4f} m")
        print(f"  • Max position error:         {metrics.max_position_error:8.4f} m")
        print(f"  • Final position error:       {metrics.final_position_error:8.4f} m")
        print(f"  • Steady-state error:         {metrics.steady_state_error:8.4f} m")
        
        print("\n🧭 Heading Tracking Performance:")
        print(f"  • Mean heading error:         {metrics.mean_heading_error:8.2f} °")
        print(f"  • Max heading error:          {metrics.max_heading_error:8.2f} °")
        
        print("\n⏱️  Time Performance:")
        print(f"  • Total simulation time:      {metrics.total_simulation_time:8.2f} s")
        print(f"  • Settling time:              {metrics.settling_time:8.2f} s")
        
        print("\n📏 Path Performance:")
        print(f"  • Actual path length:         {metrics.path_length:8.2f} m")
        print(f"  • Reference path length:      {metrics.reference_path_length:8.2f} m")
        print(f"  • Path efficiency:            {metrics.path_efficiency:8.2f} %")
        
        print("\n✓ Task Completion:")
        print(f"  • Goal reached:               {'Yes ✓' if metrics.goal_reached else 'No ✗'}")
        print(f"  • Data points collected:      {metrics.num_data_points}")
        
        print("=" * 70)
    
    @staticmethod
    def save_to_csv(
        metrics: PerformanceMetrics,
        filepath: str,
        append: bool = False
    ) -> None:
        """
        Save metrics to CSV file.
        
        Args:
            metrics: Performance metrics object
            filepath: Path to save CSV file
            append: If True, append to existing file; if False, overwrite
            
        Raises:
            IOError: If file cannot be written
        """
        try:
            file_path = Path(filepath)
            file_exists = file_path.exists()
            
            mode = 'a' if (append and file_exists) else 'w'
            
            with open(file_path, mode, newline='') as csvfile:
                # Convert metrics to dictionary
                metrics_dict = asdict(metrics)
                
                writer = csv.DictWriter(csvfile, fieldnames=metrics_dict.keys())
                
                # Write header if new file or overwrite mode
                if mode == 'w' or not file_exists:
                    writer.writeheader()
                
                # Write data
                writer.writerow(metrics_dict)
            
            print(f"\n✓ Metrics saved to: {filepath}")
            
        except Exception as e:
            raise IOError(f"Failed to save metrics to CSV: {str(e)}")
    
    @staticmethod
    def compare_metrics(
        metrics_list: List[PerformanceMetrics],
        labels: List[str]
    ) -> None:
        """
        Compare multiple sets of metrics (useful for parameter tuning).
        
        Args:
            metrics_list: List of PerformanceMetrics objects
            labels: Labels for each metrics set
        """
        if len(metrics_list) != len(labels):
            raise ValueError("Number of metrics and labels must match")
        
        print("\n" + "=" * 90)
        print(f"{'METRICS COMPARISON':^90}")
        print("=" * 90)
        
        # Header
        header = f"{'Metric':<30}"
        for label in labels:
            header += f"{label:>15}"
        print(header)
        print("-" * 90)
        
        # Compare each metric
        metric_names = [
            ('Mean Position Error (m)', 'mean_position_error'),
            ('Max Position Error (m)', 'max_position_error'),
            ('Final Position Error (m)', 'final_position_error'),
            ('Mean Heading Error (°)', 'mean_heading_error'),
            ('Total Time (s)', 'total_simulation_time'),
            ('Path Efficiency (%)', 'path_efficiency'),
        ]
        
        for display_name, attr_name in metric_names:
            row = f"{display_name:<30}"
            for metrics in metrics_list:
                value = getattr(metrics, attr_name)
                row += f"{value:>15.4f}"
            print(row)
        
        print("=" * 90)
