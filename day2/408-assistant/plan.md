# 408考研学习助手 - 架构设计文档

## 1. 模块划分

```
408-assistant/
│
├── cli.py                  # 入口层：命令行解析与调度
│
├── commands/               # 命令层：各命令实现
│   ├── __init__.py
│   ├── submit.py           # submit命令
│   ├── today.py            # today命令
│   ├── check.py            # check命令
│   ├── review.py           # review命令
│   └── config_cmd.py       # config命令
│
├── core/                   # 核心层：业务逻辑
│   ├── __init__.py
│   ├── record.py           # 记录管理
│   ├── analyzer.py         # 数据分析
│   ├── weakness.py         # 薄弱知识点计算
│   └── summary.py          # AI模拟总结
│
├── storage/                # 存储层：数据持久化
│   ├── __init__.py
│   ├── memory_store.py     # 学习记录存储
│   ├── config_store.py     # 配置存储
│   └── file_utils.py       # 文件工具函数
│
├── models/                 # 模型层：数据结构定义
│   ├── __init__.py
│   ├── record.py           # 学习记录模型
│   └── config.py           # 配置模型
│
└── data/                   # 数据目录
    ├── memory.json
    ├── today.json
    └── config.json
```

---

## 2. 模块职责

### 2.1 入口层 (cli.py)

- 解析命令行参数
- 调度对应命令模块
- 处理全局异常
- 显示输出结果

### 2.2 命令层 (commands/)

| 模块 | 职责 |
|------|------|
| submit.py | 交互式收集用户输入，调用record保存，调用summary生成总结 |
| today.py | 读取今日记录，格式化输出 |
| check.py | 调用analyzer计算指标，格式化输出进度报告 |
| review.py | 调用analyzer生成阶段报告，格式化输出 |
| config_cmd.py | 读取/修改配置 |

### 2.3 核心层 (core/)

| 模块 | 职责 |
|------|------|
| record.py | 记录的CRUD操作，数据校验 |
| analyzer.py | 计算统计指标：总时长、连续天数、科目占比、章节覆盖 |
| weakness.py | 实现WeaknessScore算法，识别薄弱知识点 |
| summary.py | 模板化生成AI总结 |

### 2.4 存储层 (storage/)

| 模块 | 职责 |
|------|------|
| memory_store.py | 学习记录的JSON读写，自动备份 |
| config_store.py | 配置文件的读写，提供默认值 |
| file_utils.py | 文件存在性检查、目录创建、损坏恢复 |

### 2.5 模型层 (models/)

| 模块 | 职责 |
|------|------|
| record.py | 学习记录的数据类定义 |
| config.py | 配置的数据类定义 |

---

## 3. 数据流设计

### 3.1 submit 命令数据流

```
用户输入
    │
    ▼
cli.py 解析命令
    │
    ▼
commands/submit.py 收集输入
    │
    ▼
core/record.py 数据校验
    │
    ├── 输入无效 ──▶ 提示错误，重新输入
    │
    ▼
core/summary.py 生成AI总结
    │
    ▼
storage/memory_store.py 写入memory.json
    │
    ▼
输出确认信息
```

### 3.2 today 命令数据流

```
cli.py 解析命令
    │
    ▼
commands/today.py
    │
    ▼
storage/memory_store.py 读取今日记录
    │
    ▼
core/analyzer.py 计算今日统计
    │
    ▼
格式化输出
```

### 3.3 check 命令数据流

```
cli.py 解析命令
    │
    ▼
commands/check.py
    │
    ▼
storage/memory_store.py 读取全部记录
    │
    ├── 无记录 ──▶ 提示"暂无学习记录"
    │
    ▼
core/analyzer.py 计算各指标
    │
    ├── 总学习时长
    ├── 连续学习天数
    ├── 科目占比
    └── 章节覆盖率
    │
    ▼
core/weakness.py 计算薄弱知识点
    │
    ├── WeaknessScore计算
    └── 遗忘风险标记
    │
    ▼
格式化输出报告
```

### 3.4 review 命令数据流

```
cli.py 解析命令
    │
    ▼
commands/review.py
    │
    ▼
storage/memory_store.py 读取全部记录
    │
    ▼
core/analyzer.py 生成分析数据
    │
    ├── 学习趋势
    ├── 高频错误
    └── 重复遗忘知识点
    │
    ▼
core/weakness.py 薄弱知识点详情
    │
    ▼
格式化输出复盘报告
```

---

## 4. 关键设计

### 4.1 记录ID生成

使用时间戳+随机数生成唯一ID：

```python
def generate_id() -> str:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = random.randint(100, 999)
    return f"{timestamp}-{random_suffix}"
```

### 4.2 连续学习天数算法

```python
def calculate_streak(records: list) -> int:
    dates = sorted(set(r.date for r in records), reverse=True)
    if not dates:
        return 0
    
    streak = 1
    today = date.today()
    
    if dates[0] != today:
        if dates[0] != today - timedelta(days=1):
            return 0
        # 从昨天开始计算
    
    for i in range(1, len(dates)):
        if dates[i-1] - dates[i] == timedelta(days=1):
            streak += 1
        else:
            break
    
    return streak
```

### 4.3 章节覆盖率计算

```python
def calculate_chapter_coverage(records: list, config: dict) -> dict:
    coverage = {}
    for subject in config["subjects"]:
        total = len(subject["chapters"])
        learned = len(set(
            r.chapter for r in records 
            if r.subject == subject["name"]
        ))
        coverage[subject["name"]] = {
            "learned": learned,
            "total": total,
            "rate": learned / total if total > 0 else 0
        }
    return coverage
```

### 4.4 WeaknessScore 实现

```python
def calculate_weakness_score(
    question_count: int,
    repeat_count: int,
    self_rating: int,
    days_since_review: int,
    weights: dict
) -> float:
    score = (weights["question_count"] * question_count +
             weights["repeat_count"] * repeat_count +
             weights["self_rating"] * (5 - self_rating) +
             weights["days_since_review"] * days_since_review)
    return score
```

### 4.5 AI总结模板

```python
SUMMARY_TEMPLATES = {
    "good": "本次学习了{subject}的{chapter}，时长{duration}小时。"
            "理解度较高（{rating}/5），建议继续保持。",
    "normal": "本次学习了{subject}的{chapter}，时长{duration}小时。"
              "理解度一般（{rating}/5），建议复习巩固。",
    "weak": "本次学习了{subject}的{chapter}，时长{duration}小时。"
            "理解度较低（{rating}/5），存在疑问：{problems}。"
            "建议重点复习相关内容。"
}

def generate_summary(record) -> str:
    if record.self_rating >= 4:
        template = SUMMARY_TEMPLATES["good"]
    elif record.self_rating >= 3:
        template = SUMMARY_TEMPLATES["normal"]
    else:
        template = SUMMARY_TEMPLATES["weak"]
    
    return template.format(
        subject=record.subject,
        chapter=record.chapter,
        duration=record.duration,
        rating=record.self_rating,
        problems=record.problems or "无"
    )
```

### 4.6 文件损坏恢复

```python
def safe_read_json(filepath: str, default: dict) -> dict:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        # 备份损坏文件
        if os.path.exists(filepath):
            backup = filepath.replace('.json', '_backup.json')
            shutil.copy2(filepath, backup)
        # 写入默认值
        write_json(filepath, default)
        return default
```

---

## 5. 风险分析

| 风险 | 影响 | 概率 | 应对措施 |
|------|------|------|----------|
| JSON文件并发读写冲突 | 数据丢失/损坏 | 低 | 单用户场景，问题不大；写入前备份 |
| 数据量增长导致读取慢 | 用户体验下降 | 低 | 短期内不会；后期可迁移SQLite |
| 配置文件被误删 | 程序异常 | 中 | 提供默认配置，自动创建 |
| 用户输入特殊字符 | 解析错误 | 中 | 输入校验和转义 |
| 时区问题 | 日期计算错误 | 低 | 统一使用本地日期 |

---

## 6. MVP设计

### 6.1 MVP范围

**必须实现：**
- [x] 项目初始化（init命令）
- [x] 学习记录提交（submit命令）
- [x] 今日记录查看（today命令）
- [x] 整体进度查看（check命令）
- [x] 薄弱知识点识别（WeaknessScore）
- [x] 配置文件管理

**后续迭代：**
- [ ] 阶段性复盘（review命令）
- [ ] 学习趋势图表
- [ ] 数据导出功能

### 6.2 MVP交付物

```
408-assistant/
├── cli.py
├── commands/
│   ├── __init__.py
│   ├── submit.py
│   ├── today.py
│   ├── check.py
│   └── config_cmd.py
├── core/
│   ├── __init__.py
│   ├── record.py
│   ├── analyzer.py
│   ├── weakness.py
│   └── summary.py
├── storage/
│   ├── __init__.py
│   ├── memory_store.py
│   ├── config_store.py
│   └── file_utils.py
├── models/
│   ├── __init__.py
│   ├── record.py
│   └── config.py
├── data/
│   ├── memory.json
│   └── config.json
├── requirements.txt
└── README.md
```

### 6.3 MVP验收流程

1. 运行 `python cli.py init` 初始化项目
2. 运行 `python cli.py submit` 提交3-5条测试记录
3. 运行 `python cli.py today` 查看今日汇总
4. 运行 `python cli.py check` 查看进度报告
5. 验证薄弱知识点计算是否正确
6. 验证边界条件处理是否符合预期

---

## 7. 技术依赖

### requirements.txt

```
# 无外部依赖，使用Python标准库
# 如需CLI美化可添加：
# click>=8.0
# rich>=13.0
```

**使用标准库：**
- `json` - 数据存储
- `os` / `pathlib` - 路径操作
- `datetime` - 日期处理
- `uuid` - ID生成（或自实现）
- `argparse` - 命令行解析
- `shutil` - 文件操作

---

## 8. 扩展点

### 8.1 后续可扩展

| 功能 | 扩展方式 |
|------|----------|
| 真实LLM集成 | 在core/summary.py中添加LLM调用接口 |
| 数据库迁移 | 在storage/层添加SQLite实现 |
| 数据导出 | 添加export命令，支持CSV/Excel |
| 学习计划 | 添加plan命令，支持目标设定 |
| 提醒功能 | 添加remind命令，结合系统定时任务 |
