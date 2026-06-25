from storage.config_store import ConfigStore


def show_config(config_store: ConfigStore):
    config = config_store.load_config()

    print("━" * 40)
    print("[当前配置]")
    print("━" * 40)

    print(f"\n[用户信息]")
    print(f"  姓名：{config.user.name}")
    print(f"  目标日期：{config.user.target_date}")
    print(f"  每日目标：{config.user.daily_goal_hours} 小时")

    print(f"\n[考试科目]")
    for subject in config.subjects:
        print(f"  - {subject.name} ({len(subject.chapters)} 个章节)")

    print(f"\n[算法参数]")
    print(f"  薄弱阈值：{config.thresholds.weakness_score}")
    print(f"  遗忘天数：{config.thresholds.forget_days} 天")
    print(f"  最大时长：{config.thresholds.max_daily_hours} 小时/天")

    print(f"\n[可用配置项]")
    print(f"  user.name            - 用户姓名")
    print(f"  user.target_date     - 目标考试日期")
    print(f"  user.daily_goal_hours - 每日学习目标")
    print(f"  thresholds.weakness_score - 薄弱知识点阈值")
    print(f"  thresholds.forget_days    - 遗忘天数阈值")

    print("━" * 40)


def execute(args=None):
    config_store = ConfigStore()

    if not args or not args.set:
        show_config(config_store)
        return

    key = args.set
    value = args.value

    if not value:
        print(f"[错误] 请提供配置值：python cli.py config --set {key} <value>")
        return

    success = config_store.set_value(key, value)
    if success:
        print(f"[成功] 配置已更新：{key} = {value}")
    else:
        print(f"[错误] 未知配置项：{key}")
        print("可用配置项：user.name, user.target_date, user.daily_goal_hours, thresholds.weakness_score, thresholds.forget_days")
