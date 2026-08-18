# Personal AI OS V1.0 前端 UI/UX 设计

> 项目：Personal AI OS  
> 定位：开源、Local First 的个人认知操作系统  
> 当前主模型：DeepSeek（通过 Model Gateway 解耦）  
> 核心原则：Your Data. Your Memory. Your AI.  
> 文档状态：研发基线，可随代码迭代同步更新


## 1. 信息架构

主导航：

- Chat
- Knowledge
- Memory
- Decisions
- Settings

V0.1 不把 Agent 放一级导航，避免尚未成熟的能力占据核心体验。

## 2. Chat

必须显示：
- 当前模型；
- 是否启用 Memory；
- 引用来源；
- 重试按钮；
- 错误状态。

Citation 点击后打开原文片段，不仅显示文件名。

## 3. Knowledge

列表字段：
- 文件名
- 类型
- 状态
- Chunk 数
- 更新时间
- 错误提示

上传后立即展示 processing 状态。

## 4. Memory

每条 Memory 卡片：
- 类型
- 内容
- 来源
- confidence
- status
- 编辑 / 确认 / 拒绝 / 删除

候选记忆与确认记忆必须视觉区分。

## 5. Decisions

结构化表单：
- 问题
- 背景
- 选项
- 选择
- 理由
- 风险
- 后续结果
- 复盘

## 6. UX 原则

- AI 不能偷偷“学会了”，必须可见；
- 任何长任务都显示状态；
- 错误要告诉用户下一步怎么办；
- Local First 设置中显示数据位置和模型连接状态。
