# AI 情报站（网站版）

一个每天自动收集字节跳动 / 阿里 / 腾讯 / MiniMax 最新动态的网站。
GitHub Actions 每天定时联网检索并提交数据，GitHub Pages 免费托管网页。
**手机浏览器输入网址即可查看，可分享给任何人，可保存到手机主屏幕当 App 用。**

## 文件说明

|文件          |作用                                |放置位置                                  |
|------------|----------------------------------|--------------------------------------|
|`collect.py`|每日采集脚本（调用 Claude API 联网检索，输出 JSON）|仓库根目录                                 |
|`index.html`|网页（读取 data/ 下的 JSON 渲染日报）         |仓库根目录                                 |
|`daily.yml` |定时任务配置                            |**必须移到 `.github/workflows/daily.yml`**|

## 部署步骤（约 10 分钟）

1. **建仓库**：GitHub 新建一个 **Public** 仓库（Pages 免费版要求公开），上传三个文件，注意把 `daily.yml` 放到 `.github/workflows/` 目录下
1. **配 API Key**：仓库 Settings → Secrets and variables → Actions → 新建 Secret，名称 `ANTHROPIC_API_KEY`，值为你在 <https://console.anthropic.com> 创建的密钥（确认 Console 中已启用 Web Search）
1. **开启网站**：Settings → Pages → Source 选 “Deploy from a branch” → Branch 选 `main`、目录选 `/ (root)` → Save
1. **首次运行**：Actions 页签 → 选”每日采集 AI 情报” → Run workflow。跑完后访问
   `https://你的用户名.github.io/仓库名/` 即可看到首期日报
1. 之后每天北京时间 8:30 自动更新，无需任何操作

## 手机上当 App 用

Safari / Chrome 打开网址 → 分享 → “添加到主屏幕”，图标点开就是全屏的情报站。

## 自定义

- **监控清单**：改 `collect.py` 顶部 `COMPANIES`，每家可写不同关注重点
- **推送时间**：改 `daily.yml` 的 cron（UTC 时间 = 北京时间 − 8 小时）
- **保留天数**：`collect.py` 中索引默认保留最近 90 天
- **叠加微信推送**：可与之前的企业微信 webhook 方案并存——在 `collect.py` 末尾加一段推送代码即可，需要时找 Claude 要

## 成本

GitHub Actions 与 Pages 免费额度完全够用。唯一成本是 Anthropic API：
4 家公司 × 每家最多 4 次检索，每天约 ¥1–3。

## 注意

- 仓库是公开的，意味着日报数据任何人可见（API Key 在 Secrets 中，不会泄露）。介意的话可用私有仓库 + 其他静态托管（Cloudflare Pages 支持私有仓库免费托管）
- 检索结果为 AI 整理，传闻类已标注，重要信息请点击信源链接核对原文
