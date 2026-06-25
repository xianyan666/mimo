from mcp.server.fastmcp import FastMCP

# 初始化MCP服务器
mcp = FastMCP("Calculator")

# 定义计算器工具
@mcp.tool()
def add(a: float, b: float) -> float:
    """计算两个数的和"""
    return a + b

@mcp.tool()
def subtract(a: float, b: float) -> float:
    """计算两个数的差"""
    return a - b

@mcp.tool()
def multiply(a: float, b: float) -> float:
    """计算两个数的积"""
    return a * b

@mcp.tool()
def divide(a: float, b: float) -> float:
    """计算两个数的商"""
    if b == 0:
        raise ValueError("除数不能为零")
    return a / b

@mcp.tool()
def power(base: float, exponent: float) -> float:
    """计算幂运算"""
    return base ** exponent

@mcp.tool()
def sqrt(number: float) -> float:
    """计算平方根"""
    if number < 0:
        raise ValueError("不能计算负数的平方根")
    return number ** 0.5

# 定义资源
@mcp.resource("calculator://info")
def get_calculator_info():
    """获取计算器信息"""
    return {
        "name": "MCP计算器",
        "version": "1.0.0",
        "supported_operations": ["add", "subtract", "multiply", "divide", "power", "sqrt"]
    }

# 定义提示词模板
@mcp.prompt()
def math_help():
    """数学帮助提示词"""
    return "我是一个数学计算器，可以帮助你进行各种数学运算。请告诉我你需要计算什么？"

if __name__ == "__main__":
    mcp.run(transport="stdio")