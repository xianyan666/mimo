import asyncio
import sys
import io
from datetime import datetime
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


async def test_calculator():
    log_lines = []
    
    def log(msg):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] {msg}"
        log_lines.append(line)
        print(line)

    server_params = StdioServerParameters(
        command="venv\\Scripts\\python.exe",
        args=["calculator.py"],
    )

    log("START: MCP Calculator Server Test")
    log("=" * 50)

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            log("INIT: Client session initialized")

            # 1. 测试工具列表
            log("-" * 50)
            log("TEST 1: List Tools")
            tools = await session.list_tools()
            log(f"RESULT: Found {len(tools.tools)} tools")
            for tool in tools.tools:
                log(f"  - {tool.name}: {tool.description}")
            log("STATUS: PASS")

            # 2. 测试加法
            log("-" * 50)
            log("TEST 2: add(a=2, b=3)")
            result = await session.call_tool("add", {"a": 2, "b": 3})
            log(f"RESULT: {result.content[0].text}")
            log("EXPECTED: 5.0")
            log("STATUS: PASS" if result.content[0].text == "5.0" else "STATUS: FAIL")

            # 3. 测试减法
            log("-" * 50)
            log("TEST 3: subtract(a=10, b=4)")
            result = await session.call_tool("subtract", {"a": 10, "b": 4})
            log(f"RESULT: {result.content[0].text}")
            log("EXPECTED: 6.0")
            log("STATUS: PASS" if result.content[0].text == "6.0" else "STATUS: FAIL")

            # 4. 测试乘法
            log("-" * 50)
            log("TEST 4: multiply(a=6, b=7)")
            result = await session.call_tool("multiply", {"a": 6, "b": 7})
            log(f"RESULT: {result.content[0].text}")
            log("EXPECTED: 42.0")
            log("STATUS: PASS" if result.content[0].text == "42.0" else "STATUS: FAIL")

            # 5. 测试除法
            log("-" * 50)
            log("TEST 5: divide(a=15, b=3)")
            result = await session.call_tool("divide", {"a": 15, "b": 3})
            log(f"RESULT: {result.content[0].text}")
            log("EXPECTED: 5.0")
            log("STATUS: PASS" if result.content[0].text == "5.0" else "STATUS: FAIL")

            # 6. 测试幂运算
            log("-" * 50)
            log("TEST 6: power(base=2, exponent=10)")
            result = await session.call_tool("power", {"base": 2, "exponent": 10})
            log(f"RESULT: {result.content[0].text}")
            log("EXPECTED: 1024.0")
            log("STATUS: PASS" if result.content[0].text == "1024.0" else "STATUS: FAIL")

            # 7. 测试平方根
            log("-" * 50)
            log("TEST 7: sqrt(number=144)")
            result = await session.call_tool("sqrt", {"number": 144})
            log(f"RESULT: {result.content[0].text}")
            log("EXPECTED: 12.0")
            log("STATUS: PASS" if result.content[0].text == "12.0" else "STATUS: FAIL")

            # 8. 测试资源列表
            log("-" * 50)
            log("TEST 8: List Resources")
            resources = await session.list_resources()
            log(f"RESULT: Found {len(resources.resources)} resources")
            for resource in resources.resources:
                log(f"  - {resource.uri}: {resource.name}")
            log("STATUS: PASS")

            # 9. 测试提示词列表
            log("-" * 50)
            log("TEST 9: List Prompts")
            prompts = await session.list_prompts()
            log(f"RESULT: Found {len(prompts.prompts)} prompts")
            for prompt in prompts.prompts:
                log(f"  - {prompt.name}: {prompt.description}")
            log("STATUS: PASS")

            log("=" * 50)
            log("END: All tests completed")

    # 写入日志文件
    with open("run_log.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))
    
    print(f"\nLog saved to run_log.txt")


if __name__ == "__main__":
    asyncio.run(test_calculator())
