#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可视化模块

本模块负责生成仿真结果的可视化图表，包括：
- 路径跟踪轨迹图：参考路径 vs 实际轨迹
- 航向角变化图：时间序列
- 位置跟踪误差图：时间序列
- 车轮速度图：三个全向轮的角速度

图表特点：
    - 高分辨率输出，适合论文和PPT
    - 支持状态机标注(可选)
    - 中英文标注，专业美观

作者：车库机器人团队
版本：1.3.0
日期：2026-03
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Optional
from .simulator import SimulationData, Simulator


class ResultVisualizer:
    """Visualizer with state machine support."""
    
    @staticmethod
    def plot_results(
        sim: Simulator,
        save_path: Optional[str] = None,
        show: bool = True,
        dpi: int = 150
    ) -> None:
        """Create and display/save simulation result plots with state annotations."""
        if not isinstance(sim, Simulator):
            raise ValueError(f"sim must be a Simulator instance, got {type(sim)}")
        
        if not sim.data.time:
            raise ValueError("Simulator has no data. Run simulation first.")
        
        # Create figure
        fig = plt.figure(figsize=(15, 10))
        
        # Plot 1: Trajectory with state annotations
        ResultVisualizer._plot_trajectory(plt.subplot(2, 2, 1), sim)
        
        # Plot 2: Heading angle
        ResultVisualizer._plot_heading(plt.subplot(2, 2, 2), sim)
        
        # Plot 3: Tracking error with state zones
        ResultVisualizer._plot_error(plt.subplot(2, 2, 3), sim)
        
        # Plot 4: Wheel velocities
        ResultVisualizer._plot_wheel_velocities(plt.subplot(2, 2, 4), sim)
        
        plt.tight_layout()
        
        if save_path:
            try:
                plt.savefig(save_path, dpi=dpi, bbox_inches='tight')
                print(f"\n✓ Combined plot saved to: {save_path}")
            except Exception as e:
                print(f"Warning: Failed to save plot: {str(e)}")
        
        if show:
            plt.show()
        else:
            plt.close(fig)
    
    @staticmethod
    def _plot_trajectory(ax: plt.Axes, sim: Simulator) -> None:
        """Plot path tracking trajectory with state annotations."""
        # Plot reference path
        ax.plot(sim.path[:, 0], sim.path[:, 1], 'b--', 
                linewidth=2, label='Reference Path', alpha=0.7)
        
        # Plot actual trajectory with state-based coloring
        if sim.state_machine and sim.data.states:
            # Color trajectory by state
            state_colors = {
                'IDLE': 'gray',
                'MOVE_TO_TARGET': 'green',
                'ALIGN_TO_DOCK': 'orange',
                'DOCKED': 'red',
                'FINISHED': 'purple'
            }
            
            # Plot segments with different colors
            for i in range(len(sim.data.x) - 1):
                state = sim.data.states[i]
                color = state_colors.get(state, 'blue')
                ax.plot(sim.data.x[i:i+2], sim.data.y[i:i+2], 
                       color=color, linewidth=2, alpha=0.8)
            
            # Add state transition markers
            state_machine = sim.get_state_machine()
            if state_machine and state_machine.state_history:
                for transition in state_machine.state_history:
                    # Find closest data point to transition time
                    idx = min(range(len(sim.data.time)), 
                             key=lambda i: abs(sim.data.time[i] - transition.timestamp))
                    
                    ax.plot(sim.data.x[idx], sim.data.y[idx], 'r*', 
                           markersize=12, zorder=10)
                    ax.annotate(f'{transition.to_state.name}\n{transition.timestamp:.1f}s',
                              xy=(sim.data.x[idx], sim.data.y[idx]),
                              xytext=(10, 10), textcoords='offset points',
                              fontsize=8, bbox=dict(boxstyle='round,pad=0.3', 
                                                   facecolor='yellow', alpha=0.7),
                              arrowprops=dict(arrowstyle='->', color='red'))
        else:
            # Normal trajectory without states
            ax.plot(sim.data.x, sim.data.y, 'r-', linewidth=1.5, label='Actual Trajectory')
        
        # Mark start and goal
        ax.plot(sim.config.init_x, sim.config.init_y, 'go', 
                markersize=12, label='Start', zorder=5)
        ax.plot(sim.path[-1, 0], sim.path[-1, 1], 'r*', 
                markersize=15, label='Goal', zorder=5)
        
        # Draw heading arrows
        arrow_interval = max(1, len(sim.data.x) // 15)
        for i in range(0, len(sim.data.x), arrow_interval):
            dx = 0.3 * np.cos(sim.data.yaw[i])
            dy = 0.3 * np.sin(sim.data.yaw[i])
            ax.arrow(sim.data.x[i], sim.data.y[i], dx, dy,
                    head_width=0.15, head_length=0.1, 
                    fc='orange', ec='orange', alpha=0.6, zorder=4)
        
        ax.set_xlabel('X (m)', fontsize=12)
        ax.set_ylabel('Y (m)', fontsize=12)
        title = 'Path Tracking Trajectory'
        if sim.state_machine:
            title += ' (with State Transitions)'
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.legend(fontsize=9, loc='best')
        ax.grid(True, alpha=0.3)
        ax.axis('equal')
    
    @staticmethod
    def _plot_heading(ax: plt.Axes, sim: Simulator) -> None:
        """Plot heading angle over time."""
        yaw_degrees = np.degrees(sim.data.yaw)
        ax.plot(sim.data.time, yaw_degrees, 'b-', linewidth=1.5)
        
        # Add state transition markers
        if sim.state_machine:
            state_machine = sim.get_state_machine()
            if state_machine and state_machine.state_history:
                for transition in state_machine.state_history:
                    ax.axvline(x=transition.timestamp, color='r', 
                              linestyle='--', alpha=0.5, linewidth=1)
        
        ax.set_xlabel('Time (s)', fontsize=12)
        ax.set_ylabel('Heading Angle (deg)', fontsize=12)
        ax.set_title('Heading Angle vs Time', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
    
    @staticmethod
    def _plot_error(ax: plt.Axes, sim: Simulator) -> None:
        """Plot position tracking error with state zones."""
        ax.plot(sim.data.time, sim.data.tracking_error, 'r-', linewidth=1.5)
        
        mean_error = np.mean(sim.data.tracking_error)
        ax.axhline(y=mean_error, color='g', linestyle='--',
                  label=f'Mean: {mean_error:.3f} m')
        
        # Add state zones as background colors
        if sim.state_machine and sim.data.states:
            state_colors = {
                'IDLE': 'lightgray',
                'MOVE_TO_TARGET': 'lightgreen',
                'ALIGN_TO_DOCK': 'lightyellow',
                'DOCKED': 'lightcoral',
                'FINISHED': 'lavender'
            }
            
            # Find state change points
            current_state = sim.data.states[0]
            start_idx = 0
            
            for i in range(1, len(sim.data.states)):
                if sim.data.states[i] != current_state or i == len(sim.data.states) - 1:
                    # State changed, fill previous zone
                    end_idx = i if i < len(sim.data.states) - 1 else i
                    color = state_colors.get(current_state, 'white')
                    ax.axvspan(sim.data.time[start_idx], sim.data.time[end_idx], 
                              alpha=0.2, color=color)
                    
                    # Add state label
                    mid_time = (sim.data.time[start_idx] + sim.data.time[end_idx]) / 2
                    ax.text(mid_time, ax.get_ylim()[1] * 0.9, current_state,
                           ha='center', va='top', fontsize=8, 
                           bbox=dict(boxstyle='round,pad=0.3', facecolor=color, alpha=0.7))
                    
                    current_state = sim.data.states[i]
                    start_idx = i
        
        ax.set_xlabel('Time (s)', fontsize=12)
        ax.set_ylabel('Tracking Error (m)', fontsize=12)
        ax.set_title('Position Tracking Error', fontsize=14, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
    
    @staticmethod
    def _plot_wheel_velocities(ax: plt.Axes, sim: Simulator) -> None:
        """Plot wheel velocities over time."""
        wheel_vel_array = np.array(sim.data.wheel_velocities)
        
        ax.plot(sim.data.time, wheel_vel_array[:, 0], 'r-', 
                linewidth=1.5, label='Wheel 1 (0°)')
        ax.plot(sim.data.time, wheel_vel_array[:, 1], 'g-', 
                linewidth=1.5, label='Wheel 2 (120°)')
        ax.plot(sim.data.time, wheel_vel_array[:, 2], 'b-', 
                linewidth=1.5, label='Wheel 3 (240°)')
        
        # Add state transition markers
        if sim.state_machine:
            state_machine = sim.get_state_machine()
            if state_machine and state_machine.state_history:
                for transition in state_machine.state_history:
                    ax.axvline(x=transition.timestamp, color='k', 
                              linestyle='--', alpha=0.3, linewidth=1)
        
        ax.set_xlabel('Time (s)', fontsize=12)
        ax.set_ylabel('Wheel Angular Velocity (rad/s)', fontsize=12)
        ax.set_title('Wheel Velocities', fontsize=14, fontweight='bold')
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)
