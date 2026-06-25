# MCP Calculator Server

一个基于 Python FastMCP 的 MCP（Model Context Protocol）计算器服务 Demo，提供 6 个数学运算工具、1 个资源和 1 个提示词模板。

## 功能特性

**Tools（工具）**
| 名称 | 说明 | 参数 |
|------|------|------|
| `add` | 加法 | a: float, b: float |
| `subtract` | 减法 | a: float, b: float |
| `multiply` | 乘法 | a: float, b: float |
| `divide` | 除法 | a: float, b: float |
| `power` | 幂运算 | base: float, exponent: float |
| `sqrt` | 平方根 | number: float |

**Resource（资源）**
- `calculator://info` — 返回计算器元信息（名称、版本、支持的操作列表）

**Prompt（提示词）**
- `math_help` — 数学帮助提示词模板

## 环境要求

- Python >= 3.10
- 操作系统：Windows / macOS / Linux

## 安装步骤

```bash
# 1. 进入项目目录
cd demo

# 2. 创建虚拟环境
python -m venv venv

# 3. 激活虚拟环境
# Windows (PowerShell)
venv\Scripts\activate
# Windows (CMD)
venv\Scripts\activate.bat
# macOS / Linux
source venv/bin/activate

# 4. 安装依赖
pip install -r requirements.txt
```

> 国内用户可使用清华镜像加速：`pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`

## 依赖清单

| 包名 | 版本 | 说明 |
|------|------|------|
| mcp | 1.28.0 | MCP 官方 Python SDK |
| anyio | 4.14.0 | 异步 I/O 框架 |
| pydantic | 2.13.4 | 数据校验 |
| httpx | 0.28.1 | HTTP 客户端 |
| uvicorn | 0.49.0 | ASGI 服务器 |
| starlette | 1.3.1 | Web 框架 |

> 完整依赖见 `requirements.txt`

## 运行方式

### 方式一：MCP Inspector（推荐，可视化测试）

```bash
mcp dev calculator.py
```

浏览器自动打开 `http://localhost:6274`，可在界面上选择 Tool、输入参数、查看返回结果。

### 方式二：Client SDK 测试

```bash
python test_client.py
```

使用 MCP Client SDK 连接 Server，自动调用所有 Tool 并打印结果。

### 方式三：带日志的完整测试

```bash
python run_test.py
```

运行 9 项测试（6 个 Tool + Tool 列表 + Resource 列表 + Prompt 列表），结果写入 `run_log.txt`。

## 扩展指南

在 `calculator.py` 中添加新工具只需 3 步：

```python
# 1. 用 @mcp.tool() 装饰器定义函数
@mcp.tool()
def modulo(a: int, b: int) -> int:
    """计算取模运算"""
    return a % b

# 2. 函数名即为工具名（modulo）
# 3. docstring 会自动成为工具描述
```

添加后重启 Server 即可生效。可用 `mcp dev calculator.py` 在 Inspector 中验证新工具。

## MCP Inspector 使用

[MCP Inspector](https://github.com/modelcontextprotocol/inspector) 是官方提供的调试工具，用于可视化测试 MCP Server。

```bash
# 安装（已随 mcp[cli] 自动安装）
pip install mcp[cli]

# 启动
mcp dev calculator.py
```

启动后浏览器打开 Inspector 界面：
- **Tools** 标签页：查看所有工具，输入参数，点击执行
- **Resources** 标签页：查看所有资源，读取内容
- **Prompts** 标签页：查看提示词模板

## 常见问题

### 1. PowerShell 提示"无法加载文件，因为在此系统上禁止运行脚本"

PowerShell 默认执行策略阻止虚拟环境的 activate 脚本。解决方案：

```powershell
# 方案一：修改执行策略（需管理员权限）
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 方案二：不使用 activate，直接调用 venv 中的 python
venv\Scripts\python.exe calculator.py
```

### 2. pip install 超时

默认 PyPI 源在国内访问较慢，使用镜像源：

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

常用镜像源：
- 清华：`https://pypi.tuna.tsinghua.edu.cn/simple`
- 阿里：`https://mirrors.aliyun.com/pypi/simple`

### 3. Windows 中文路径显示乱码

在 PowerShell 中执行涉及中文路径的命令时，使用 `cmd /c` 包装：

```powershell
cmd /c "D:\ai工具\venv\Scripts\python.exe" calculator.py
```

### 4. emoji 字符导致 GBK 编码错误

Windows 默认编码为 GBK，某些 emoji 字符无法输出。解决方案：在 print 时避免使用 emoji，改用 `[PASS]`、`[FAIL]` 等文本标记。

## 相关资源

- [MCP 官方文档](https://modelcontextprotocol.io/) — 协议规范、架构说明
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) — 官方 Python 实现
- [MCP TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk) — 官方 TypeScript 实现
- [MCP Inspector](https://github.com/modelcontextprotocol/inspector) — 可视化调试工具
- [MCP Server 示例集合](https://github.com/modelcontextprotocol/servers) — 官方参考实现
