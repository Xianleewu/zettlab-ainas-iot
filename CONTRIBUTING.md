# Contributing

Thanks for your interest in improving the Zettlab AINAS integration!
（中文版见下方 · [Chinese version below](#贡献指南简体中文)）

## Development setup

```bash
git clone https://github.com/xianleewu/zettlab-ainas-iot
cd zettlab-ainas-iot
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements_test.txt
```

## Workflow

```bash
ruff format .            # format
ruff check . --fix       # lint
pytest                   # run the test suite
pytest --cov=custom_components/zettlab_ainas --cov-report=term-missing
```

All of the above run in CI (`.github/workflows/test.yml`), plus Home Assistant
`hassfest` and HACS validation (`validate.yml`). PRs must pass them.

## Standards

- **Python 3.12+, fully async** — never block the event loop; use `aiohttp` and
  `hass.async_add_executor_job` for unavoidable blocking work.
- **Typed** — type hints on all signatures; `from __future__ import annotations`.
- The API client (`api.py`) is **transport-only** and must not import
  `homeassistant`.
- Keep the data model in `CLAUDE.md` (the verified ZettOS API contract) accurate
  when you touch endpoints.
- Add or update tests for any behavior change; target **≥ 80%** coverage.
- Don't commit device IPs, credentials, tokens, or `.env` files.

## Reverse-engineering helpers

`CLAUDE.md` documents the verified device API. Open items (fan-mode enum,
reboot/shutdown endpoints, UDP-9527 discovery, remote-ID) are listed there; if you
capture one, please update both the code and `CLAUDE.md`.

## Commit & PR

- Conventional, descriptive commits (`feat:`, `fix:`, `docs:`, `test:`, …).
- Describe what changed and how you verified it; attach diagnostics for bug fixes.

---

## 贡献指南（简体中文）

感谢你帮助改进 Zettlab AINAS 集成！

### 开发环境

```bash
git clone https://github.com/xianleewu/zettlab-ainas-iot
cd zettlab-ainas-iot
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements_test.txt
```

### 工作流

```bash
ruff format .            # 格式化
ruff check . --fix       # 静态检查
pytest                   # 跑测试
pytest --cov=custom_components/zettlab_ainas --cov-report=term-missing
```

以上都会在 CI 里运行(`test.yml`),外加 Home Assistant `hassfest` 与 HACS 校验
(`validate.yml`)。PR 必须全绿。

### 规范

- **Python 3.12+,全异步** —— 不要阻塞事件循环;不可避免的阻塞用 `aiohttp` 或
  `hass.async_add_executor_job`。
- **完整类型标注**;`from __future__ import annotations`。
- API 客户端(`api.py`)**只负责传输**,不得 import `homeassistant`。
- 改动端点时,请同步维护 `CLAUDE.md`(已验证的 ZettOS API 契约)。
- 任何行为变更都要加/改测试,覆盖率目标 **≥ 80%**。
- 切勿提交设备 IP、凭据、令牌或 `.env`。

### 提交与 PR

- 语义化、描述清晰的提交(`feat:`、`fix:`、`docs:`、`test:` …)。
- 说明改了什么、如何验证;修 bug 请附诊断信息。
