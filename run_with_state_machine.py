#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
带状态机的车库充电机器人仿真脚本

本脚本启用状态机运行仿真，演示完整的充电任务流程和状态转换。

功能：
    - 模拟完整的充电任务流程（IDLE -> MOVE_TO_TARGET -> ALIGN_TO_DOCK -> DOCKED -> FINISHED）
    - 记录详细的状态转换日志
    - 生成带状态标注的可视化图表
    - 计算各状态的停留时间

使用方法：
    python run_with_state_machine.py

输出文件：
    - results/figures/state_machine_simulation_*.png  # 状态机仿真图表
    - results/data/state_machine_metrics_*.csv        # 性能指标数据
    - results/figures/latest_state_machine.png        # 最新结果链接
    - results/data/latest_state_machine.csv           # 最新数据链接

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
from src.simulator import Simulator
from src.plotting import ResultVisualizer


def main() -> int:
    """
    Main function to run simulation with state machine.
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    try:
        print("\n" + "=" * 70)
        print("GARAGE CHARGING ROBOT SIMULATION")
        print("Mode: State Machine Enabled")
        print("=" * 70)
        
        # Create configuration
        print("\nInitializing simulation configuration...")
        config = SimulationConfig()
        
        # Print configuration summary
        print(config.summary())
        
        # Create results directories
        results_dir = Path("results")
        data_dir = results_dir / "data"
        figures_dir = results_dir / "figures"
        data_dir.mkdir(parents=True, exist_ok=True)
        figures_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create simulator with state machine enabled
        print("Creating simulator with state machine...")
        simulator = Simulator(config, use_state_machine=True)
        
        # Run simulation
        print("\nRunning simulation with state machine...\n")
        data = simulator.run(verbose=True)
        
        # Print performance metrics
        print("\n" + "=" * 70)
        print("PERFORMANCE METRICS")
        print("=" * 70)
        simulator.print_performance_summary()
        
        # Save metrics to CSV
        csv_filename = data_dir / f"state_machine_metrics_{timestamp}.csv"
        simulator.save_metrics_to_csv(str(csv_filename))
        
        # Generate visualization with state annotations
        plot_filename = figures_dir / f"state_machine_simulation_{timestamp}.png"
        print(f"\nCreating plot with state annotations: {plot_filename}")
        ResultVisualizer.plot_results(
            sim=simulator,
            save_path=str(plot_filename),
            show=config.show_plot,
            dpi=config.plot_dpi
        )
        
        # Create symbolic links to latest results
        latest_csv = data_dir / "latest_state_machine.csv"
        latest_plot = figures_dir / "latest_state_machine.png"
        
        try:
            if latest_csv.exists():
                latest_csv.unlink()
            if latest_plot.exists():
                latest_plot.unlink()
            
            os.symlink(csv_filename.name, latest_csv)
            os.symlink(plot_filename.name, latest_plot)
        except Exception:
            pass  # Ignore symlink errors on Windows
        
        # Print final summary
        print("\n" + "=" * 70)
        print("SIMULATION SUMMARY")
        print("=" * 70)
        
        metrics = simulator.get_performance_metrics()
        state_machine = simulator.get_state_machine()
        
        if metrics:
            print(f"\n📊 Performance:")
            print(f"  • Task completion:            {'✓ Success' if metrics.goal_reached else '✗ Failed'}")
            print(f"  • Total time:                 {metrics.total_simulation_time:.2f} s")
            print(f"  • Mean position error:        {metrics.mean_position_error:.4f} m")
            print(f"  • Final position error:       {metrics.final_position_error:.4f} m")
        
        if state_machine:
            print(f"\n🔄 State Machine:")
            print(f"  • Final state:                {state_machine.get_state_name()}")
            print(f"  • Total transitions:          {len(state_machine.state_history)}")
            
            # Print state durations
            durations = state_machine.get_state_durations()
            print(f"\n⏱️  Time in Each State:")
            for state_name, duration in durations.items():
                if duration > 0:
                    print(f"  • {state_name:<20} {duration:6.2f} s")
        
        print(f"\n📁 Generated Files:")
        print(f"  • Visualization:              {plot_filename}")
        print(f"  • Performance metrics:        {csv_filename}")
        print(f"  • Latest plot link:           results/figures/latest_state_machine.png")
        print(f"  • Latest CSV link:            results/data/latest_state_machine.csv")
        
        print("\n" + "=" * 70)
        print("✓ Simulation with state machine completed successfully!")
        print("=" * 70 + "\n")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\nSimulation interrupted by user.")
        return 1
        
    except Exception as e:
        print(f"\n✗ Simulation failed with error:")
        print(f"  {type(e).__name__}: {str(e)}")
        
        # Print traceback for debugging
        import traceback
        print("\nTraceback:")
        traceback.print_exc()
        
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
