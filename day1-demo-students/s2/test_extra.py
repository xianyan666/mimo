# test_extra.py — 补充测试用例
# 运行: python test_extra.py
# 验证修复后的功能和其他边界情况

import sys
from src.task_manager import add_task, list_tasks, filter_by_priority

passed = 0
failed = 0


def check(name, condition, msg=None):
    global passed, failed
    if condition:
        print(f'  ✅ {name}')
        passed += 1
    else:
        print(f'  ❌ {name}')
        if msg:
            print(f'     错误: {msg}')
        failed += 1


print('补充测试用例\n')

# ==========================================
# 测试 1: priority 为数字字符串
# ==========================================
print('测试 1: priority 为数字字符串')

tasks = []
add_task(tasks, '任务A', '5')
add_task(tasks, '任务B', '3')
check('数字字符串 priority 转换',
      tasks[0]['priority'] == 5 and tasks[1]['priority'] == 3 and
      isinstance(tasks[0]['priority'], int) and isinstance(tasks[1]['priority'], int),
      f'priority 值: {[t["priority"] for t in tasks]}')

print('')

# ==========================================
# 测试 2: priority 为负数
# ==========================================
print('测试 2: priority 为负数')

tasks = []
add_task(tasks, '负优先级', -1)
add_task(tasks, '零优先级', 0)
add_task(tasks, '正优先级', 1)
check('负数 priority 排序',
      tasks[0]['priority'] == 1 and tasks[1]['priority'] == 0 and tasks[2]['priority'] == -1,
      f'排序后 priority: {[t["priority"] for t in tasks]}')

print('')

# ==========================================
# 测试 3: title 前后空格 trim
# ==========================================
print('测试 3: title 前后空格 trim')

tasks = []
add_task(tasks, '  带空格的任务  ', 1)
check('title 被正确 trim',
      tasks[0]['title'] == '带空格的任务',
      f'实际 title: "{tasks[0]["title"]}"')

print('')

# ==========================================
# 测试 4: add_task 返回列表引用
# ==========================================
print('测试 4: add_task 返回列表引用')

tasks = []
result = add_task(tasks, '测试任务', 1)
check('add_task 返回同一个列表',
      result is tasks,
      f'result is tasks: {result is tasks}')

print('')

# ==========================================
# 测试 5: 多个相同优先级任务
# ==========================================
print('测试 5: 多个相同优先级任务')

tasks = []
add_task(tasks, '任务1', 5)
add_task(tasks, '任务2', 5)
add_task(tasks, '任务3', 5)
check('相同优先级任务数量',
      len(tasks) == 3,
      f'任务数量: {len(tasks)}')
check('相同优先级任务都能访问',
      all(t['priority'] == 5 for t in tasks),
      f'优先级: {[t["priority"] for t in tasks]}')

print('')

# ==========================================
# 测试 6: filter_by_priority 边界值
# ==========================================
print('测试 6: filter_by_priority 边界值')

tasks = []
add_task(tasks, '高', 5)
add_task(tasks, '中', 3)
add_task(tasks, '低', 1)
filtered = filter_by_priority(tasks, 3)
check('filter_by_priority 包含等于 min_priority 的任务',
      len(filtered) == 2 and any(t['priority'] == 3 for t in filtered),
      f'filtered: {[t["priority"] for t in tasks]}')

print('')
print('=' * 40)
print(f'结果: {passed} 通过, {failed} 失败')
print('=' * 40)

if failed > 0:
    print('\n⚠️  有测试失败')
    sys.exit(1)
else:
    print('\n✅ 所有补充测试通过')