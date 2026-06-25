from models.record import Record


SUMMARY_TEMPLATES = {
    "excellent": "本次学习了【{subject}】的【{chapter}】章节，时长{duration}小时。"
                 "理解度很高（{rating}/5），学习状态优秀！建议继续保持，可以尝试挑战更高难度的内容。",
    "good": "本次学习了【{subject}】的【{chapter}】章节，时长{duration}小时。"
            "理解度良好（{rating}/5），掌握情况不错。建议定期复习巩固，加深记忆。",
    "normal": "本次学习了【{subject}】的【{chapter}】章节，时长{duration}小时。"
              "理解度一般（{rating}/5），建议针对薄弱环节进行专项复习，可通过做题和查阅资料加强理解。",
    "weak": "本次学习了【{subject}】的【{chapter}】章节，时长{duration}小时。"
            "理解度较低（{rating}/5），存在疑问：{problems}。"
            "建议重点复习相关内容，可以寻求帮助或参考多种学习资源。",
    "no_problems": "本次学习了【{subject}】的【{chapter}】章节，时长{duration}小时。"
                   "理解度{rating}/5，学习过程顺利，未遇到明显问题。"
}


def generate_summary(record: Record) -> str:
    if record.self_rating >= 5:
        template = SUMMARY_TEMPLATES["excellent"]
    elif record.self_rating >= 4:
        template = SUMMARY_TEMPLATES["good"]
    elif record.self_rating >= 3:
        if record.problems and record.problems.strip():
            template = SUMMARY_TEMPLATES["normal"]
        else:
            template = SUMMARY_TEMPLATES["no_problems"]
    else:
        if record.problems and record.problems.strip():
            template = SUMMARY_TEMPLATES["weak"]
        else:
            template = SUMMARY_TEMPLATES["normal"]

    return template.format(
        subject=record.subject,
        chapter=record.chapter,
        duration=record.duration,
        rating=record.self_rating,
        problems=record.problems if record.problems else "无"
    )
