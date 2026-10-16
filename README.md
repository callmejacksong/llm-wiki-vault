# LLM Wiki 知识库 · Codex

基于 [Karpathy 的 LLM Wiki 理念](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) 构建的 Obsidian 知识库：用 Codex 将原始资料编译成结构化、可追溯、相互链接的知识网络，用 Obsidian 阅读和浏览。

## 目录结构

```text
karpathy-llm-wiki-vault/
├── AGENTS.md                       # Codex 项目约定
├── .agents/skills/                 # 仓库级技能
│   ├── ingest/SKILL.md             # 导入原始资料
│   ├── query/SKILL.md              # 检索和综合回答
│   ├── lint/SKILL.md               # 知识库健康检查
│   └── youtube-transcript-digest/  # YouTube 原始字幕
├── 01-原始资料/
│   ├── 01-文章/                    # 网页剪藏、技术文章
│   ├── 02-转录/                    # 视频、播客转录
│   │   └── <视频简短标题>.md      # 单份原始字幕 Markdown
│   ├── 03-论文/                    # 论文、研报
│   └── 99-归档/                    # 历史归档
├── 02-wiki知识库/
│   ├── index.md                    # 分类索引
│   ├── log.md                      # 追加式操作日志
│   ├── 01-概念/                    # 概念、框架和方法论
│   ├── 02-实体/                    # 人物、公司和产品
│   ├── 03-摘要/                    # 原始资料摘要
│   └── 04-综合/                    # 跨资料综合分析
└── 99-附件/                        # 图片、PDF、附件
```

## 在 Codex 中使用

1. 在 Codex 中打开本仓库根目录作为工作目录。若已安装并登录 Codex CLI，也可以在仓库根目录运行 `codex`。
2. 开始新会话，让 Codex 加载根目录的 `AGENTS.md` 和 `.agents/skills/` 中的技能。迁移前已打开的会话建议重新开启。
3. 在对话框中输入下列请求；这些是对话提示，不是终端命令。

```text
$ingest
$ingest "01-原始资料/01-文章/Prompting best practices-Anthropic.md"
$query 我的知识库里，Few-shot 和 Chain of Thought 有什么区别？
$lint
$youtube-transcript-digest https://www.youtube.com/watch?v=视频ID
```

也可以直接说“将这篇资料导入知识库”“查询我的笔记中关于提示工程的内容”或“检查知识库健康状况”。如果技能没有出现在当前会话中，重启 Codex；也可以明确要求读取 `.agents/skills/ingest/SKILL.md` 等对应文件后执行。

Codex 使用 `AGENTS.md` 提供项目指令，通过 `.agents/skills/` 发现仓库技能，详见 [项目指令官方文档](https://developers.openai.com/codex/guides/agents-md) 和 [技能官方文档](https://developers.openai.com/codex/skills)。旧 `/ingest`、`/query`、`/lint` 已改为上面的技能调用方式。

## 工作流约定

- **导入**：手动将新资料放入 `01-原始资料/`，再让 Codex 导入。批量导入默认跳过历史归档、字幕工作文件和已有完整来源摘要的文件；指定路径可重新提炼并增量更新。原始文件始终保留原位，不再自动归档。
- **查询**：先读取索引与相关页面，回答附带 `[[页面名称]]` 引用。需要保存研究结论时，直接说“查询并保存为综合笔记”。
- **巡检**：`$lint` 输出问题报告并追加日志；“只读检查，不写日志”会完全只读。需要修复时可直接说“检查并修复死链和缺失索引”。知识冲突会保留双方来源并标注。
- **PDF**：使用当前环境可用的文本提取工具。无法提取时会报告未完成，不会把文件名当作正文生成摘要。

本仓库的技能直接读写本地 Markdown，无需 Obsidian CLI、Claudian 或额外 MCP 服务。用 Obsidian 打开同一目录即可浏览双链与附件；不需要运行构建命令。

YouTube 技能使用 Python 3.9+ 标准库，通过 Supadata 获取字幕。在线获取需要 `SUPADATA_API_KEY` 环境变量或 `~/.superdata` 中的单行 Key；请勿将密钥写入仓库。默认直接输出 `01-原始资料/02-转录/<视频简短标题>.md`，例如 `Prompt_Engineering_Full_Course.md`，只生成一份原始字幕 Markdown，不新建交付子目录，不生成翻译或总结。文件保留 YAML 属性、视频嵌入、完整原始简介、原文章节和逐条时间戳。中间文件放在转录目录下的 `youtube-transcript-*` 专用工作目录，使用 `check --cleanup` 校验通过后删除本次工作目录，不创建 `99-工作文件/`。已有资料不覆盖，重名时使用带版本号或视频 ID 的新短标题，历史工作目录不自动删除。配套脚本支持离线导入已有字幕响应。技能复制自本地 `llm-wiki-knowledge-base` 仓库。


## 知识来源

- Google Gemini API 官方文档
- Anthropic Claude 最佳实践
- 各机构发布的 Prompt Engineering 白皮书
- 学术论文（如 5C Prompt Contracts）
