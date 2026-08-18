# Personal AI OS V1.0 代码规范与 Git 管理

> 项目：Personal AI OS  
> 定位：开源、Local First 的个人认知操作系统  
> 当前主模型：DeepSeek（通过 Model Gateway 解耦）  
> 核心原则：Your Data. Your Memory. Your AI.  
> 文档状态：研发基线，可随代码迭代同步更新


## 1. 分支

轻量策略：

- `main`：始终可发布
- `feature/<issue>-<name>`
- `fix/<issue>-<name>`

开源早期不强制长期 develop 分支，降低维护成本。

## 2. Commit

Conventional Commits：
- feat
- fix
- refactor
- test
- docs
- chore

示例：
`feat(memory): add candidate confirmation flow`

## 3. Pull Request

必须包含：
- 解决的问题；
- 修改范围；
- 测试方法；
- 是否涉及 migration；
- UI 变化截图（如有）；
- 文档是否更新。

## 4. Python

- ruff
- black 或 ruff format
- mypy/pyright（核心模块）
- pytest

## 5. TypeScript

- eslint
- prettier
- strict mode

## 6. 禁止项

- API Key 入库或提交仓库；
- Router 中直接 SQL；
- 业务代码直接调用 DeepSeek SDK；
- 无 migration 修改 schema；
- AI 生成 JSON 不经 Pydantic 校验；
- 捕获 Exception 后静默忽略。
