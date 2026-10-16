---
title: "结构化输出"
type: concept
tags: ["提示工程", "结构化输出"]
sources: ["01-原始资料/02-转录/Prompt_Engineering_Full_Course.md"]
last_updated: 2026-10-15
---

## 核心认识

本次来源中的结构化输出，是通过提示约定 JSON、XML、表格、Markdown 或固定文本形状，使结果便于解析与复用。[[prompt-engineering-full-course]] 的 20:05–22:03 演示给定 JSON 形状并要求只返回该格式，以便供代码、API 或数据库使用。

## 实践要点与限制

说明目标形状，提供示例，并明确是否允许附加文字；35:45–36:03 再次强调明确键与仅输出 JSON。工单标题案例也体现单行固定形状的价值。

课程转录未完整列出屏幕上的 schema，也没有展示独立解析器或 schema 校验过程。提示要求有效 JSON 与输出已通过校验是两件事；不能把讲者的单次观察当成所有结果均可解析、字段完整或事实准确的保证。本页也不据此推断使用了 API 层的强制结构化能力。

## 关联连接

- [[prompt-engineering-full-course]] — JSON 输出演示
- [[Prompt_Engineering]] — 明确格式要求
- [[Few_Shot_Prompting]] — 输入输出形状示范
- [[Prompt_Chaining]] — 传递可复用的中间产物
