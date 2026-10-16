---
title: "思维链提示"
type: concept
tags: ["提示工程", "推理"]
sources: ["01-原始资料/02-转录/Prompt_Engineering_Full_Course.md"]
last_updated: 2026-10-15
---

## 核心认识

Chain of Thought（CoT）提示引导模型分步求解，再给出答案。[[prompt-engineering-full-course]] 的 18:10–20:04 将其用于数学、逻辑、规划与比较任务。

## 适用条件与证据

讲者同时指出，现代推理模型可能已经自动进行相应处理，因此额外加入逐步推理指令的重要性依模型和使用方式而变。讲者没有在演示中运行算术例子的提示对照，因为预计当前所用模型两种提示都会得到类似结果。

因此，课程支持将 CoT 作为可选策略理解，不能据此主张每次任务都必须加固定措辞，也不能将讲者对推理模型内部编排的简化解释视为已核实的实现细节。

## 关联连接

- [[prompt-engineering-full-course]] — 概念讲解与限制
- [[Prompt_Engineering]] — 根据任务选择策略
- [[Prompt_Chaining]] — 多次调用的任务分阶段，与单次分步求解区别
