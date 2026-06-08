# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 语言偏好 / Language
- 使用中文进行所有交互。

## Python 环境 / Python Environment
- 使用 `uv venv` 管理虚拟环境。
- 使用 `uv pip` 安装包。
- pip 镜像源使用阿里云: `-i https://mirrors.aliyun.com/pypi/simple/`

### 常用命令
```bash
# 创建并激活虚拟环境
uv venv
source .venv/bin/activate

# 安装依赖
uv pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 安装开发依赖
uv pip install -r requirements-dev.txt -i https://mirrors.aliyun.com/pypi/simple/
```

## 项目说明
- 项目名称: funasr-flow，预计是一个基于 FunASR 的语音识别流程项目。
- 当前处于初始状态，尚未包含任何业务代码。
- FunASR: 阿里达摩院端到端语音识别工具包 (https://github.com/modelscope/FunasR)

## 技能/Skills
本仓库预装了来自 `mattpocock/skills` 的技能集，详见 `skills-lock.json`。

## Agent skills

### Issue tracker

Issues and PRDs are tracked as local markdown files under `.scratch/<feature-slug>/`. See `docs/agents/issue-tracker.md`.

### Triage labels

Uses the default canonical label vocabulary: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context repo — one `CONTEXT.md` at the root, one `docs/adr/` directory. See `docs/agents/domain.md`.
