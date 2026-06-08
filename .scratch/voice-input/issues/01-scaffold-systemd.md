Status: ready-for-agent

# 01 — 项目脚手架 + systemd 集成

## Parent

[PRD: FunASR 语音输入](../PRD.md)

## What to build

搭建项目骨架：Python 包结构、`pyproject.toml`、CLI 入口、systemd user unit 模板，以及一个能启动并常驻的空守护进程。

用户执行 `uv tool install .` 后，可用 `funasr-flow install` 安装 systemd unit，用 `start/stop/status` 控制守护进程生命周期。守护进程启动后前台运行（由 systemd 管理），初始只打印日志，不做任何实际工作。

状态机定义三个状态 `IDLE | RECORDING | TRANSCRIBING`，初始始终为 IDLE。

## Acceptance criteria

- [ ] `pyproject.toml` 配置完整，`[project.scripts]` 定义 `funasr-flow` 入口
- [ ] `uv tool install .` 可成功安装
- [ ] `funasr-flow install` 将 systemd user unit 写入 `~/.config/systemd/user/funasr-flow.service`
- [ ] `funasr-flow start` 等价于 `systemctl --user start funasr-flow`
- [ ] `funasr-flow stop` 等价于 `systemctl --user stop funasr-flow`
- [ ] `funasr-flow status` 等价于 `systemctl --user status funasr-flow`
- [ ] `funasr-flow uninstall` 停止服务并删除 unit 文件
- [ ] 守护进程启动后在前台保持运行（不退出）
- [ ] `state.py` 定义 `State` 枚举：`IDLE`、`RECORDING`、`TRANSCRIBING`
- [ ] systemd unit 配置日志输出到 journald

## Blocked by

None — can start immediately.
