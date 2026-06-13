# -*- coding: utf-8 -*-
"""
AI 情报站 · 每日采集脚本（Kimi / Moonshot 版）
对监控清单逐家联网检索 -> 生成结构化 JSON -> 写入 data/ 目录。
配合 GitHub Actions 定时运行并提交，GitHub Pages 渲染成网页。

环境变量：MOONSHOT_API_KEY  （在 https://platform.moonshot.cn 获取）
依赖：pip install openai
"""

import os
import re
import sys
import json
import time
import datetime

from openai import OpenAI

# ---- 监控清单：改这里即可增删公司 ----
COMPANIES = [
    # -- 国内 --
    {"name": "字节跳动", "focus": "AI战略、Seed/豆包大模型、TikTok AI、算力与芯片、组织人事变动"},
    {"name": "阿里巴巴", "focus": "通义千问/Qwen、阿里云AI、资本开支、夸克"},
    {"name": "腾讯", "focus": "混元大模型、元宝、AI资本开支、微信AI"},
    {"name": "MiniMax", "focus": "模型发布、融资、海螺AI、商业化进展"},
    # -- 海外 --
    {"name": "Anthropic", "focus": "Claude模型发布、安全研究、融资估值、企业合作、政策动向", "en": "Anthropic Claude"},
    {"name": "OpenAI", "focus": "GPT模型、产品发布、融资与算力合约、组织人事、Sora", "en": "OpenAI ChatGPT"},
    {"name": "Google", "focus": "Gemini模型、DeepMind研究、AI产品集成、TPU与基建", "en": "Google Gemini DeepMind"},
]

MODEL = "kimi-k2.5"
BASE_URL = "https://api.moonshot.cn/v1"   # 海外用 https://api.moonshot.ai/v1
TZ = datetime.timezone(datetime.timedelta(hours=8))
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
MAX_SEARCH_ROUNDS = 5   # 每家公司最多允许的搜索往返次数

SEARCH_TOOL = [{"type": "builtin_function", "function": {"name": "$web_search"}}]


def research(client, company):
    """对单家公司：发起对话 -> 循环响应 $web_search 工具调用 -> 拿到最终JSON。"""
    today = datetime.datetime.now(TZ).strftime("%Y年%m月%d日")
    en_hint = f"（英文检索关键词可用：{company['en']}）" if company.get("en") else ""
    prompt = f"""今天是{today}。请联网检索「{company['name']}」过去48小时的最新动态，关注：{company['focus']}。{en_hint}
优先官方信源与主流科技财经媒体（含 Reuters、Bloomberg、TechCrunch、The Information、36氪、晚点等）。

检索完成后，只输出一个JSON数组作为最终回答，不要任何其他文字、不要markdown代码块：
[{{"t":"事件一句话概括（中文）","s":"信源名称","u":"原文链接（没有则空字符串）","r":false}}]
r 为 true 表示来自传闻/知情人士。最多5条，按重要性排序。无重要动态则输出 []"""

    messages = [
        {"role": "system", "content": "你是一名严谨的AI产业情报分析师，只依据检索到的信息作答，不编造。"},
        {"role": "user", "content": prompt},
    ]

    for _ in range(MAX_SEARCH_ROUNDS):
        completion = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=8192,
            temperature=0.3,
            extra_body={"thinking": {"type": "disabled"}},  # 联网搜索需关闭思考模式
            tools=SEARCH_TOOL,
        )
        choice = completion.choices[0]
        msg = choice.message

        if choice.finish_reason == "tool_calls":
            # 把助手消息原样加回，并对每个 $web_search 调用回填 arguments（Kimi官方约定）
            messages.append(msg.model_dump())
            for tc in msg.tool_calls:
                if tc.function.name == "$web_search":
                    args = tc.function.arguments  # 已是JSON字符串
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "name": "$web_search",
                        "content": args,  # 原样返回即可，平台自动执行搜索
                    })
            continue

        # 正常结束：解析最终文本
        text = msg.content or ""
        m = re.search(r"\[.*\]", text.replace("```json", "").replace("```", ""), re.S)
        if not m:
            return []
        items = json.loads(m.group(0))
        return [x for x in items if isinstance(x, dict) and x.get("t")]

    return [{"t": "检索超过最大轮次，未得到结果", "s": "系统", "u": "", "r": False}]


def main():
    api_key = os.environ.get("MOONSHOT_API_KEY")
    if not api_key:
        sys.exit("缺少环境变量 MOONSHOT_API_KEY")
    client = OpenAI(api_key=api_key, base_url=BASE_URL)

    date = datetime.datetime.now(TZ).strftime("%Y-%m-%d")
    brief = {"date": date, "generated_at": datetime.datetime.now(TZ).isoformat(), "companies": []}

    for c in COMPANIES:
        print(f"检索 {c['name']} ...")
        try:
            items = research(client, c)
        except Exception as e:
            items = [{"t": f"检索失败：{type(e).__name__}: {e}", "s": "系统", "u": "", "r": False}]
        brief["companies"].append({"name": c["name"], "items": items})
        time.sleep(2)

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(os.path.join(DATA_DIR, f"{date}.json"), "w", encoding="utf-8") as f:
        json.dump(brief, f, ensure_ascii=False, indent=1)

    dates = sorted(
        (fn[:-5] for fn in os.listdir(DATA_DIR) if re.fullmatch(r"\d{4}-\d{2}-\d{2}\.json", fn)),
        reverse=True,
    )[:90]
    with open(os.path.join(DATA_DIR, "index.json"), "w", encoding="utf-8") as f:
        json.dump({"dates": dates}, f, ensure_ascii=False)

    print(f"已生成 data/{date}.json，索引共 {len(dates)} 天")


if __name__ == "__main__":
    main()
