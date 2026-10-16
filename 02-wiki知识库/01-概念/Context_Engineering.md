---
title: "上下文工程"
type: concept
tags: ["上下文", "提示工程"]
sources: ["01-原始资料/02-转录/Prompt_Engineering_Full_Course.md"]
last_updated: 2026-10-15
---

## 核心认识

本页用上下文工程归纳课程中关于模型可见信息的组织方法。[[prompt-engineering-full-course]] 的 7:05–10:39 指出，应用可能将历史、文件、工具和额外指令与用户请求一起提供给模型，因此当前输入不一定是完整上下文。

## 会话与持续设定

13:54–14:23 通过新会话减少前一个演示的影响；17:41–18:04 则利用同一会话中的既有示例继续处理反馈。36:03–36:25 提醒在新会话或长线程中重述、总结关键事实，避免假定旧信息始终可用。

29:13–31:21 用 system/user prompts 说明持续角色、规则与当次任务的差别，并用自定义指令改变语气。此类比用于理解持续设定，不等于已经核实某个应用内部如何拼接消息或实现记忆。

## 关联连接

- [[prompt-engineering-full-course]] — 上下文与会话演示
- [[Prompt_Engineering]] — 当前任务与背景
- [[Interview_Style_Prompting]] — 通过提问补齐信息
- [[Prompt_Chaining]] — 为后续阶段提供必要产物
