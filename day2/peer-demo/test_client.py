import asyncio
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


async def test_calculator():
    server_params = StdioServerParameters(
        command="venv\\Scripts\\python.exe",
        args=["calculator.py"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            print("=== 测试工具列表 ===")
            tools = await session.list_tools()
            for tool in tools.tools:
                print(f"  工具: {tool.name} - {tool.description}")

            print("\n=== 测试加法: 2 + 3 ===")
            result = await session.call_tool("add", {"a": 2, "b": 3})
            print(f"  结果: {result.content[0].text}")

            print("\n=== 测试减法: 10 - 4 ===")
            result = await session.call_tool("subtract", {"a": 10, "b": 4})
            print(f"  结果: {result.content[0].text}")

            print("\n=== 测试乘法: 6 * 7 ===")
            result = await session.call_tool("multiply", {"a": 6, "b": 7})
            print(f"  结果: {result.content[0].text}")

            print("\n=== 测试除法: 15 / 3 ===")
            result = await session.call_tool("divide", {"a": 15, "b": 3})
            print(f"  结果: {result.content[0].text}")

            print("\n=== 测试幂运算: 2 ^ 10 ===")
            result = await session.call_tool("power", {"base": 2, "exponent": 10})
            print(f"  结果: {result.content[0].text}")

            print("\n=== 测试平方根: sqrt(144) ===")
            result = await session.call_tool("sqrt", {"number": 144})
            print(f"  结果: {result.content[0].text}")

            print("\n=== 测试资源列表 ===")
            resources = await session.list_resources()
            for resource in resources.resources:
                print(f"  资源: {resource.uri} - {resource.name}")

            print("\n=== 测试提示词列表 ===")
            prompts = await session.list_prompts()
            for prompt in prompts.prompts:
                print(f"  提示词: {prompt.name} - {prompt.description}")

            print("\n[PASS] 所有测试通过!")


if __name__ == "__main__":
    asyncio.run(test_calculator())
