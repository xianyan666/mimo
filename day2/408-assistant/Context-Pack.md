# Context-Pack.md

项目名称：408考研学习助手

版本：1.0

更新日期：2026-06-23

---

## ① 目标（Goal）

**项目目标：**

构建一个基于CLI的408考研学习助手，帮助用户记录每日学习进度、跟踪整体学习状态、识别薄弱知识点、生成阶段性复盘报告，通过本地JSON文件维护长期学习记忆。

**当前阶段目标：**

完成核心功能开发并通过全部测试，包括：submit（提交记录）、today（今日查看）、check（进度查看）、review（复盘报告）四个命令，以及WeaknessScore算法、AI总结模板、配置管理等功能。

**验收目标：**

- 4个核心命令可正常运行
- WeaknessScore算法计算正确
- 160项测试用例全部通过
- 边界条件处理符合预期
- 中文显示正常，无乱码

---

## ② 非目标（Non-Goal）

本项目不负责：

- 多用户支持
- 多设备同步/云端存储
- 真实LLM API集成（使用模拟AI总结）
- 图形界面（仅CLI）
- 自动计时功能
- 学习资源推荐
- 模拟考试/题目练习
- 数据库集成（使用JSON文件）
- Web页面

---

## ③ 资料（Reference）

**项目背景：**

408考研包含四门科目：数据结构、计算机组成原理、操作系统、计算机网络。系统需要帮助考生记录学习进度、分析薄弱环节、提供复习建议。

**核心功能：**

| 命令 | 功能 | 输出 |
|------|------|------|
| submit | 交互式提交学习记录 | 确认信息 + AI总结 |
| today | 查看今日记录 | 记录表格 + 统计 |
| check | 查看整体进度 | 完整进度报告 |
| review | 生成复盘报告 | 阶段性分析 |

**核心数据结构：**

```json
{
  "records": [{
    "id": "uuid",
    "date": "YYYY-MM-DD",
    "subject": "科目",
    "chapter": "章节",
    "duration": 2.5,
    "content": "学习内容",
    "problems": "遇到的问题",
    "self_rating": 3,
    "ai_summary": "AI总结",
    "created_at": "ISO8601"
  }],
  "metadata": {
    "created_at": "首次创建时间",
    "last_updated": "最后更新时间"
  }
}
```

**WeaknessScore算法：**

```
Score = (2.0 × 提问次数) + (1.5 × 重复次数) + (1.0 × (5-自评)) + (0.5 × 未复习天数)
```

- < 4：良好
- 4-8：关注
- ≥ 8：薄弱

---

## ④ 代码（Code Context）

**当前目录结构：**

```
408-assistant/
├── cli.py                  # 主程序入口
├── commands/               # 命令层
│   ├── submit.py           # submit命令
│   ├── today.py            # today命令
│   ├── check.py            # check命令
│   ├── review.py           # review命令
│   └── config_cmd.py       # config命令
├── core/                   # 核心层
│   ├── analyzer.py         # 数据分析
│   ├── weakness.py         # 薄弱知识点计算
│   └── summary.py          # AI总结生成
├── storage/                # 存储层
│   ├── memory_store.py     # 学习记录存储
│   ├── config_store.py     # 配置存储
│   └── file_utils.py       # 文件工具
├── models/                 # 模型层
│   ├── record.py           # 记录模型
│   └── config.py           # 配置模型
└── data/                   # 数据目录
    ├── memory.json         # 学习记录
    └── config.json         # 配置文件
```

**关键模块：**

| 模块 | 职责 |
|------|------|
| cli.py | 命令行解析与调度，UTF-8编码设置 |
| commands/submit.py | 交互式输入收集，数据校验 |
| core/analyzer.py | 统计分析：总时长、连续天数、科目占比、章节覆盖 |
| core/weakness.py | WeaknessScore算法实现 |
| core/summary.py | AI总结模板生成 |
| storage/memory_store.py | JSON读写，记录查询 |

**当前已实现功能：**

- [x] submit命令 - 交互式提交学习记录
- [x] today命令 - 今日记录查看
- [x] check命令 - 整体进度查看
- [x] review命令 - 阶段性复盘报告
- [x] config命令 - 配置管理
- [x] WeaknessScore算法
- [x] AI总结模板
- [x] 边界条件处理
- [x] 中文UTF-8支持

**待实现功能：**

- [ ] 数据导出功能
- [ ] 学习计划功能
- [ ] 提醒功能

---

## ⑤ 日志（Log）

**已完成：**

- 完成全部核心功能开发
- 通过160项测试用例
- 修复中文乱码问题
- 修复JSON字段缺失处理

**发现的问题：**

| 问题 | 严重等级 | 状态 |
|------|----------|------|
| Windows终端中文显示乱码 | Medium | 已修复 |
| memory.json字段缺失时默认值处理 | Low | 已修复 |

**已修复问题：**

1. **中文乱码** - 在cli.py中添加UTF-8编码设置
2. **字段缺失** - Record.from_dict()增加默认值处理

**未解决问题：**

- 无

---

## ⑥ 约束（Constraint）

**技术约束：**

- Python 3.11+
- CLI项目，无GUI
- JSON文件存储，无数据库
- 使用Python标准库，无外部依赖

**功能约束：**

- 仅支持408四门科目
- 不接入数据库
- 不接入Web页面
- 不接入真实LLM API
- 仅支持单用户

**数据约束：**

- 学习时长：0-16小时
- 自评分数：1-5分
- WeaknessScore阈值：默认8
- 遗忘天数：默认7天

**禁止事项：**

- 不修改memory.json记录结构
- 不删除历史记录
- 不新增无关功能
- 不引入外部依赖
- 不上传用户数据

---

## ⑦ 输出格式（Output Format）

**实现方案：**

- 模块化设计：cli → commands → core → storage → models
- 数据流：用户输入 → 命令层 → 核心层 → 存储层 → 输出
- 异常处理：输入校验 + 文件恢复 + 全局捕获

**代码修改：**

- 修改cli.py添加UTF-8编码支持
- 修改models/record.py增加默认值处理
- 保持现有代码结构不变

**测试结果：**

- 总测试数：160
- 通过：160
- 失败：0
- 通过率：100%

**风险说明：**

| 风险 | 影响 | 概率 | 应对 |
|------|------|------|------|
| JSON并发读写 | 数据损坏 | 低 | 写入前备份 |
| 数据量增长 | 读取变慢 | 低 | 后期可迁移SQLite |
| 配置文件误删 | 程序异常 | 中 | 提供默认配置 |

**最终输出采用Markdown格式。**

---

## 附录：关键文件路径

| 文件 | 路径 | 说明 |
|------|------|------|
| 主程序 | 408-assistant/cli.py | 命令行入口 |
| 学习记录 | 408-assistant/data/memory.json | 存储学习数据 |
| 配置文件 | 408-assistant/data/config.json | 用户配置 |
| 测试用例 | test.md | 160条测试用例 |
| 测试记录 | test record.md | 测试执行结果 |
| 产品规格 | spec.md | 功能规格说明 |
| 架构设计 | plan.md | 模块划分与数据流 |
| 任务清单 | tasks.md | 开发任务列表 |
| Agent定义 | AGENTS.md | 助手行为规则 |
