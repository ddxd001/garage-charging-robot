#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
参数对比实验运行脚本

本脚本用于自动化运行参数对比实验，寻找全向轮机器人路径跟踪系统的最优控制参数。

功能：
    - 自动测试多组预定义的参数配置
    - 批量运行仿真并收集性能数据
    - 生成参数对比图表和CSV数据文件
    - 智能推荐最优参数组合

使用方法：
    python run_experiment.py

输出文件：
    - results/figures/parameter_comparison_*.png  # 对比图表
    - results/data/parameter_comparison_*.csv     # 性能数据
    - results/figures/latest_comparison.png       # 最新结果链接
    - results/data/latest_comparison.csv          # 最新数据链接

作者：车库机器人团队
版本：1.3.0
日期：2026-03
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import SimulationConfig
from src.experiment import ParameterComparisonExperiment, ParameterSet


def main() -> int:
    """
    Main function to run parameter comparison experiments.
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    try:
        print("\n" + "=" * 70)
        print("PARAMETER COMPARISON EXPERIMENT")
        print("Omni-Directional Robot Path Tracking Control")
        print("=" * 70)
        
        # Create base configuration
        base_config = SimulationConfig()
        base_config.show_plot = False  # Don't show individual plots
        
        # Create experiment framework
        experiment = ParameterComparisonExperiment(base_config)
        
        # Add predefined parameter sets
        print("\nAdding predefined parameter sets...")
        experiment.add_predefined_sets()
        print(f"✓ Added {len(experiment.parameter_sets)} parameter configurations")
        
        # You can also add custom parameter sets
        # experiment.add_parameter_set(ParameterSet(
        #     name="Custom",
        #     position_gain=1.8,
        #     heading_gain=2.2,
        #     look_ahead_distance=0.7,
        #     description="Custom tuned parameters"
        # ))
        
        # Run the experiment
        print("\nStarting experiment...")
        results = experiment.run_experiment(verbose=True)
        
        if not results:
            print("\n✗ No results obtained. Experiment failed.")
            return 1
        
        # Print comparison table
        experiment.print_comparison_table()
        
        # Get and print recommendation
        print("\n" + "=" * 70)
        print("ANALYZING RESULTS...")
        print("=" * 70)
        
        recommended_params, explanation = experiment.get_recommended_parameters()
        print(explanation)
        
        # Create results directories
        results_dir = Path("results")
        data_dir = results_dir / "data"
        figures_dir = results_dir / "figures"
        data_dir.mkdir(parents=True, exist_ok=True)
        figures_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save results to CSV
        csv_filename = data_dir / f"parameter_comparison_{timestamp}.csv"
        experiment.save_results_to_csv(str(csv_filename))
        
        # Generate comparison plots
        print("\nGenerating comparison visualizations...")
        plot_filename = figures_dir / f"parameter_comparison_{timestamp}.png"
        experiment.plot_comparison(save_path=str(plot_filename), show=False)
        
        # Create symbolic links to latest results
        latest_csv = data_dir / "latest_comparison.csv"
        latest_plot = figures_dir / "latest_comparison.png"
        
        try:
            if latest_csv.exists():
                latest_csv.unlink()
            if latest_plot.exists():
                latest_plot.unlink()
            
            os.symlink(csv_filename.name, latest_csv)
            os.symlink(plot_filename.name, latest_plot)
        except Exception:
            pass  # Ignore symlink errors on Windows
        
        # Final summary
        print("\n" + "=" * 70)
        print("EXPERIMENT COMPLETE")
        print("=" * 70)
        print(f"\n📊 Results Summary:")
        print(f"  • Configurations tested:  {len(results)}")
        print(f"  • Recommended setting:    {recommended_params.name}")
        print(f"\n📁 Generated Files:")
        print(f"  • Comparison plot:        {plot_filename}")
        print(f"  • Results CSV:            {csv_filename}")
        print(f"  • Latest plot link:       results/figures/latest_comparison.png")
        print(f"  • Latest CSV link:        results/data/latest_comparison.csv")
        print(f"\n💡 Next Steps:")
        print(f"  1. Review the comparison plot: results/figures/latest_comparison.png")
        print(f"  2. Update config.py with recommended parameters:")
        print(f"     - position_gain = {recommended_params.position_gain}")
        print(f"     - heading_gain = {recommended_params.heading_gain}")
        print(f"     - look_ahead_distance = {recommended_params.look_ahead_distance}")
        print(f"  3. Run main.py to verify performance with new parameters")
        
        print("\n" + "=" * 70)
        print("✓ Experiment completed successfully!")
        print("=" * 70 + "\n")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\nExperiment interrupted by user.")
        return 1
        
    except Exception as e:
        print(f"\n✗ Experiment failed with error:")
        print(f"  {type(e).__name__}: {str(e)}")
        
        # Print traceback for debugging
        import traceback
        print("\nTraceback:")
        traceback.print_exc()
        
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
