# -*- coding: utf-8 -*-
"""
AI 情报站 · 每日采集脚本
对监控清单逐家联网检索 -> 生成结构化 JSON -> 写入 data/ 目录。
配合 GitHub Actions 定时运行并提交，GitHub Pages 渲染成网页。

环境变量：ANTHROPIC_API_KEY
"""

import os
import re
import sys
import json
import time
import datetime

import anthropic

COMPANIES = [
    {"name": "字节跳动", "focus": "AI战略、Seed/豆包大模型、TikTok AI、算力与芯片、组织人事变动"},
    {"name": "阿里巴巴", "focus": "通义千问/Qwen、阿里云AI、资本开支、夸克"},
    {"name": "腾讯", "focus": "混元大模型、元宝、AI资本开支、微信AI"},
    {"name": "MiniMax", "focus": "模型发布、融资、海螺AI、商业化进展"},
]
MODEL = "claude-sonnet-4-6"
TZ = datetime.timezone(datetime.timedelta(hours=8))
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def research(client, name, focus):
    today = datetime.datetime.now(TZ).strftime("%Y年%m月%d日")
    prompt = f"""今天是{today}。请联网检索「{name}」过去48小时的最新动态，关注：{focus}。
优先官方信源与主流科技财经媒体（36氪、晚点、界面、财新、Reuters、Bloomberg等）。

检索完成后，只输出一个JSON数组，不要任何其他文字、不要markdown代码块：
[{{"t":"事件一句话概括","s":"信源名称","u":"原文链接（没有则留空字符串）","r":false}}]
r 为 true 表示来自传闻/知情人士。最多5条，按重要性排序。无重要动态则输出 []"""
    resp = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 4}],
    )
    text = "\n".join(b.text for b in resp.content if b.type == "text")
    m = re.search(r"\[.*\]", text.replace("```json", "").replace("```", ""), re.S)
    if not m:
        return []
    items = json.loads(m.group(0))
    return [x for x in items if isinstance(x, dict) and x.get("t")]


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("缺少环境变量 ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=api_key)

    date = datetime.datetime.now(TZ).strftime("%Y-%m-%d")
    brief = {"date": date, "generated_at": datetime.datetime.now(TZ).isoformat(), "companies": []}

    for c in COMPANIES:
        print(f"检索 {c['name']} …")
        try:
            items = research(client, c["name"], c["focus"])
        except Exception as e:
            items = [{"t": f"检索失败：{type(e).__name__}: {e}", "s": "系统", "u": "", "r": False}]
        brief["companies"].append({"name": c["name"], "items": items})
        time.sleep(2)

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(os.path.join(DATA_DIR, f"{date}.json"), "w", encoding="utf-8") as f:
        json.dump(brief, f, ensure_ascii=False, indent=1)

    # 维护日期索引（最近90天）
    dates = sorted(
        (fn[:-5] for fn in os.listdir(DATA_DIR) if re.fullmatch(r"\d{4}-\d{2}-\d{2}\.json", fn)),
        reverse=True,
    )[:90]
    with open(os.path.join(DATA_DIR, "index.json"), "w", encoding="utf-8") as f:
        json.dump({"dates": dates}, f, ensure_ascii=False)

    print(f"✅ 已生成 data/{date}.json，索引共 {len(dates)} 天")


if __name__ == "__main__":
    main()
