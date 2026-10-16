## [2026-10-16] ingest | 提炼两份提示工程资料
- **变更**: 新建当前工作区中的 2 个摘要 [[anthropic-prompting-best-practices]]、[[prompt-engineering-full-course]]；3 个实体 [[Anthropic]]、[[Claude]]、[[Tech_With_Tim]]；2 个概念 [[Prompt_Engineering]]、[[Context_Engineering]]；更新 [[index]] 并建立关联双链。沿用已有命名，按本次正文重新编译，未恢复其他已删除知识页。
- **完成**: 完整读取 558 行文章与 1100 行课程转录；按 sources 相对路径精确检查，开始时摘要目录为空，2 份非归档来源均需导入。
- **跳过**: 默认排除 `01-原始资料/99-归档/The Complete Prompt Engineering Guide (2025).md`；完整已导入来源跳过 0 份。
- **冲突**: 在两个摘要及 [[Prompt_Engineering]] 中并列标注“正向描述与负面约束”“普遍拆步骤与按需拆步骤”的建议差异，保留来源与适用条件。
- **未完成**: 两份现有正文的导入无未完成项。Anthropic 剪藏中的预填充迁移场景列表缺失，未推测补写；模型/API 时效、宣传性性能结论与课程经验说法未作外部核验，已在页面标明边界。

- **校验**: 7 个知识页通过 YAML、来源存在性、类型、双链目标、摘要反向关联和索引覆盖检查；2 份非归档来源完整覆盖；全部原始资料哈希不变，日志保留本次开始时的全部内容。仅验证本地编译与结构，未运行材料中的示例工作流。

## [2026-10-16] ingest | 提炼 Gemini API 提示设计策略
- **变更**: 新增摘要 [[gemini-api-prompt-design-strategies]] 与实体 [[Gemini]]；增量更新 [[Prompt_Engineering]]、[[Context_Engineering]]；为 [[anthropic-prompting-best-practices]] 补充对照关联，更新 [[index]]。
- **完成**: 完整读取 `01-原始资料/01-文章/提示设计策略    Gemini API.md` 共 607 行；集中提炼 1 个实体和 2 个已有核心概念，保留原文件名中的四个空格。
- **跳过**: 按摘要 YAML sources 精确路径匹配，已有完整摘要与关联页的 Anthropic 文章、Tech With Tim 课程共 2 份不重复导入；默认排除归档资料 1 份。
- **冲突**: 在 [[Prompt_Engineering]] 与新增摘要标注强规划和减少过度思考的策略张力，并为原有拆分任务的差异补充 Gemini 来源；区分提示内补全与 API 消息预填充，避免误判为接口冲突。
- **未完成**: 本地正文导入无未完成项；模型规格、参数默认值、确定性和模板性能未在线核验，未运行文档中的示例或智能体模板，已在页面记录证据边界。

## [2026-10-16] query | 如何写好提示词
- **输出**: 即时回答未保存为综合页；整理任务、背景、输出格式、约束、示例和验收标准，提供可改写模板及访谈式澄清方法。
- **依据**: [[Prompt_Engineering]]、[[Context_Engineering]]、[[gemini-api-prompt-design-strategies]]、[[anthropic-prompting-best-practices]]、[[prompt-engineering-full-course]]。
- **冲突**: 保留正向描述与负面约束、任务拆分和规划强度的适用条件，不宣称存在跨模型通用最优写法。

## [2026-10-16] query | 保存如何写好提示词的回答
- **输出**: 已保存为综合页 [[how-to-write-good-prompts]]，保留六个要点、完整模板、摘要改写示例、访谈式提示与迭代建议；模板和示例标为依据 Wiki 整理，未经效果实验。
- **变更**: 更新 [[index]] 综合分类，并在 5 个依据页面补充反向关联。
- **依据**: [[Prompt_Engineering]]、[[Context_Engineering]]、[[prompt-engineering-full-course]]、[[anthropic-prompting-best-practices]]、[[gemini-api-prompt-design-strategies]]；综合页 sources 为 []，正文引用实际依据的 Wiki 页面。
- **冲突**: 保留正向描述与负面约束、任务拆分与规划强度的适用条件；无新增未完成项。
