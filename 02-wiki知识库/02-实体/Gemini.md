---
title: "Gemini 与 Gemini API"
type: entity
tags: [模型, Gemini, API]
sources: ["01-原始资料/01-文章/提示设计策略    Gemini API.md"]
last_updated: 2026-10-16
---

## 实体说明

Gemini 是本库《提示设计策略｜Gemini API》文档讨论的模型系列，Gemini API 是文中调用模型及相关工具能力的接口。为避免同一资料拆出多个高度重叠的产品页面，本页集中记录系列与接口相关信息。

## 来源中的使用要点

- 通用策略强调清晰输入、少样本示例、一致格式、必要上下文，以及逐步试验提示措辞与生成参数。
- 剪藏中的 Gemini 3 指导偏好简洁直接的任务说明，关键规则放在系统指令或开头，长资料放在具体问题之前；多模态任务要清楚指明对应输入。
- 文档称 Gemini 2.5 和 3 系列支持内部思考；复杂智能体可显式控制规划、诊断、恢复和权限处理，并考虑词元与时延成本。
- 文档介绍复杂 JSON 架构的结构化输出、Google 搜索接地和 Python 代码执行；本次未核验各型号的具体支持范围。

上述均为创建于 2026-10-16 的本地剪藏内容；默认值、知识截点和型号能力不能自动推广为现行统一规范。完整摘要、示例限制与建议差异见 [[gemini-api-prompt-design-strategies]]。

## 关联连接

- [[gemini-api-prompt-design-strategies]] — 本页的文档来源摘要。
- [[Prompt_Engineering]] — 指令、示例、格式与规划方法。
- [[Context_Engineering]] — 上下文锚定及事实与计算工具的作用。
