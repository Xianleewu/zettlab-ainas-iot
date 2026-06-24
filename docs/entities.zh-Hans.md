# 实体参考

> [English](entities.md) · [简体中文](entities.zh-Hans.md)

所有实体归属于同一个 Home Assistant 设备(以 NAS 序列号标识)。实体 ID 以设备名为
前缀,例如 `sensor.<设备名>_cpu_usage`。

## 传感器 (sensor)

| 实体 | 单位 | 设备类别 | 默认 | 来源 |
|------|------|----------|:----:|------|
| CPU 使用率 | % | — | 开 | `monitor/v1/view` → `cpu.usage_rate` |
| CPU 温度 | °C | temperature | 开 | `monitor/v1/view` → `cpu.thermal` |
| 内存使用率 | % | — | 开 | `monitor/v1/view` → `mem.used / mem.total` |
| 已用内存 | GiB | data size | 开 | `monitor/v1/view` → `mem.used` |
| NPU 使用率 | % | — | **关** | `monitor/v1/view` → `npu[]`(取平均) |
| GPU 使用率 | % | — | **关** | `monitor/v1/view` → `gpu[]` |
| 上次启动 | 时间戳 | timestamp | 开(诊断) | `device` → `last_start_time` |
| 存储池 _N_ 使用率 | % | — | 开 | `storage-pool` → `used_size / total_size` |
| 存储池 _N_ 已用 | GiB | data size | 开 | `storage-pool` → `used_size` |
| 存储池 _N_ 容量 | GiB | data size | 开 | `storage-pool` → `total_size` |
| 磁盘 _序列号_ 温度 | °C | temperature | 开 | `storage-pool` → `disks[].temperature` |

磁盘温度传感器附带额外属性:`model`、`slot`、`type`、`path`。

NPU 与 GPU 传感器**默认关闭**(常年为 0);需要的话在实体页面手动启用。

## 二元传感器 (binary_sensor)

| 实体 | 设备类别 | 触发条件 | 来源 |
|------|----------|----------|------|
| 存储池 _N_ 异常 | problem | 池 `status` ≠ 0 | `storage-pool` |

## 控制实体

| 实体 | 平台 | 行为 | 来源 |
|------|------|------|------|
| 风扇模式 | `select` | 选择风扇模式(标签破解前以原始整数展示) | `POST fan/{mode}` |
| 状态灯 | `light` | RGB 颜色;"关"会把灯设为黑色。设备的灯效模式与速度会被保留并作为属性展示 | `POST light` |
| 屏幕 | `switch` | 开关设备 LCD 屏幕 | `POST lcd {enable}` |

## 说明

- 动态实体(存储池、磁盘)在初始化时根据设备状态创建。之后新增磁盘或存储池,需
  **重新加载**集成才能识别。
- 没有亮度控制:设备只暴露屏幕开/关。
