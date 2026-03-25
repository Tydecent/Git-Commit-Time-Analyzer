#!/usr/bin/env python3
"""
统计 Git 仓库的平均提交时间
用法：在 Git 仓库目录下运行 python git_commit_time_stats.py
"""

import subprocess
import sys
from datetime import datetime
from collections import Counter

def get_commit_times(repo_path='.'):
    """通过 git log 获取所有提交的时间（小时）"""
    try:
        # 获取所有提交的时间戳（ISO 8601 格式，包含时区）
        result = subprocess.run(
            ['git', 'log', '--pretty=format:%aI'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        print("错误：无法读取 Git 日志。请确保在 Git 仓库中运行此脚本。")
        print(e.stderr)
        sys.exit(1)

    if not result.stdout:
        print("没有找到任何提交记录。")
        return []

    times = []
    for line in result.stdout.strip().split('\n'):
        if line:
            # 解析 ISO 8601 时间，例如：2023-12-01T23:45:30+08:00
            # 我们需要提取小时，并转换为本地时区（或者就按 UTC+8 理解）
            # 这里我们提取的是提交者在提交时所处的本地时间的小时（根据时区字段）
            try:
                # 使用 Python 的 datetime.fromisoformat 解析
                dt = datetime.fromisoformat(line)
                # 提取小时（0-23）
                hour = dt.hour
                times.append(hour)
            except ValueError as e:
                print(f"警告：无法解析时间戳: {line}, 错误: {e}")
                continue

    return times

def calculate_stats(hours):
    """计算平均小时和中位数等统计信息"""
    if not hours:
        return None

    # 计算平均小时（考虑圆形平均值，因为 23 点和 0 点实际上是相邻的）
    # 简单平均对于跨午夜的情况会有偏差，但对于大多数场景足够
    avg_hour = sum(hours) / len(hours)

    # 更科学的圆形平均值计算（可选）
    # 将小时转换为角度，然后平均，再转回小时
    import math
    sin_sum = sum(math.sin(2 * math.pi * h / 24) for h in hours)
    cos_sum = sum(math.cos(2 * math.pi * h / 24) for h in hours)
    circular_avg = (math.atan2(sin_sum, cos_sum) % (2 * math.pi)) * 24 / (2 * math.pi)

    # 中位数
    sorted_hours = sorted(hours)
    median = sorted_hours[len(sorted_hours)//2]

    return {
        'total_commits': len(hours),
        'simple_average': avg_hour,
        'circular_average': circular_avg,
        'median': median,
        'min_hour': min(hours),
        'max_hour': max(hours)
    }

def print_stats(stats):
    """打印统计结果"""
    print("\n=== Git 提交时间统计 ===")
    print(f"总提交数: {stats['total_commits']}")
    print(f"提交时间分布（小时，0-23）:")
    print(f"  简单平均: {stats['simple_average']:.2f} 时")
    print(f"  圆形平均: {stats['circular_average']:.2f} 时")
    print(f"  中位数: {stats['median']} 时")
    print(f"  最早提交: {stats['min_hour']:02d}:00")
    print(f"  最晚提交: {stats['max_hour']:02d}:00")

def plot_distribution(hours):
    """可选：画出提交时间分布直方图"""
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("\n未安装 matplotlib，跳过绘图。如需图表，请运行: pip install matplotlib")
        return

    # 统计每个小时的数量
    counter = Counter(hours)
    all_hours = list(range(24))
    counts = [counter.get(h, 0) for h in all_hours]

    plt.figure(figsize=(10, 5))
    bars = plt.bar(all_hours, counts, width=0.8, color='skyblue', edgecolor='navy')
    plt.xticks(all_hours)
    plt.xlabel('小时（24小时制）')
    plt.ylabel('提交次数')
    plt.title('Git 提交时间分布')
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    # 标注平均时间
    avg_hour = stats['circular_average']
    plt.axvline(x=avg_hour, color='red', linestyle='--', linewidth=1.5, label=f'平均时间: {avg_hour:.1f}时')
    plt.legend()

if __name__ == '__main__':
    # 获取当前目录的 Git 提交时间
    print("正在读取 Git 提交记录...")
    hours = get_commit_times()

    if not hours:
        print("没有找到提交记录。")
        sys.exit(0)

    stats = calculate_stats(hours)
    print_stats(stats)

    # 询问是否绘图
    try:
        answer = input("\n是否显示分布图？(y/n): ").strip().lower()
        if answer == 'y':
            plot_distribution(hours)
    except KeyboardInterrupt:
        print("\n已取消。")