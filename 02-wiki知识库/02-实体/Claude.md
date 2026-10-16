---
title: "Claude"
type: entity
tags: [模型, Claude, 提示工程]
sources: ["01-原始资料/01-文章/Prompting best practices-Anthropic.md"]
last_updated: 2026-10-16
---

## 实体说明

Claude 是 [[Anthropic]] 开发的模型系列。本库剪藏的提示文档主要讨论 Opus 4.6、Sonnet 4.6、Haiku 4.5，并包含旧版本迁移建议。以下是材料版本中的描述，不构成当前型号目录或现行 API 规范。

## 来源中的使用特点

- 清晰、明确的指令，相关且多样的示例，以及区分指令与资料的 XML 标签，有助于表达预期输出。
- 文档对 Opus 4.6、Sonnet 4.6 推荐 adaptive thinking，并通过 effort 与任务复杂度调节推理；不应机械沿用旧版要求大量探索的提示。
- 长任务可借助进度文件、结构化测试记录和上下文压缩继续工作；这些行为需要应用环境提供相应工具与状态管理。
- 工具主动性、输出篇幅和格式均需明确表达；提示强度应结合模型行为调整，防止过度触发。

具体参数默认值、弃用信息和性能比较均保留在 [[anthropic-prompting-best-practices]] 的材料语境中，实施前需另行核验对应版本。

## 关联连接

- [[Anthropic]] — 开发方与文档发布方。
- [[Prompt_Engineering]] — 模型相关的指令、示例与推理方法。
- [[Context_Engineering]] — 长文档组织和跨窗口状态管理。
- [[anthropic-prompting-best-practices]] — 本页依据的文档摘要。
