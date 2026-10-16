---
title: "提示链"
type: concept
tags: ["提示工程", "工作流"]
sources: ["01-原始资料/02-转录/Prompt_Engineering_Full_Course.md"]
last_updated: 2026-10-15
---

## 核心认识

Prompt chaining 将复杂任务分为多个调用或阶段，把前一步输出交给下一步，并检查中间产物。[[prompt-engineering-full-course]] 的 31:22–32:15 给出“大纲→正文→SEO 标题与描述”的例子，未现场运行这一流程。

## 评审与修改

32:16–33:16 建议按清晰度、完整性评分，再提出最重要的修改并据此改稿。讲者还建议用新会话或改变作者归属获得更客观的评价，但转录没有提供比较证据；本页将其保留为来源经验，不把自评分数当作独立质量验证。

## 适用边界

分链适合需要逐阶段检查或容易遗漏子任务的工作。课程称此法通常更好，但未给出足以证明所有任务都应拆分的数据。提示链侧重跨调用组织任务，与单次调用中的逐步求解不同。

## 关联连接

- [[prompt-engineering-full-course]] — 分链与评审建议出处
- [[Prompt_Engineering]] — 拆分过多任务
- [[Chain_of_Thought]] — 单次分步求解
- [[Context_Engineering]] — 传递必要上下文
- [[Structured_Output]] — 约定中间产物形状
