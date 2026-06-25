# 408考研学习助手

一个基于CLI的408考研学习助手，帮助你记录、跟踪和分析学习进度。

## 功能特性

- **submit** - 提交学习记录（交互式输入）
- **today** - 查看今日学习记录
- **check** - 查看整体学习进度
- **review** - 生成阶段性复盘报告
- **config** - 管理配置

## 快速开始

```bash
# 查看帮助
python cli.py --help

# 提交学习记录
python cli.py submit

# 查看今日记录
python cli.py today

# 查看整体进度
python cli.py check

# 生成复盘报告
python cli.py review

# 查看配置
python cli.py config
```

## 学习指标

系统会自动计算以下指标：

1. **总学习时长** - 累计学习小时数
2. **连续学习天数** - 最近连续提交记录的天数
3. **科目占比** - 各科目学习时长百分比
4. **章节覆盖率** - 已学习章节/总章节
5. **高频疑问** - 出现次数最多的问题
6. **薄弱知识点** - WeaknessScore ≥ 8的知识点
7. **遗忘风险** - 超过7天未复习的内容
8. **冲刺预测** - 基于当前进度的完成预测

## WeaknessScore算法

采用多因素评分机制识别薄弱知识点：

```
Score = (2.0 × 提问次数) + (1.5 × 重复次数) + (1.0 × (5-自评)) + (0.5 × 未复习天数)
```

- Score < 4：掌握良好
- 4 ≤ Score < 8：需要关注
- Score ≥ 8：薄弱知识点

## 配置管理

```bash
# 查看配置
python cli.py config

# 修改配置
python cli.py config --set user.name 张三
python cli.py config --set user.target_date 2025-12-21
python cli.py config --set user.daily_goal_hours 4
python cli.py config --set thresholds.weakness_score 8
python cli.py config --set thresholds.forget_days 7
```

## 数据存储

- 学习记录：`data/memory.json`
- 配置文件：`data/config.json`

## 系统要求

- Python 3.11+
- 无额外依赖（使用Python标准库）
