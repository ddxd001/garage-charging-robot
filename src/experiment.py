#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
参数对比实验模块

本模块实现了自动化的参数对比实验框架，用于：
- 测试不同控制参数组合的性能
- 自动生成对比图表和数据
- 智能推荐最优参数配置

实验流程：
    1. 定义多组参数配置
    2. 批量运行仿真
    3. 收集性能指标
    4. 对比分析并推荐最优参数

作者：车库机器人团队
版本：1.3.0
日期：2026-03
"""

import numpy as np
import matplotlib.pyplot as plt
import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

from .config import SimulationConfig
from .simulator import Simulator
from .metrics import PerformanceMetrics


@dataclass
class ParameterSet:
    """
    Container for a set of control parameters to test.
    
    Attributes:
        name: Descriptive name for this parameter set
        position_gain: Position control gain
        heading_gain: Heading control gain
        look_ahead_distance: Look-ahead distance (m)
        description: Optional description of the parameter set
    """
    name: str
    position_gain: float
    heading_gain: float
    look_ahead_distance: float
    description: str = ""


class ParameterComparisonExperiment:
    """
    Framework for running parameter comparison experiments.
    
    Automates the process of testing multiple parameter configurations,
    collecting results, and generating comparison visualizations.
    """
    
    def __init__(self, base_config: Optional[SimulationConfig] = None):
        """
        Initialize the experiment framework.
        
        Args:
            base_config: Base configuration (will be copied and modified for each test)
                        If None, uses default configuration
        """
        self.base_config = base_config if base_config else SimulationConfig()
        self.parameter_sets: List[ParameterSet] = []
        self.results: List[Tuple[ParameterSet, PerformanceMetrics]] = []
    
    def add_parameter_set(self, param_set: ParameterSet) -> None:
        """
        Add a parameter set to test.
        
        Args:
            param_set: Parameter configuration to test
        """
        self.parameter_sets.append(param_set)
    
    def add_predefined_sets(self) -> None:
        """
        Add predefined parameter sets for comparison.
        
        These sets represent different control strategies:
        1. Conservative: Low gains, large look-ahead (smooth but slower)
        2. Balanced: Medium gains, medium look-ahead (default)
        3. Aggressive: High gains, small look-ahead (fast but may oscillate)
        4. Precision: Medium-high gains, small look-ahead (accurate positioning)
        5. Smooth: Low position gain, high heading gain (smooth turns)
        """
        predefined_sets = [
            ParameterSet(
                name="Conservative",
                position_gain=1.0,
                heading_gain=1.5,
                look_ahead_distance=1.2,
                description="Low gains, large look-ahead - smooth but slower response"
            ),
            ParameterSet(
                name="Balanced",
                position_gain=1.5,
                heading_gain=2.0,
                look_ahead_distance=0.8,
                description="Default balanced parameters - good overall performance"
            ),
            ParameterSet(
                name="Aggressive",
                position_gain=2.5,
                heading_gain=3.0,
                look_ahead_distance=0.5,
                description="High gains, small look-ahead - fast but may oscillate"
            ),
            ParameterSet(
                name="Precision",
                position_gain=2.0,
                heading_gain=2.5,
                look_ahead_distance=0.6,
                description="Medium-high gains - optimized for positioning accuracy"
            ),
            ParameterSet(
                name="Smooth",
                position_gain=1.2,
                heading_gain=2.5,
                look_ahead_distance=1.0,
                description="Low position gain, high heading - smooth trajectory"
            ),
        ]
        
        for param_set in predefined_sets:
            self.add_parameter_set(param_set)
    
    def run_experiment(self, verbose: bool = True) -> List[Tuple[ParameterSet, PerformanceMetrics]]:
        """
        Run the parameter comparison experiment.
        
        Tests each parameter set and collects performance metrics.
        
        Args:
            verbose: Whether to print progress information
            
        Returns:
            List of (ParameterSet, PerformanceMetrics) tuples
            
        Raises:
            ValueError: If no parameter sets have been added
        """
        if not self.parameter_sets:
            raise ValueError("No parameter sets added. Use add_parameter_set() or add_predefined_sets()")
        
        self.results = []
        
        if verbose:
            print("\n" + "=" * 70)
            print("PARAMETER COMPARISON EXPERIMENT")
            print("=" * 70)
            print(f"Testing {len(self.parameter_sets)} parameter configurations...")
            print(f"Base path type: {self.base_config.path_type}")
            print("=" * 70 + "\n")
        
        for i, param_set in enumerate(self.parameter_sets, 1):
            if verbose:
                print(f"\n[{i}/{len(self.parameter_sets)}] Testing: {param_set.name}")
                print(f"  Position gain: {param_set.position_gain}")
                print(f"  Heading gain: {param_set.heading_gain}")
                print(f"  Look-ahead distance: {param_set.look_ahead_distance} m")
                if param_set.description:
                    print(f"  Description: {param_set.description}")
                print("-" * 70)
            
            # Create modified configuration
            config = SimulationConfig()
            config.position_gain = param_set.position_gain
            config.heading_gain = param_set.heading_gain
            config.look_ahead_distance = param_set.look_ahead_distance
            
            # Copy other settings from base config
            config.dt = self.base_config.dt
            config.total_time = self.base_config.total_time
            config.path_type = self.base_config.path_type
            config.max_linear_vel = self.base_config.max_linear_vel
            config.max_angular_vel = self.base_config.max_angular_vel
            
            # Run simulation
            try:
                simulator = Simulator(config)
                simulator.run(verbose=False)  # Suppress individual run output
                
                metrics = simulator.get_performance_metrics()
                if metrics is None:
                    raise RuntimeError("Metrics not calculated")
                
                self.results.append((param_set, metrics))
                
                if verbose:
                    print(f"  ✓ Complete - Mean error: {metrics.mean_position_error:.4f} m, "
                          f"Max error: {metrics.max_position_error:.4f} m, "
                          f"Final error: {metrics.final_position_error:.4f} m")
                
            except Exception as e:
                if verbose:
                    print(f"  ✗ Failed: {str(e)}")
                # Continue with other parameter sets
                continue
        
        if verbose:
            print("\n" + "=" * 70)
            print(f"Experiment complete! Tested {len(self.results)}/{len(self.parameter_sets)} configurations")
            print("=" * 70)
        
        return self.results
    
    def print_comparison_table(self) -> None:
        """Print a formatted comparison table of all results."""
        if not self.results:
            print("No results available. Run experiment first.")
            return
        
        print("\n" + "=" * 100)
        print("PARAMETER COMPARISON RESULTS")
        print("=" * 100)
        
        # Header
        header = f"{'Parameter Set':<15} {'Pos Gain':<10} {'Head Gain':<10} {'Look-Ahead':<12} "
        header += f"{'Mean Err':<12} {'Max Err':<12} {'Final Err':<12} {'Goal':<6}"
        print(header)
        print("-" * 100)
        
        # Data rows
        for param_set, metrics in self.results:
            row = f"{param_set.name:<15} "
            row += f"{param_set.position_gain:<10.2f} "
            row += f"{param_set.heading_gain:<10.2f} "
            row += f"{param_set.look_ahead_distance:<12.2f} "
            row += f"{metrics.mean_position_error:<12.4f} "
            row += f"{metrics.max_position_error:<12.4f} "
            row += f"{metrics.final_position_error:<12.4f} "
            row += f"{'✓' if metrics.goal_reached else '✗':<6}"
            print(row)
        
        print("=" * 100)
        
        # Find best performers
        self._print_best_performers()
    
    def _print_best_performers(self) -> None:
        """Print the best performing parameter sets for different metrics."""
        if not self.results:
            return
        
        print("\n🏆 BEST PERFORMERS:")
        
        # Best mean error
        best_mean = min(self.results, key=lambda x: x[1].mean_position_error)
        print(f"  • Lowest mean error:      {best_mean[0].name} ({best_mean[1].mean_position_error:.4f} m)")
        
        # Best max error
        best_max = min(self.results, key=lambda x: x[1].max_position_error)
        print(f"  • Lowest max error:       {best_max[0].name} ({best_max[1].max_position_error:.4f} m)")
        
        # Best final error
        best_final = min(self.results, key=lambda x: x[1].final_position_error)
        print(f"  • Lowest final error:     {best_final[0].name} ({best_final[1].final_position_error:.4f} m)")
        
        # Best path efficiency
        best_efficiency = max(self.results, key=lambda x: x[1].path_efficiency)
        print(f"  • Best path efficiency:   {best_efficiency[0].name} ({best_efficiency[1].path_efficiency:.2f}%)")
        
        # Fastest completion
        best_time = min(self.results, key=lambda x: x[1].total_simulation_time)
        print(f"  • Fastest completion:     {best_time[0].name} ({best_time[1].total_simulation_time:.2f} s)")
    
    def plot_comparison(self, save_path: Optional[str] = None, show: bool = True) -> None:
        """
        Create comparison plots for all parameter sets.
        
        Args:
            save_path: Path to save the figure (optional)
            show: Whether to display the plot
        """
        if not self.results:
            print("No results to plot. Run experiment first.")
            return
        
        fig, axes = plt.subplots(2, 3, figsize=(18, 10))
        fig.suptitle('Parameter Comparison Results', fontsize=16, fontweight='bold')
        
        names = [ps.name for ps, _ in self.results]
        x_pos = np.arange(len(names))
        
        # 1. Mean Position Error
        ax1 = axes[0, 0]
        mean_errors = [m.mean_position_error for _, m in self.results]
        bars1 = ax1.bar(x_pos, mean_errors, color='skyblue', edgecolor='black')
        ax1.set_ylabel('Mean Position Error (m)', fontsize=11)
        ax1.set_title('Mean Position Error', fontweight='bold')
        ax1.set_xticks(x_pos)
        ax1.set_xticklabels(names, rotation=45, ha='right')
        ax1.grid(True, alpha=0.3, axis='y')
        self._add_value_labels(ax1, bars1)
        
        # 2. Max Position Error
        ax2 = axes[0, 1]
        max_errors = [m.max_position_error for _, m in self.results]
        bars2 = ax2.bar(x_pos, max_errors, color='lightcoral', edgecolor='black')
        ax2.set_ylabel('Max Position Error (m)', fontsize=11)
        ax2.set_title('Maximum Position Error', fontweight='bold')
        ax2.set_xticks(x_pos)
        ax2.set_xticklabels(names, rotation=45, ha='right')
        ax2.grid(True, alpha=0.3, axis='y')
        self._add_value_labels(ax2, bars2)
        
        # 3. Final Position Error
        ax3 = axes[0, 2]
        final_errors = [m.final_position_error for _, m in self.results]
        bars3 = ax3.bar(x_pos, final_errors, color='lightgreen', edgecolor='black')
        ax3.set_ylabel('Final Position Error (m)', fontsize=11)
        ax3.set_title('Final Position Error', fontweight='bold')
        ax3.set_xticks(x_pos)
        ax3.set_xticklabels(names, rotation=45, ha='right')
        ax3.grid(True, alpha=0.3, axis='y')
        self._add_value_labels(ax3, bars3)
        
        # 4. Path Efficiency
        ax4 = axes[1, 0]
        efficiencies = [m.path_efficiency for _, m in self.results]
        bars4 = ax4.bar(x_pos, efficiencies, color='gold', edgecolor='black')
        ax4.set_ylabel('Path Efficiency (%)', fontsize=11)
        ax4.set_title('Path Efficiency', fontweight='bold')
        ax4.set_xticks(x_pos)
        ax4.set_xticklabels(names, rotation=45, ha='right')
        ax4.axhline(y=100, color='r', linestyle='--', linewidth=1, alpha=0.5)
        ax4.grid(True, alpha=0.3, axis='y')
        self._add_value_labels(ax4, bars4, format_str='{:.1f}')
        
        # 5. Total Time
        ax5 = axes[1, 1]
        times = [m.total_simulation_time for _, m in self.results]
        bars5 = ax5.bar(x_pos, times, color='plum', edgecolor='black')
        ax5.set_ylabel('Total Time (s)', fontsize=11)
        ax5.set_title('Completion Time', fontweight='bold')
        ax5.set_xticks(x_pos)
        ax5.set_xticklabels(names, rotation=45, ha='right')
        ax5.grid(True, alpha=0.3, axis='y')
        self._add_value_labels(ax5, bars5, format_str='{:.1f}')
        
        # 6. Parameter Values
        ax6 = axes[1, 2]
        pos_gains = [ps.position_gain for ps, _ in self.results]
        head_gains = [ps.heading_gain for ps, _ in self.results]
        look_aheads = [ps.look_ahead_distance for ps, _ in self.results]
        
        width = 0.25
        ax6.bar(x_pos - width, pos_gains, width, label='Position Gain', color='steelblue')
        ax6.bar(x_pos, head_gains, width, label='Heading Gain', color='darkorange')
        ax6.bar(x_pos + width, look_aheads, width, label='Look-Ahead (m)', color='green')
        ax6.set_ylabel('Parameter Value', fontsize=11)
        ax6.set_title('Parameter Values', fontweight='bold')
        ax6.set_xticks(x_pos)
        ax6.set_xticklabels(names, rotation=45, ha='right')
        ax6.legend(fontsize=9)
        ax6.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"\n✓ Comparison plot saved to: {save_path}")
        
        if show:
            plt.show()
        else:
            plt.close(fig)
    
    def _add_value_labels(self, ax, bars, format_str: str = '{:.4f}') -> None:
        """Add value labels on top of bars."""
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   format_str.format(height),
                   ha='center', va='bottom', fontsize=8)
    
    def save_results_to_csv(self, filepath: str) -> None:
        """
        Save experiment results to CSV file.
        
        Args:
            filepath: Path to save CSV file
        """
        if not self.results:
            print("No results to save. Run experiment first.")
            return
        
        try:
            with open(filepath, 'w', newline='') as csvfile:
                fieldnames = [
                    'parameter_set', 'position_gain', 'heading_gain', 'look_ahead_distance',
                    'mean_position_error', 'max_position_error', 'final_position_error',
                    'steady_state_error', 'mean_heading_error', 'max_heading_error',
                    'total_simulation_time', 'settling_time', 'path_length',
                    'reference_path_length', 'path_efficiency', 'goal_reached'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for param_set, metrics in self.results:
                    row = {
                        'parameter_set': param_set.name,
                        'position_gain': param_set.position_gain,
                        'heading_gain': param_set.heading_gain,
                        'look_ahead_distance': param_set.look_ahead_distance,
                        'mean_position_error': metrics.mean_position_error,
                        'max_position_error': metrics.max_position_error,
                        'final_position_error': metrics.final_position_error,
                        'steady_state_error': metrics.steady_state_error,
                        'mean_heading_error': metrics.mean_heading_error,
                        'max_heading_error': metrics.max_heading_error,
                        'total_simulation_time': metrics.total_simulation_time,
                        'settling_time': metrics.settling_time,
                        'path_length': metrics.path_length,
                        'reference_path_length': metrics.reference_path_length,
                        'path_efficiency': metrics.path_efficiency,
                        'goal_reached': metrics.goal_reached,
                    }
                    writer.writerow(row)
            
            print(f"✓ Results saved to: {filepath}")
            
        except Exception as e:
            print(f"✗ Failed to save results: {str(e)}")
    
    def get_recommended_parameters(self) -> Tuple[ParameterSet, str]:
        """
        Analyze results and recommend the best parameter set.
        
        Returns:
            Tuple of (recommended ParameterSet, explanation string)
        """
        if not self.results:
            raise ValueError("No results available. Run experiment first.")
        
        # Score each parameter set based on multiple criteria
        scores = []
        
        for param_set, metrics in self.results:
            # Normalize metrics to 0-1 scale (lower is better for errors, higher for efficiency)
            all_mean_errors = [m.mean_position_error for _, m in self.results]
            all_max_errors = [m.max_position_error for _, m in self.results]
            all_final_errors = [m.final_position_error for _, m in self.results]
            all_efficiencies = [m.path_efficiency for _, m in self.results]
            
            # Calculate normalized scores (0-1, higher is better)
            mean_score = 1 - (metrics.mean_position_error - min(all_mean_errors)) / (max(all_mean_errors) - min(all_mean_errors) + 1e-6)
            max_score = 1 - (metrics.max_position_error - min(all_max_errors)) / (max(all_max_errors) - min(all_max_errors) + 1e-6)
            final_score = 1 - (metrics.final_position_error - min(all_final_errors)) / (max(all_final_errors) - min(all_final_errors) + 1e-6)
            efficiency_score = (metrics.path_efficiency - min(all_efficiencies)) / (max(all_efficiencies) - min(all_efficiencies) + 1e-6)
            
            # Weighted combination (prioritize mean error and final error)
            total_score = (
                0.35 * mean_score +      # Mean error (most important)
                0.20 * max_score +       # Max error
                0.30 * final_score +     # Final error (important for charging)
                0.15 * efficiency_score  # Path efficiency
            )
            
            scores.append((param_set, metrics, total_score))
        
        # Find best overall
        best = max(scores, key=lambda x: x[2])
        best_param, best_metrics, best_score = best
        
        # Generate explanation
        explanation = f"""
RECOMMENDED PARAMETERS: {best_param.name}
{'=' * 70}

Parameter Values:
  • Position Gain:          {best_param.position_gain}
  • Heading Gain:           {best_param.heading_gain}
  • Look-Ahead Distance:    {best_param.look_ahead_distance} m

Performance Metrics:
  • Mean Position Error:    {best_metrics.mean_position_error:.4f} m
  • Max Position Error:     {best_metrics.max_position_error:.4f} m
  • Final Position Error:   {best_metrics.final_position_error:.4f} m
  • Path Efficiency:        {best_metrics.path_efficiency:.2f} %
  • Total Time:             {best_metrics.total_simulation_time:.2f} s

Overall Score: {best_score:.3f} / 1.000

Recommendation Rationale:
{best_param.description}

This parameter set achieved the best overall balance across all metrics,
with particular strength in:
"""
        
        # Add specific strengths
        strengths = []
        if best_metrics.mean_position_error == min(m.mean_position_error for _, m in self.results):
            strengths.append("  ✓ Lowest mean tracking error")
        if best_metrics.max_position_error == min(m.max_position_error for _, m in self.results):
            strengths.append("  ✓ Lowest maximum error")
        if best_metrics.final_position_error == min(m.final_position_error for _, m in self.results):
            strengths.append("  ✓ Best final positioning accuracy")
        if best_metrics.path_efficiency == max(m.path_efficiency for _, m in self.results):
            strengths.append("  ✓ Highest path efficiency")
        
        if not strengths:
            strengths.append("  ✓ Well-balanced performance across all metrics")
        
        explanation += "\n".join(strengths)
        explanation += "\n" + "=" * 70
        
        return best_param, explanation
