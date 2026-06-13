# AI 情报站（网站版 · Kimi 驱动）

每天自动收集 7 家公司的最新动态，GitHub Actions 定时联网检索并提交数据，GitHub Pages 免费托管网页。
**手机浏览器输入网址即可查看，可分享，可保存到主屏幕当 App 用。**

监控清单：

- 国内：字节跳动 / 阿里巴巴 / 腾讯 / MiniMax
- 海外：Anthropic / OpenAI / Google

采集由 **Kimi（Moonshot）API** 的内置联网搜索 `$web_search` 完成。

## 文件说明

|文件          |作用                          |放置位置                                  |
|------------|----------------------------|--------------------------------------|
|`collect.py`|每日采集脚本（调用 Kimi 联网检索，输出 JSON）|仓库根目录                                 |
|`index.html`|网页（读取 data/ 下的 JSON 渲染日报）   |仓库根目录                                 |
|`daily.yml` |定时任务配置                      |**必须移到 `.github/workflows/daily.yml`**|

## 部署步骤（约 10 分钟）

1. **建仓库**：GitHub 新建 **Public** 仓库，上传三个文件，把 `daily.yml` 放到 `.github/workflows/` 目录
1. **配 API Key**：先到 <https://platform.moonshot.cn> 注册并创建 API Key；
   仓库 Settings → Secrets and variables → Actions → 新建 Secret，名称 `MOONSHOT_API_KEY`，值为你的密钥
1. **开启网站**：Settings → Pages → Source 选 “Deploy from a branch” → Branch 选 `main`、目录 `/ (root)` → Save
1. **首次运行**：Actions 页签 → “每日采集 AI 情报” → Run workflow，跑完访问
   `https://你的用户名.github.io/仓库名/`
1. 之后每天北京时间 8:30 自动更新

## 如何调整监控对象

编辑 `collect.py` 顶部的 `COMPANIES` 列表，每家一行字典：

```python
{"name": "公司名", "focus": "关注重点1、关注重点2、..."}
```

- **加海外公司**：建议多加一个 `"en"` 字段提供英文检索关键词，命中外媒更准，例如：
  `{"name": "Meta", "focus": "Llama模型、AI眼镜、超算集群", "en": "Meta Llama AI"}`
- **删公司**：直接删掉对应那一行
- **调关注点**：改 `focus` 里的内容，越具体检索越聚焦
- 改完提交到仓库即可，下次定时运行自动生效

网页端无需改动——它按 JSON 里的公司顺序自动渲染分组。

## 其他自定义

- **推送时间**：改 `daily.yml` 的 cron（UTC 时间 = 北京时间 − 8 小时）
- **保留天数**：`collect.py` 中索引默认保留最近 90 天
- **每家搜索上限**：`collect.py` 的 `MAX_SEARCH_ROUNDS`
- **换模型**：`collect.py` 的 `MODEL`（如未来的 kimi-k2.6）

## 成本

GitHub Actions 与 Pages 免费额度足够。Kimi 联网搜索约每次 ¥0.03，
7 家公司 × 每天数次检索，日成本约 ¥1–2，外加少量 token 费用。

## 注意

- Public 仓库的日报数据任何人可见（API Key 在 Secrets 中不会泄露）。介意可改用 Cloudflare Pages + 私有仓库
- 海外公司检索如命中外媒原文，链接可能需科学上网才能打开，但摘要本身为中文
- 结果为 AI 整理，传闻类已标注，重要信息请点信源链接核对
