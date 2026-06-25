# Apache HTTP 服务器日志智能分析报告

## 1. 项目概述

本项目对 Apache HTTP Server 的错误日志进行全流程分析：日志解析 → 异常识别 → 统计分析 → 可视化 → 根因定位。目标是从 56,482 条原始日志中提取结构化信息，识别故障模式，并给出系统优化建议。

- **数据来源**：GitHub logpai/loghub 项目 Apache 日志数据集
- **技术栈**：Python 3.13 / pandas / re / matplotlib
- **日志时间跨度**：2005-06-09 ~ 2006-02-28（约 9 个月）

## 2. 数据探索

| 指标 | 值 |
|------|-----|
| 原始总行数 | 56,482 |
| 标准格式行数 | 52,004 |
| 异常行（无标准前缀） | 4,478 |
| 日志级别分布 | error: 38,081 / notice: 13,755 / warn: 168 / unknown: 4,478 |

异常行主要是 `script not found or unable to stat` 等无时间戳前缀的日志条目，已保留为 `level="unknown"` 写入结构化数据。

## 3. 日志解析方法

采用正则表达式 `^\[(.+?)\]\s+\[(\w+)\]\s+(.+)$` 提取三个字段：

- `timestamp`：时间戳，格式如 `Thu Jun 09 06:07:04 2005`，异常行为空字符串
- `level`：日志级别（error / notice / warn / unknown）
- `content`：日志内容

解析流程支持分块读取（chunk_size=10,000），适用于大规模日志文件。异常行保留为 `level="unknown"` 写入结构化数据。解析结果保存为 `structured_logs.csv`（56,482 条记录）。

## 4. 异常识别结果

从 38,081 条 error 日志中，通过三维度识别异常：

**维度一：日志级别** — 所有 `[error]` 级别日志均纳入异常范围。

**维度二：关键词/错误码** — 提取 19 种错误码：

| 错误码 | 数量 | 占比 | 含义 |
|--------|------|------|------|
| HTTP_404 | 20,861 | 54.78% | 请求文件不存在 |
| HTTP_403 | 6,745 | 17.71% | 目录索引被禁止 |
| HTTP_500 | 3,301 | 8.67% | CGI 脚本未找到 |
| mod_jk_state_5 | 1,320 | 3.47% | mod_jk 后端回复读取失败 |
| mod_jk_child_init | 1,259 | 3.31% | mod_jk 子进程初始化失败 |
| mod_jk_state_6 | 1,044 | 2.74% | mod_jk 后端连接已关闭 |
| mod_jk_state_4 | 1,024 | 2.69% | mod_jk 请求发送失败 |
| jk2_init | 971 | 2.55% | jk2 子进程注册信息 |
| 其他 | 5,056 | 13.28% | state 1/2/3/7/8/9/10 + config/env/uriMap |

**维度三：模块** — 按消息中的组件关键词划分 7 个模块（workerEnv 优先级高于 mod_jk）：

| 模块 | 数量 | 占比 |
|------|------|------|
| other（HTTP 客户端请求类） | 31,115 | 81.71% |
| workerEnv | 4,349 | 11.42% |
| mod_jk | 1,259 | 3.31% |
| jk2_init | 971 | 2.55% |
| config | 180 | 0.47% |
| env | 180 | 0.47% |
| uriMap | 27 | 0.07% |

## 5. 统计分析结果

### 5.1 大类分布

| 类别 | 数量 | 占比 |
|------|------|------|
| HTTP 客户端请求错误 | 31,115 | 81.71% |
| 服务端模块错误 | 6,966 | 18.29% |

客户端请求错误占绝对多数，说明大量异常来自外部请求而非服务器自身故障。

### 5.2 每日 Error 趋势

- 共 213 天有 error 记录
- 日均 error 数量：约 179 条
- 峰值：2005-11-29 出现 1,262 条 error
- 2005 年 11 月起 error 数量明显上升，可能与网站流量增长或配置变更有关

### 5.3 模块异常率

服务端模块错误（6,966 条）中：

| 模块 | 数量 | 占服务端错误比例 |
|------|------|-----------------|
| workerEnv | 4,349 | 62.43% |
| mod_jk | 1,259 | 18.08% |
| jk2_init | 971 | 13.94% |
| config | 180 | 2.58% |
| env | 180 | 2.58% |
| uriMap | 27 | 0.39% |

workerEnv 模块是服务端错误的主要来源，占服务端错误的 62.43%。

## 6. 可视化分析

生成三张图表，保存在 `charts/` 目录：

- **daily_error_trend.png**：每日 Error 数量趋势折线图。可观察到 error 数量在 2005 年 11 月后显著增加，存在多个尖峰（如 11-29 的 1,262 条）。
- **error_code_pie.png**：错误码占比饼图。HTTP_404 独占 54.78%，是最大的错误类型；HTTP_403 和 HTTP_500 分列二三位。
- **module_error_bar.png**：模块 Error 数量柱状图。other 类（HTTP 客户端请求）远超其他模块，mod_jk 是服务端最大错误源。

## 7. 故障根因分析

### 7.1 workerEnv / mod_jk 系列错误（5,608 条）

mod_jk 是 Apache 与 Tomcat 之间的连接器模块，workerEnv 是其核心组件。本日志中相关错误包括：

- **workerEnv error state 1~10**（4,349 条）：表示 worker 进程处于不同异常状态。state 5（后端回复读取失败，1,320 条）和 state 6（后端连接已关闭，1,044 条）最为常见，说明 Tomcat 端存在连接不稳定、超时或进程异常退出的问题。
- **mod_jk child init 1 -2**（1,259 条）：子进程初始化失败，返回码 -2 表示无法注册到 Apache scoreboard，通常与 MPM 配置不兼容或 worker 进程数超出限制有关。

**根因推断**：Tomcat 后端服务不稳定，可能由 GC 停顿、内存不足或连接池耗尽引起。workerEnv 组件承载了主要的连接状态管理，其频繁报错表明 mod_jk 与 Tomcat 之间的通信链路存在系统性问题。

### 7.2 HTTP 404 错误（20,861 条）

大量 404 请求指向不存在的路径：`/var/www/html/blog`、`/var/www/html/blogs`、`/var/www/html/drupal`、`/var/www/html/wordpress` 等。

**根因推断**：服务器曾部署或尝试部署多个 CMS 应用（WordPress、Drupal、phpGroupWare 等），但这些应用未正确安装或已被移除，导致大量死链接。同时存在搜索引擎爬虫和攻击扫描器探测这些路径。

### 7.3 HTTP 403 错误（6,745 条）

`Directory index forbidden by rule: /var/www/html/` 表示请求了根目录且未配置 index 文件。

**根因推断**：Apache 配置中未启用目录索引（Options Indexes），且根目录缺少 index.html 或 index.php。这是配置问题而非攻击。

### 7.4 HTTP 500 错误（3,301 条）

`script not found or unable to stat: /var/www/cgi-bin/awstats` 表示 CGI 脚本缺失。

**根因推断**：AWStats 统计工具的 CGI 脚本被删除或权限配置错误，但 Apache 配置中仍保留了对应的 ScriptAlias。

### 7.5 安全风险

208 条 unknown 类型错误是目录遍历攻击尝试（`../../../winnt/system32/cmd.exe`），针对 Windows IIS 的已知漏洞。虽然 Apache on Linux 不受影响，但说明服务器暴露在公网且被自动化扫描工具探测。

## 8. 总结与系统优化建议

### 8.1 问题总结

| 优先级 | 问题 | 影响范围 |
|--------|------|----------|
| 高 | workerEnv/mod_jk 连接不稳定 | 5,608 条 error，影响 Tomcat 后端服务可用性 |
| 高 | 大量 404 死链接 | 20,861 条 error，浪费服务器资源，影响 SEO |
| 中 | 目录索引配置缺失 | 6,745 条 403 error，用户体验差 |
| 中 | CGI 脚本缺失 | 3,301 条 500 error |
| 低 | 安全扫描探测 | 208 条，暂无实际危害 |

### 8.2 优化建议

1. **mod_jk 调优**：
   - 调整 `worker.connect_timeout` 和 `worker.prepost_timeout` 参数，减少超时导致的 state 错误
   - 启用 `worker.retries` 设置合理的重试次数
   - 监控 Tomcat JVM 内存使用，避免 GC 停顿导致连接中断
   - 考虑升级到 mod_proxy_ajp 替代 mod_jk（更现代、维护更活跃）

2. **清理死链接**：
   - 移除未使用的 CMS 应用配置和文件
   - 配置自定义 404 错误页面，引导用户到有效页面
   - 使用 robots.txt 阻止爬虫访问已废弃路径

3. **修复配置问题**：
   - 为 `/var/www/html/` 添加 index 文件或启用 DirectoryIndex
   - 清理 cgi-bin 中不存在的 ScriptAlias 配置
   - 移除 AWStats 相关配置（如果不再使用）

4. **安全加固**：
   - 配置 mod_security 规则拦截目录遍历攻击
   - 限制 Apache 错误日志的访问权限
   - 定期审计访问日志中的异常请求模式

5. **监控改进**：
   - 设置 error 日志告警阈值（如每日 error 超过 500 条触发告警）
   - 对 mod_jk state 错误建立专项监控面板
   - 定期生成本分析报告，跟踪优化效果
