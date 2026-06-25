<p align="center">
  <img src="assets/logo.png" alt="Zettlab" width="120">
</p>

<h1 align="center">Zettlab AINAS 的 Home Assistant 集成</h1>

<p align="center">
  <a href="README.md">English</a> · <b>简体中文</b>
</p>

<p align="center">
  在 Home Assistant 中监控并控制你的 <a href="https://zettlab.com">Zettlab</a> AI-NAS(ZettOS)—— 存储池、磁盘健康、CPU/NPU/GPU、风扇、RGB 状态灯和屏幕,全部走本地网络。
</p>

<p align="center">
  <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5.svg" alt="HACS Custom"></a>
  <a href="https://github.com/xianleewu/zettlab-ainas-iot/actions/workflows/validate.yml"><img src="https://github.com/xianleewu/zettlab-ainas-iot/actions/workflows/validate.yml/badge.svg" alt="Validate"></a>
  <a href="https://github.com/xianleewu/zettlab-ainas-iot/actions/workflows/test.yml"><img src="https://github.com/xianleewu/zettlab-ainas-iot/actions/workflows/test.yml/badge.svg" alt="Tests"></a>
  <a href="https://github.com/xianleewu/zettlab-ainas-iot/releases"><img src="https://img.shields.io/github/v/release/xianleewu/zettlab-ainas-iot?display_name=tag" alt="Release"></a>
  <img src="https://img.shields.io/badge/Home%20Assistant-2024.12%2B-41BDF5?logo=home-assistant&logoColor=white" alt="HA 2024.12+">
  <a href="LICENSE"><img src="https://img.shields.io/github/license/xianleewu/zettlab-ainas-iot" alt="License: MIT"></a>
</p>

---

## ✨ 功能

- 📊 **系统监控** —— CPU 使用率与温度、NPU/GPU 使用率、内存使用率与已用字节。
- 💾 **存储** —— 每个存储池的容量 / 已用 / 使用率、RAID 异常状态、每块磁盘温度。
- 🌬️ **风扇控制** —— 读取并切换风扇模式。
- 💡 **RGB 状态灯** —— 作为 Home Assistant 灯实体完整控制颜色。
- 🖥️ **屏幕** —— 开关设备 LCD 屏幕。
- 🔐 **本地、私密** —— 仅通过局域网与 NAS 通信(RSA 加密登录,不走云端)。
- 🧩 **一设备多实体** —— 所有实体归到一个 HA 设备下,含诊断信息。
- 🌍 **中英双语** —— 内置 English 与简体中文界面翻译。

> 想看完整列表?见 **[实体参考](docs/entities.zh-Hans.md)**。

## 📦 支持的设备

**支持所有 Zettlab AINAS(ZettOS)型号**,要求 **ZettOS 固件 1.9.0 或更新**。本集成
**与型号无关** —— 从设备读取型号、序列号和固件,使用通用的 ZettOS API,因此所有型号
无需改代码即可工作。

已验证:

| 型号 | 固件 |
|------|------|
| Zettlab **D4** | ZettOS 1.9.0-beta |
| Zettlab **D6 Ultra** | ZettOS 1.9.1-beta |

## ✅ 前提条件

- Home Assistant **2024.12** 或更新版本。
- 一台运行 **ZettOS 固件 1.9.0 或更新** 的 Zettlab AINAS。
- NAS 在你的局域网内可达(同一网段 / 可路由 IP)。
- 你的 NAS 网页登录凭据(即访问 `https://<nas-ip>` 用的账号,默认用户名 `admin`)。

## 🚀 安装

### HACS(推荐)

1. 在 HACS 中打开右上角三点菜单 → **自定义存储库 (Custom repositories)**。
2. 添加 `https://github.com/xianleewu/zettlab-ainas-iot`,类别选 **Integration**。
3. 搜索 **Zettlab AINAS**,安装后**重启 Home Assistant**。

[![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=xianleewu&repository=zettlab-ainas-iot&category=integration)

### 手动安装

1. 把 `custom_components/zettlab_ainas` 复制到 Home Assistant 的 `config/custom_components/` 目录。
2. 重启 Home Assistant。

## ⚙️ 配置

从界面添加集成,无需 YAML:

[![Add Integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=zettlab_ainas)

或进入 **设置 → 设备与服务 → 添加集成 → Zettlab AINAS**。会引导你用三种方式添加设备:

1. **在局域网中发现** —— 自动查找设备。
2. **输入 IP 地址** —— 发现不到时,手动填 NAS 的 IP。

然后用 NAS 的网页用户名和密码登录。凭据加密存放在配置项里,绝不离开你的 Home Assistant。

**选项**(集成卡片上的 ⚙️):可修改**轮询间隔**(默认 30 秒,最小 10 秒)。

详见 **[配置指南](docs/configuration.zh-Hans.md)**。

## 🧩 实体

会创建一个设备,包含(部分):

| 平台 | 实体 | 来源 |
|------|------|------|
| `sensor` | CPU 使用率 / 温度、NPU·GPU 使用率、内存使用率 / 已用 | 实时监控 |
| `sensor` | 存储池 容量 / 已用 / 使用率、磁盘温度(每块盘) | 存储池 |
| `sensor` | 上次启动(诊断) | 设备信息 |
| `binary_sensor` | 存储池异常 | 存储池 |
| `select` | 风扇模式 | 风扇 |
| `light` | 状态灯(RGB) | LED |
| `switch` | 屏幕开关 | LCD |

含单位和说明的完整表格:**[docs/entities.zh-Hans.md](docs/entities.zh-Hans.md)**。

## ⚠️ 已知限制与路线图

- **远程访问** —— 本集成**仅限本地**。Zettlab 远程访问依赖云账号 + P2P 隧道,没有可复用的本地 API,因此请用 HA 常规方式远程访问 NAS(VPN / 反向代理 / Home Assistant Cloud)。
- **屏幕亮度** —— 设备只提供开/关,API 没有亮度设置接口;因此只提供开关 `switch`。
- **风扇模式标签** —— 模式是整数(人类可读标签尚未破解),目前以原始模式值展示。
- **重启 / 关机按钮** —— 端点尚未梳理。

发布历史见 [CHANGELOG.md](CHANGELOG.md)。

## 🩺 故障排查

- **连不上 / cannot_connect** —— 确认浏览器能打开 `https://<nas-ip>`,且设备与 HA 在同一网络。
- **认证失败 / invalid_auth** —— 用与 NAS 网页端相同的用户名/密码。
- **要求重新认证** —— 密码改过了,重新登录即可。

更多见 **[docs/troubleshooting.zh-Hans.md](docs/troubleshooting.zh-Hans.md)**。提交问题时,请从设备页面下载诊断信息并附上。

## 🤝 参与贡献

欢迎贡献!开发环境、测试与编码规范见 **[CONTRIBUTING.md](CONTRIBUTING.md)**。

## 📄 许可证

采用 [MIT 许可证](LICENSE)。

> 非 Zettlab 官方产品。"Zettlab" 与 "ZettOS" 为各自所有者的商标。使用风险自负。
