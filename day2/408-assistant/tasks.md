# 408考研学习助手 - 任务清单

## 任务概览

| 任务ID | 任务名称 | 优先级 | 预估耗时 | 依赖 |
|--------|----------|--------|----------|------|
| T1 | 项目初始化与目录结构 | P0 | 10min | - |
| T2 | 数据模型定义 | P0 | 15min | T1 |
| T3 | 存储层实现 | P0 | 30min | T2 |
| T4 | 配置管理功能 | P1 | 20min | T3 |
| T5 | submit命令实现 | P0 | 40min | T3, T4 |
| T6 | today命令实现 | P0 | 20min | T3 |
| T7 | 分析器核心实现 | P0 | 40min | T2 |
| T8 | WeaknessScore算法实现 | P0 | 30min | T2 |
| T9 | check命令实现 | P0 | 30min | T7, T8 |
| T10 | AI总结模板实现 | P1 | 15min | T2 |
| T11 | review命令实现 | P1 | 30min | T7, T8 |
| T12 | CLI主程序整合 | P0 | 20min | T5, T6, T9, T11 |
| T13 | 边界条件与异常处理 | P0 | 30min | T12 |
| T14 | 集成测试与验收 | P0 | 30min | T13 |

---

## 依赖关系图

```
T1 ──▶ T2 ──▶ T3 ──▶ T4 ──▶ T5 ──┐
                │                  │
                ▼                  ▼
                T6            T12 ──▶ T13 ──▶ T14
                │                  ▲
           T7 ──┼──────────────────┤
                │                  │
           T8 ──┼──────────────────┤
                │                  │
                T9 ────────────────┤
                │                  │
           T10  │                  │
                │                  │
                T11 ───────────────┘
```

---

## 详细任务说明

### T1: 项目初始化与目录结构

**目标：** 创建项目骨架和目录结构

**实现内容：**
- 创建项目根目录 `408-assistant/`
- 创建子目录：`commands/`、`core/`、`storage/`、`models/`、`data/`
- 创建各目录的 `__init__.py`
- 创建 `requirements.txt`
- 创建 `cli.py` 主入口骨架
- 初始化 `data/config.json` 和 `data/memory.json` 空文件

**验收标准：**
- [ ] 目录结构符合plan.md设计
- [ ] 所有`__init__.py`文件存在
- [ ] `python cli.py --help` 可运行（即使功能未实现）

---

### T2: 数据模型定义

**目标：** 定义学习记录和配置的数据结构

**实现内容：**
- 创建 `models/record.py`：
  - `Record` 数据类：id, date, subject, chapter, duration, content, problems, self_rating, ai_summary, created_at
  - 字段校验方法
- 创建 `models/config.py`：
  - `Config` 数据类：user, subjects, weakness_weights, thresholds
  - 默认配置生成方法

**验收标准：**
- [ ] `Record` 可正确实例化
- [ ] `Config` 可正确实例化
- [ ] 字段校验可捕获无效输入（如duration < 0）
- [ ] 默认配置可正确生成

---

### T3: 存储层实现

**目标：** 实现JSON文件的读写和管理

**实现内容：**
- 创建 `storage/file_utils.py`：
  - `ensure_dir()` - 确保目录存在
  - `safe_read_json()` - 安全读取JSON，损坏时自动恢复
  - `write_json()` - 写入JSON文件
  - `backup_file()` - 备份文件
- 创建 `storage/memory_store.py`：
  - `load_records()` - 加载所有记录
  - `save_record()` - 保存单条记录
  - `get_records_by_date()` - 按日期查询
  - `get_records_by_subject()` - 按科目查询
  - `get_all_records()` - 获取全部记录
- 创建 `storage/config_store.py`：
  - `load_config()` - 加载配置
  - `save_config()` - 保存配置
  - `get_default_config()` - 获取默认配置

**验收标准：**
- [ ] 可正确读写 `data/memory.json`
- [ ] 可正确读写 `data/config.json`
- [ ] JSON损坏时可自动备份并恢复
- [ ] 文件不存在时可自动创建

---

### T4: 配置管理功能

**目标：** 实现配置的查看和修改

**实现内容：**
- 创建 `commands/config_cmd.py`：
  - `show_config()` - 显示当前配置
  - `set_config()` - 修改配置项
  - `reset_config()` - 重置为默认配置
- 支持的配置项：
  - `user.name` - 用户姓名
  - `user.target_date` - 目标考试日期
  - `user.daily_goal_hours` - 每日目标时长
  - `thresholds.weakness_score` - 薄弱知识点阈值
  - `thresholds.forget_days` - 遗忘天数阈值

**验收标准：**
- [ ] `python cli.py config` 显示当前配置
- [ ] `python cli.py config --set user.name 张三` 修改成功
- [ ] 配置修改后正确持久化

---

### T5: submit命令实现

**目标：** 实现交互式学习记录提交

**实现内容：**
- 创建 `commands/submit.py`：
  - `prompt_subject()` - 选择科目（交互式菜单）
  - `prompt_chapter()` - 输入章节
  - `prompt_duration()` - 输入时长（含校验）
  - `prompt_content()` - 输入完成内容
  - `prompt_problems()` - 输入遇到的问题
  - `prompt_rating()` - 输入自我评价（1-5）
  - `collect_input()` - 收集所有输入
  - `execute()` - 执行提交流程
- 输入校验：
  - 科目必须在配置范围内
  - 时长必须为正数且 ≤ 16
  - 评价必须在 1-5 范围

**验收标准：**
- [ ] 交互式输入流程完整
- [ ] 输入校验生效
- [ ] 记录正确保存到 `memory.json`
- [ ] 提交后显示确认信息

---

### T6: today命令实现

**目标：** 实现今日学习记录查看

**实现内容：**
- 创建 `commands/today.py`：
  - `get_today_records()` - 获取今日记录
  - `calculate_today_stats()` - 计算今日统计
  - `format_record()` - 格式化单条记录
  - `format_summary()` - 格式化今日汇总
  - `execute()` - 执行查看流程
- 输出内容：
  - 今日记录列表（表格形式）
  - 今日总学习时长
  - 各科目时长分布

**验收标准：**
- [ ] 正确显示今日所有记录
- [ ] 总时长计算正确
- [ ] 无记录时显示友好提示
- [ ] 输出格式清晰易读

---

### T7: 分析器核心实现

**目标：** 实现学习数据的各种统计分析

**实现内容：**
- 创建 `core/analyzer.py`：
  - `calculate_total_hours()` - 计算总学习时长
  - `calculate_streak()` - 计算连续学习天数
  - `calculate_subject_distribution()` - 计算科目占比
  - `calculate_chapter_coverage()` - 计算章节覆盖率
  - `find_frequent_problems()` - 找出高频疑问
  - `find_forgettable_content()` - 找出遗忘风险内容
  - `predict_completion()` - 冲刺预测

**验收标准：**
- [ ] 总时长计算正确
- [ ] 连续天数算法正确（处理跨月、断档等情况）
- [ ] 科目占比百分比正确（总和为100%）
- [ ] 章节覆盖率统计正确
- [ ] 高频疑问排序正确

---

### T8: WeaknessScore算法实现

**目标：** 实现薄弱知识点识别算法

**实现内容：**
- 创建 `core/weakness.py`：
  - `extract_knowledge_points()` - 从记录中提取知识点
  - `calculate_question_count()` - 统计提问次数
  - `calculate_repeat_count()` - 统计重复学习次数
  - `calculate_days_since_review()` - 计算未复习天数
  - `calculate_weakness_score()` - 计算单个知识点得分
  - `identify_weak_points()` - 识别所有薄弱知识点
  - `classify_weakness_level()` - 分类薄弱程度

**验收标准：**
- [ ] WeaknessScore计算公式正确
- [ ] 四个因素权重正确应用
- [ ] 阈值 ≥ 8 正确判定为薄弱
- [ ] 输出包含知识点详情和得分

---

### T9: check命令实现

**目标：** 实现整体学习进度查看

**实现内容：**
- 创建 `commands/check.py`：
  - `gather_statistics()` - 收集所有统计数据
  - `format_progress_report()` - 格式化进度报告
  - `execute()` - 执行查看流程
- 输出内容：
  - 总学习时长
  - 连续学习天数
  - 科目占比表
  - 章节覆盖率表
  - 高频疑问列表
  - 薄弱知识点列表
  - 遗忘风险内容
  - 冲刺预测

**验收标准：**
- [ ] 所有指标正确显示
- [ ] 输出格式清晰（使用表格/列表）
- [ ] 无记录时显示友好提示
- [ ] 薄弱知识点高亮显示

---

### T10: AI总结模板实现

**目标：** 实现模拟AI总结生成功能

**实现内容：**
- 创建 `core/summary.py`：
  - 总结模板库（按评分分级）
  - `generate_summary()` - 生成总结
  - `select_template()` - 选择合适模板
  - `fill_template()` - 填充模板内容
- 模板分级：
  - 评分 ≥ 4：肯定型总结
  - 评分 = 3：中性型总结
  - 评分 ≤ 2：警示型总结

**验收标准：**
- [ ] 不同评分生成不同风格总结
- [ ] 总结包含关键信息（科目、时长、评价）
- [ ] 有问题时总结中包含问题提示

---

### T11: review命令实现

**目标：** 实现阶段性复盘报告

**实现内容：**
- 创建 `commands/review.py`：
  - `prompt_date_range()` - 输入时间范围
  - `gather_review_data()` - 收集复盘数据
  - `format_review_report()` - 格式化复盘报告
  - `execute()` - 执行复盘流程
- 输出内容：
  - 学习趋势（时长变化）
  - 高频错误汇总
  - 重复遗忘知识点
  - 薄弱知识点详情及建议
  - 距离目标差距

**验收标准：**
- [ ] 可选择时间范围
- [ ] 趋势分析正确
- [ ] 薄弱知识点建议具体
- [ ] 输出格式清晰

---

### T12: CLI主程序整合

**目标：** 将所有命令整合到主程序

**实现内容：**
- 更新 `cli.py`：
  - 使用argparse定义命令
  - 注册所有子命令
  - 全局异常处理
  - 帮助信息完善
- 支持的命令：
  - `init` - 初始化项目
  - `submit` - 提交记录
  - `today` - 今日查看
  - `check` - 进度查看
  - `review` - 复盘报告
  - `config` - 配置管理

**验收标准：**
- [ ] `python cli.py --help` 显示所有命令
- [ ] `python cli.py <command> --help` 显示命令帮助
- [ ] 所有命令可正常调用
- [ ] 异常不会导致程序崩溃

---

### T13: 边界条件与异常处理

**目标：** 完善所有边界条件处理

**实现内容：**
- 输入为空处理
- 非408内容提示
- 学习时长异常处理
- 重复提交支持
- 无历史记录提示
- 文件损坏恢复
- 配置缺失兜底
- 特殊字符处理
- 中断处理（Ctrl+C）

**验收标准：**
- [ ] 所有spec.md中定义的边界条件已处理
- [ ] 错误提示友好明确
- [ ] 程序不会因异常输入崩溃
- [ ] 文件损坏可自动恢复

---

### T14: 集成测试与验收

**目标：** 完整功能测试和验收

**实现内容：**
- 完整流程测试：
  1. 初始化项目
  2. 提交多条记录（不同科目、不同日期）
  3. 查看今日记录
  4. 查看整体进度
  5. 查看复盘报告
- 边界测试：
  - 空输入
  - 极端值（时长0/16）
  - 特殊字符
  - 文件损坏场景
- 算法验证：
  - WeaknessScore计算
  - 连续天数计算
  - 科目占比计算

**验收标准：**
- [ ] 完整流程无报错
- [ ] 所有边界条件处理正确
- [ ] 算法计算结果正确
- [ ] 数据持久化正确

---

## 任务执行顺序

**第一阶段：基础框架（T1-T3）**
```
T1 → T2 → T3
```

**第二阶段：核心功能（T4-T6, T7-T8）**
```
T4 ──┐
     ├──▶ T5
T3 ──┤
     └──▶ T6

T2 ──▶ T7
T2 ──▶ T8
```

**第三阶段：命令整合（T9-T12）**
```
T7 + T8 ──▶ T9
T7 + T8 ──▶ T11
T5 + T6 + T9 + T11 ──▶ T12
```

**第四阶段：完善验收（T13-T14）**
```
T12 ──▶ T13 ──▶ T14
```

---

## 预估总耗时

| 阶段 | 任务 | 耗时 |
|------|------|------|
| 基础框架 | T1-T3 | 55min |
| 核心功能 | T4-T8 | 140min |
| 命令整合 | T9-T12 | 100min |
| 完善验收 | T13-T14 | 60min |
| **总计** | | **355min (~6h)** |
