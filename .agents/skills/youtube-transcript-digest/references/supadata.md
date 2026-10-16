# Supadata 调用约定

本 skill 的链接解析、API 调用、任务轮询和字幕导出均由自身的 `scripts/transcript.py` 实现，仅依赖 Python 3.9+ 标准库。所有运行所需约定在本文和 `SKILL.md` 中，不需要其他本地项目。

官方文档：https://docs.supadata.ai/get-transcript 

- `GET https://api.supadata.ai/v1/transcript`
- Header：`x-api-key: <解析得到的 API Key>`。优先读取非空的 `SUPADATA_API_KEY` 环境变量；未设置或空白时，读取当前用户的 `~/.superdata` 文件。文件为 UTF-8 单行纯文本 API Key，可有末尾换行，权限建议为 `600`；不接受 JSON、`KEY=value` 或多行配置。读取失败、内容为空或认证失败时明确报错，不打印密钥。离线导入不读取任何密钥。
- Query：`url=https://www.youtube.com/watch?v=<video-id>`、`text=false`、`mode=native`。可选 `lang` 是源字幕的偏好语言；缺少指定语言时服务可能回退到其他轨道，应核对返回的 `lang` / `availableLangs`。
- `mode=native` 只抓已有字幕；`auto` 可回退到 AI 生成；`generate` 总是生成。文档当前写明 native 请求 1 credit，生成每分钟 2 credits。后两种模式仅在用户要求转录时使用，价格变更以官方文档为准。
- HTTP 200：`{"content":[{"text":"...","offset":1234,"duration":2500,"lang":"en"}],"lang":"en","availableLangs":["en"]}`。`offset`、`duration` 均为毫秒。脚本暂存完整 API 文本在 `source.json`，逐条 ID 用于内部校验。只导出一份原始字幕 Markdown，包含 Obsidian 剪藏格式的 YAML、视频嵌入、完整原始简介、原文章节和逐条时间戳，不翻译或总结。
- HTTP 202：`{"jobId":"..."}`；轮询 `GET https://api.supadata.ai/v1/transcript/<jobId>`，同一 header。状态为 queued、active、completed、failed。兼容 completed 结果直接带 `content`，或嵌在 `result` 内。
- 默认每秒轮询，最多 40 次；超时报告 jobId，使用 `--job-id` 恢复。同一任务不重新提交。文档注明完成结果保留一小时。
- 本 skill 对 HTTP 206 的处理约定：未取得完整原生字幕，不输出成功结果，也不自动切换 AI 转录。401 为认证问题，402 为额度问题，403 为访问受限，404 为无视频/字幕或任务失效，429 为限流。空字幕不能生成看似成功的交付文件。

## 视频链接与时间轴

- 视频 ID 必须是 11 位 ASCII 字母、数字、`_` 或 `-`。
- 接受 `youtube.com`、`www.youtube.com`、`m.youtube.com`、`music.youtube.com` 的 `/watch?v=<id>`、`/shorts/<id>`、`/embed/<id>`、`/live/<id>`；接受 `youtu.be/<id>` 和 `youtube-nocookie.com` / `www.youtube-nocookie.com` 的 `/embed/<id>`，也可直接输入 ID。
- 只接受 HTTP/HTTPS 的确切域名，不接受伪装域名、频道链接或纯播放列表链接。`live` 路径支持提取 ID，不代表正在直播的视频可获取字幕；服务仅支持已完成的视频。
- API 只接收规范 URL `https://www.youtube.com/watch?v=<id>`，不包含列表、推荐来源或起播时间等额外参数。
- 每条字幕按 API 顺序分配稳定数字 ID，起点来自 `offset`，终点为 `offset + duration`，毫秒四舍五入为整数后留在内部工作数据。Markdown 中按起点向下取整到秒显示 `**M:SS** · 原始文本`（超过一小时为 `**H:MM:SS** · 原始文本`）。缺少文本、无效时间、零时长、乱序或空字幕直接报错，不改写字幕或显示内部 ID。

## 离线复现

将 API 原始响应保存为 JSON，使用 `fetch URL --input-json response.json --output <目录>` 可以离线导入，不读取 Key、不访问网络。不能将模拟响应声称为真实视频获取结果。用 `python3 -m unittest discover -s <SKILL_DIR>/tests -v` 跑脚本测试。

## 工作数据与交付目录

从仓库根目录运行时，`fetch` 默认在 `01-原始资料/02-转录/` 下新建带任务标记的 `youtube-transcript-*` 工作目录，返回的 `directory` 是其中的 `<video-id>/`，用于暂存 API 原始响应、字幕 ID/时间轴和元数据。离线导入使用同一规则，不使用系统临时目录，不新建 `99-工作文件/`。`fetch --output` 仅保留用于显式指定工作根目录的兼容场景，其无标记目录不支持自动清理；通常不传此参数。

`render` 只生成 `<输出目录>/<视频简短标题>.md`，不创建视频交付子目录。`short_title` 取自元数据或 `--short-title`，空格和标点替换为下划线，不包含扩展名。`render` 和 `check` 只需相同的 `directory`、`--metadata`、`--short-title` 与 `--output`，无需译文或总结参数。`--output` 指定最终输出目录，默认是仓库根目录下的 `01-原始资料/02-转录/`。同名文件不覆盖，修订时使用带版本号的新短标题。Agent 必须运行 `check --cleanup`，脚本确认原始字幕、元数据、章节和时间戳与文件一致后，删除本次带标记的专用工作目录。校验失败、未知文件或路径保护不通过时保留工作数据并报告原因；失败或中断时提供工作路径以便恢复。历史工作目录不自动清理，校验不代表已核实音轨或字幕识别准确性。
