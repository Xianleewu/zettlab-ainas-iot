# 故障排查

> [English](troubleshooting.md) · [简体中文](troubleshooting.zh-Hans.md)

## 常见问题

### “连接失败”(cannot_connect)

- 在同一网络下用浏览器打开 `https://<nas-ip>`,必须能加载。
- 确认 Home Assistant 与 NAS 在同一局域网 / 可路由网段。
- 确认填的是 IP,而不是 HA 解析不了的主机名。

### “用户名或密码错误”(invalid_auth)

- 使用 NAS 网页端的准确凭据(默认用户名 `admin`)。
- 如果设备上启用了双因素或邮箱登录,请使用本地用户名/密码账号。

### 要求重新认证

NAS 密码变了。点击 *设置 → 设备与服务* 里的通知,输入新密码即可。

### 实体显示“不可用”

- 设备可能在重启或离线 —— 下次轮询成功后实体会自动恢复。
- 检查网络连通性,以及 NAS 网页端是否可访问。

## 开启调试日志

加入 `configuration.yaml` 后重启:

```yaml
logger:
  default: warning
  logs:
    custom_components.zettlab_ainas: debug
```

## 下载诊断信息

在设备页面使用右上角三点菜单 → **下载诊断信息**。其中的敏感信息(密码、序列号、
MAC)会自动脱敏。提交问题时请附上该文件。

## 已知限制

- **远程访问** 集成内不支持 —— 请用 VPN / 反向代理 / Home Assistant Cloud 远程访问
  NAS。
- **屏幕亮度** 无法设置(设备只暴露开/关)。
- **风扇模式** 选项在标签破解前以原始整数展示。

## 还没解决?

提交 issue:https://github.com/xianleewu/zettlab-ainas-iot/issues —— 请附上 HA 版本、
设备型号与固件、调试日志和诊断信息。
