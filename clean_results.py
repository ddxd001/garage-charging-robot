#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
                    清除仿真结果脚本
                    Clean Simulation Results
=============================================================================

本脚本用于一键清除所有仿真生成的结果文件，包括：
- results/ 目录下的所有文件
- 根目录下的临时结果文件
- Python 缓存文件

使用方法：
    python clean_results.py

选项：
    --all       清除所有内容（包括 results 目录）
    --cache     只清除 Python 缓存
    --results   只清除 results 目录（默认）

=============================================================================
"""

import os
import shutil
import sys
from pathlib import Path
from datetime import datetime


def print_header():
    """打印脚本标题"""
    print("\n" + "=" * 80)
    print("║" + " " * 78 + "║")
    print("║" + "清除仿真结果脚本".center(76) + "║")
    print("║" + "Clean Simulation Results".center(76) + "║")
    print("║" + " " * 78 + "║")
    print("=" * 80)
    print(f"║ 运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".ljust(79) + "║")
    print("=" * 80 + "\n")


def get_file_size(path: Path) -> int:
    """获取文件或目录的大小（字节）"""
    if path.is_file():
        return path.stat().st_size
    elif path.is_dir():
        total = 0
        for item in path.rglob('*'):
            if item.is_file():
                total += item.stat().st_size
        return total
    return 0


def format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def clean_results_directory():
    """清除 results 目录下的所有文件"""
    results_dir = Path("results")
    
    if not results_dir.exists():
        print("  ℹ️  results/ 目录不存在，无需清理")
        return 0
    
    total_size = get_file_size(results_dir)
    file_count = sum(1 for _ in results_dir.rglob('*') if _.is_file())
    
    if file_count == 0:
        print("  ℹ️  results/ 目录为空，无需清理")
        return 0
    
    print(f"  📊 发现 {file_count} 个文件，总大小 {format_size(total_size)}")
    
    # 删除所有子目录和文件
    for item in results_dir.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
            print(f"  🗑️  删除目录: {item.name}/")
        elif item.is_file():
            item.unlink()
            print(f"  🗑️  删除文件: {item.name}")
    
    # 重新创建子目录结构
    (results_dir / "figures").mkdir(exist_ok=True)
    (results_dir / "data").mkdir(exist_ok=True)
    (results_dir / "logs").mkdir(exist_ok=True)
    
    print(f"  ✅ 已清理 results/ 目录")
    print(f"  ✅ 已重建目录结构: figures/, data/, logs/")
    
    return total_size


def clean_root_results():
    """清除根目录下的结果文件"""
    root_dir = Path(".")
    
    # 需要清除的文件模式
    patterns = [
        "*.png",
        "*.csv",
        "*_metrics.csv",
        "*_results.png",
        "*_simulation.png",
        "*_analysis.png",
        "*_comparison.png",
    ]
    
    cleaned_files = []
    total_size = 0
    
    for pattern in patterns:
        for file in root_dir.glob(pattern):
            if file.is_file():
                size = file.stat().st_size
                total_size += size
                cleaned_files.append((file.name, size))
                file.unlink()
    
    if cleaned_files:
        print(f"  📊 在根目录发现 {len(cleaned_files)} 个结果文件")
        for filename, size in cleaned_files:
            print(f"  🗑️  删除: {filename} ({format_size(size)})")
        print(f"  ✅ 已清理根目录结果文件")
    else:
        print("  ℹ️  根目录无结果文件，无需清理")
    
    return total_size


def clean_python_cache():
    """清除 Python 缓存文件"""
    cache_dirs = []
    cache_files = []
    total_size = 0
    
    # 查找 __pycache__ 目录
    for pycache in Path(".").rglob("__pycache__"):
        if pycache.is_dir():
            size = get_file_size(pycache)
            total_size += size
            cache_dirs.append((pycache, size))
    
    # 查找 .pyc 文件
    for pyc in Path(".").rglob("*.pyc"):
        if pyc.is_file():
            size = pyc.stat().st_size
            total_size += size
            cache_files.append((pyc, size))
    
    if cache_dirs or cache_files:
        print(f"  📊 发现 {len(cache_dirs)} 个缓存目录，{len(cache_files)} 个 .pyc 文件")
        
        for cache_dir, size in cache_dirs:
            shutil.rmtree(cache_dir)
            print(f"  🗑️  删除缓存目录: {cache_dir}")
        
        for cache_file, size in cache_files:
            cache_file.unlink()
            print(f"  🗑️  删除缓存文件: {cache_file}")
        
        print(f"  ✅ 已清理 Python 缓存 ({format_size(total_size)})")
    else:
        print("  ℹ️  无 Python 缓存，无需清理")
    
    return total_size


def main():
    """主函数"""
    print_header()
    
    # 解析命令行参数
    args = sys.argv[1:]
    
    clean_all = "--all" in args
    clean_cache_only = "--cache" in args
    clean_results_only = "--results" in args or len(args) == 0
    
    total_cleaned = 0
    
    # 1. 清除 results 目录
    if clean_all or clean_results_only:
        print("▶ 步骤 1: 清除 results/ 目录")
        print("─" * 80)
        size = clean_results_directory()
        total_cleaned += size
        print()
    
    # 2. 清除根目录结果文件
    if clean_all or clean_results_only:
        print("▶ 步骤 2: 清除根目录结果文件")
        print("─" * 80)
        size = clean_root_results()
        total_cleaned += size
        print()
    
    # 3. 清除 Python 缓存
    if clean_all or clean_cache_only:
        print("▶ 步骤 3: 清除 Python 缓存")
        print("─" * 80)
        size = clean_python_cache()
        total_cleaned += size
        print()
    
    # 打印总结
    print("=" * 80)
    print("║" + " " * 78 + "║")
    print("║" + "清理完成！".center(76) + "║")
    print("║" + " " * 78 + "║")
    print("=" * 80)
    
    print(f"\n📊 清理统计:")
    print(f"  • 总共释放空间: {format_size(total_cleaned)}")
    
    print(f"\n💡 提示:")
    print(f"  • 运行仿真将自动创建新的结果文件")
    print(f"  • results/ 目录结构已保留")
    
    print(f"\n🚀 下一步:")
    print(f"  • 运行演示: python run_demo.py")
    print(f"  • 参数实验: python run_experiment.py")
    print(f"  • 状态机演示: python run_with_state_machine.py")
    
    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  清理被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 清理失败: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
