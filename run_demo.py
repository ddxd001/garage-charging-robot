#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
        家庭车库智能充电机器人 - 路径跟踪控制仿真演示
        Garage Charging Robot - Path Tracking Control Simulation Demo
=============================================================================

本程序演示全向轮移动机器人在车库环境中的路径跟踪控制性能。

适用场景：
  - 大学生机器人竞赛
  - 控制算法课程设计
  - 移动机器人导航研究

作者：Garage Robot Team
版本：1.3.0
日期：2026-03-18

使用方法：
    python run_demo.py

输出文件：
    results/figures/    - 可视化图表（PNG格式，适合PPT）
    results/data/       - 性能指标数据（CSV格式）
    results/logs/       - 仿真日志文件

=============================================================================
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
from src.metrics import MetricsCalculator


def print_header():
    """打印程序标题"""
    print("\n" + "=" * 80)
    print("║" + " " * 78 + "║")
    print("║" + "家庭车库智能充电机器人 - 路径跟踪控制仿真演示".center(76) + "║")
    print("║" + "Garage Charging Robot - Path Tracking Control Demo".center(76) + "║")
    print("║" + " " * 78 + "║")
    print("=" * 80)
    print(f"║ 运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".ljust(79) + "║")
    print(f"║ 版本号: v1.3.0".ljust(79) + "║")
    print("=" * 80 + "\n")


def print_section(title: str):
    """打印章节标题"""
    print("\n" + "─" * 80)
    print(f"▶ {title}")
    print("─" * 80)


def print_config_summary(config: SimulationConfig):
    """打印配置摘要（适合截图）"""
    print_section("仿真配置参数")
    
    print("\n【机器人参数】")
    print(f"  • 底盘类型：三轮全向轮（正三角形布局）")
    print(f"  • 机器人半径：{config.robot_radius} m")
    print(f"  • 车轮半径：{config.wheel_radius} m")
    print(f"  • 最大线速度：{config.max_linear_vel} m/s")
    print(f"  • 最大角速度：{config.max_angular_vel} rad/s")
    
    print("\n【控制器参数】")
    print(f"  • 位置控制增益：{config.position_gain}")
    print(f"  • 航向控制增益：{config.heading_gain}")
    print(f"  • 前视距离：{config.look_ahead_distance} m")
    print(f"  • 到位阈值：{config.goal_threshold} m")
    
    print("\n【仿真参数】")
    print(f"  • 仿真步长：{config.dt} s")
    print(f"  • 仿真时长：{config.total_time} s")
    print(f"  • 路径类型：{config.path_type}")


def print_results_summary(metrics, goal_reached: bool):
    """打印结果摘要（适合截图）"""
    print_section("仿真结果摘要")
    
    print("\n【任务完成情况】")
    status = "✓ 成功完成" if goal_reached else "✗ 未完成"
    print(f"  • 任务状态：{status}")
    print(f"  • 总用时：{metrics.total_simulation_time:.2f} s")
    
    print("\n【位置跟踪性能】")
    print(f"  • 平均位置误差：{metrics.mean_position_error:.4f} m")
    print(f"  • 最大位置误差：{metrics.max_position_error:.4f} m")
    print(f"  • 最终到位误差：{metrics.final_position_error:.4f} m")
    print(f"  • 稳态误差：{metrics.steady_state_error:.4f} m")
    
    print("\n【航向跟踪性能】")
    print(f"  • 平均航向误差：{metrics.mean_heading_error:.2f}°")
    print(f"  • 最大航向误差：{metrics.max_heading_error:.2f}°")
    
    print("\n【路径效率】")
    print(f"  • 实际路径长度：{metrics.path_length:.2f} m")
    print(f"  • 参考路径长度：{metrics.reference_path_length:.2f} m")
    print(f"  • 路径效率：{metrics.path_efficiency:.2f}%")
    
    # 性能评级
    print("\n【性能评级】")
    if metrics.mean_position_error < 0.05:
        grade = "优秀 (A+)"
    elif metrics.mean_position_error < 0.08:
        grade = "良好 (A)"
    elif metrics.mean_position_error < 0.12:
        grade = "中等 (B)"
    else:
        grade = "需改进 (C)"
    print(f"  • 综合评级：{grade}")


def save_results(simulator, timestamp: str):
    """保存所有结果文件"""
    print_section("保存实验结果")
    
    results_dir = Path("results")
    figures_dir = results_dir / "figures"
    data_dir = results_dir / "data"
    
    # 确保目录存在
    figures_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存图表
    print("\n正在生成可视化图表...")
    figure_path = figures_dir / f"simulation_results_{timestamp}.png"
    ResultVisualizer.plot_results(
        sim=simulator,
        save_path=str(figure_path),
        show=False,
        dpi=300  # 高分辨率，适合PPT
    )
    print(f"  ✓ 主结果图已保存：{figure_path}")
    
    # 保存性能指标
    print("\n正在保存性能指标...")
    metrics_path = data_dir / f"performance_metrics_{timestamp}.csv"
    simulator.save_metrics_to_csv(str(metrics_path))
    print(f"  ✓ 性能指标已保存：{metrics_path}")
    
    # 创建最新结果的符号链接
    latest_figure = figures_dir / "latest_result.png"
    latest_metrics = data_dir / "latest_metrics.csv"
    
    try:
        if latest_figure.exists():
            latest_figure.unlink()
        if latest_metrics.exists():
            latest_metrics.unlink()
        
        # 创建相对路径的符号链接
        os.symlink(figure_path.name, latest_figure)
        os.symlink(metrics_path.name, latest_metrics)
        
        print(f"\n  ✓ 最新结果链接已更新")
        print(f"    - {latest_figure}")
        print(f"    - {latest_metrics}")
    except Exception as e:
        print(f"\n  ⚠ 创建符号链接失败：{e}")
    
    return figure_path, metrics_path


def main() -> int:
    """主函数"""
    try:
        # 打印标题
        print_header()
        
        # 生成时间戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 第一步：配置
        print_section("步骤 1/4：初始化仿真配置")
        config = SimulationConfig()
        print("✓ 配置加载完成")
        print_config_summary(config)
        
        # 第二步：运行仿真
        print_section("步骤 2/4：运行路径跟踪仿真")
        print("\n开始仿真...\n")
        
        simulator = Simulator(config, use_state_machine=False)
        simulator.run(verbose=False)  # 静默运行，避免过多输出
        
        print("\n✓ 仿真运行完成")
        
        # 第三步：分析结果
        print_section("步骤 3/4：分析仿真结果")
        metrics = simulator.get_performance_metrics()
        
        if metrics is None:
            print("✗ 性能指标计算失败")
            return 1
        
        print_results_summary(metrics, simulator.goal_reached)
        
        # 第四步：保存结果
        print_section("步骤 4/4：保存实验结果")
        figure_path, metrics_path = save_results(simulator, timestamp)
        
        # 最终总结
        print("\n" + "=" * 80)
        print("║" + " " * 78 + "║")
        print("║" + "实验完成！".center(76) + "║")
        print("║" + " " * 78 + "║")
        print("=" * 80)
        
        print("\n【生成的文件】")
        print(f"  1. 仿真结果图表：results/figures/latest_result.png")
        print(f"  2. 性能指标数据：results/data/latest_metrics.csv")
        
        print("\n【使用建议】")
        print("  • 图表可直接插入PPT（300 DPI高清）")
        print("  • CSV数据可用Excel打开分析")
        print("  • 控制台输出可截图用于汇报")
        
        print("\n【下一步】")
        print("  • 查看图表：open results/figures/latest_result.png")
        print("  • 参数对比实验：python run_experiment.py")
        print("  • 状态机演示：python run_with_state_machine.py")
        
        print("\n" + "=" * 80 + "\n")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n实验被用户中断")
        return 1
        
    except Exception as e:
        print(f"\n✗ 实验失败：{type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
