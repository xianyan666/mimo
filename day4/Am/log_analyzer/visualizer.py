"""可视化模块：生成三种图表。"""

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

from .utils import CHARTS_DIR, ensure_dir, get_chinese_font

FONT_NAME = get_chinese_font()
plt.rcParams['font.sans-serif'] = [FONT_NAME]
plt.rcParams['axes.unicode_minus'] = False


def plot_daily_error_trend(daily: pd.DataFrame, save_dir: str | None = None) -> str:
    """每日 Error 数量趋势折线图。返回保存路径。"""
    save_dir = save_dir or CHARTS_DIR
    ensure_dir(save_dir)
    path = os.path.join(save_dir, 'daily_error_trend.png')

    fig, ax = plt.subplots(figsize=(12, 6))
    dates = pd.to_datetime(daily['date'])
    ax.plot(dates, daily['error_count'], color='#2196F3', linewidth=1.2)
    ax.fill_between(dates, daily['error_count'], alpha=0.15, color='#2196F3')
    ax.set_title('Apache 每日 Error 数量趋势', fontsize=14, fontweight='bold')
    ax.set_xlabel('日期', fontsize=11)
    ax.set_ylabel('Error 数量', fontsize=11)
    ax.tick_params(axis='x', rotation=45)
    ax.grid(axis='y', alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_error_code_pie(code_stats: pd.DataFrame, top_n: int = 8, save_dir: str | None = None) -> str:
    """错误码占比饼图（Top N，其余合并为"其他"）。返回保存路径。"""
    save_dir = save_dir or CHARTS_DIR
    ensure_dir(save_dir)
    path = os.path.join(save_dir, 'error_code_pie.png')

    top = code_stats.head(top_n).copy()
    rest = code_stats.iloc[top_n:]
    if len(rest) > 0:
        other_row = pd.DataFrame({
            'error_code': ['其他'],
            'count': [rest['count'].sum()],
        })
        top = pd.concat([top[['error_code', 'count']], other_row], ignore_index=True)

    colors = ['#E53935', '#1E88E5', '#43A047', '#FB8C00', '#8E24AA',
              '#00ACC1', '#F4511E', '#6D4C41', '#757575'][:len(top)]

    fig, ax = plt.subplots(figsize=(8, 8))
    wedges, texts, autotexts = ax.pie(
        top['count'], labels=top['error_code'], autopct='%1.1f%%',
        colors=colors, startangle=140, pctdistance=0.8,
        textprops={'fontsize': 9},
    )
    for t in autotexts:
        t.set_fontsize(8)
    ax.set_title('Error 错误码占比分布', fontsize=14, fontweight='bold')
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_module_error_bar(module_stats: pd.DataFrame, save_dir: str | None = None) -> str:
    """各模块 Error 数量柱状图（带数值标签）。返回保存路径。"""
    save_dir = save_dir or CHARTS_DIR
    ensure_dir(save_dir)
    path = os.path.join(save_dir, 'module_error_bar.png')

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(
        module_stats['module'], module_stats['error_count'],
        color=['#E53935', '#1E88E5', '#43A047', '#FB8C00', '#8E24AA', '#00ACC1'],
        edgecolor='white', linewidth=0.5,
    )
    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + 50,
                f'{int(h):,}', ha='center', va='bottom', fontsize=9)
    ax.set_title('各模块 Error 数量对比', fontsize=14, fontweight='bold')
    ax.set_xlabel('模块', fontsize=11)
    ax.set_ylabel('Error 数量', fontsize=11)
    ax.grid(axis='y', alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path
