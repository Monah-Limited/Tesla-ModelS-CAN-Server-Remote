# Orange Pi 4 Pro → MCP2515 CAN 模块 → Tesla OBD-II 接线图

## 所需零件

| 零件 | 说明 | 香港購買 |
|------|------|---------|
| MCP2515 CAN 模块 | SPI 转 CAN，通常含 SN65HVD230 收发器 | 淘宝 ~¥15 |
| 母对母杜邦线 | 5-7 条，连接 Pi GPIO 到 CAN 模块 | 華輝/淘宝 ~¥5 |
| OBD-II 公头 | 16 pin，接车上的 OBD 口 | 淘宝 ~¥20 |
| 接线端子或焊锡 | 把 CAN 模块输出接到 OBD 头 | 華輝 ~¥10 |

## Orange Pi 4 Pro GPIO → MCP2515

Orange Pi 4 Pro 的 40-pin GPIO 定义（物理引脚编号）：

```
Orange Pi 4 Pro (正面朝上, USB口朝下)
┌──────────────────────────────────────┐
│  (1) 3.3V  (2) 5V                    │
│  (3) I2C   (4) 5V                    │
│  (5) I2C   (6) GND                   │
│  (7)       (8) TX                    │
│  (9) GND   (10) RX                   │
│  (11)      (12)                      │
│  (13)      (14) GND                  │
│  (15)      (16)                      │
│  (17) 3.3V  (18)                     │
│  (19) MOSI  (20) GND     ← SPI      │
│  (21) MISO  (22) INT     ← SPI      │
│  (23) SCLK  (24) CE0     ← SPI      │
│  (25) GND   (26)                     │
│  ...                                 │
└──────────────────────────────────────┘
```

### 接线表

| Pi 物理引脚 | Pi 功能 | MCP2515 CAN 模块 |
|------------|---------|-----------------|
| 19         | MOSI    | MOSI           |
| 21         | MISO    | MISO           |
| 23         | SCLK    | SCK            |
| 24         | CE0     | CS             |
| 22         | GPIO 中断 | INT           |
| 1 或 17    | 3.3V    | VCC            |
| 6 或 9     | GND     | GND            |

### 接线口诀

> **白橙绿棕**：Pi 19→MOSI(MOSI)，21→MISO(MISO)，23→SCK(SCLK)，24→CE0(CS)  
> **红黑蓝**：3.3V→VCC，GND→GND，GPIO22→INT

## MCP2515 → OBD-II (Tesla Model S)

MCP2515 模块上通常有 CAN_H 和 CAN_L 输出端子（绿色端子或排针）：

```
MCP2515 模块            Tesla OBD-II 接口
─────────────           ─────────────────
CAN_H (H)  ──────────── pin 1 (黄/白) — BCAN_H
CAN_L (L)  ──────────── pin 9 (白/蓝) — BCAN_L
GND        ──────────── pin 4 (黑)    — 底盘地
```

OBD-II 接口（面向前方看）：
```
    ┌───────────────────────┐
    │ 4  3  2  1            │
    │ 9  8  7  6  5         │
    └───────────────────────┘

    pin 1 = BCAN_H (125kbps) ← 门锁/车门
    pin 9 = BCAN_L (125kbps) ←
    pin 4 = 底盘地
    pin 5 = 信号地
```

## 实物组装步骤

1. **MCP2515 模块插面包板**
2. **杜邦线连接 Pi GPIO**：19-21-23-24-22 + 3.3V + GND
3. **CAN_H/CAN_L 接到 OBD 公头**：pin 1 和 pin 9
4. **GND 接到 OBD pin 4**
5. **OBD 公头插到特斯拉 OBD 接口**
   - 位置：方向盘左下方，刹车踏板上方
6. **Orange Pi 通电** → 系统启动 → CAN 接口自动拉起

## 验证接线

```bash
# 检查 SPI (应该看到 spidev0.0 或 spidev1.0)
ls /dev/spidev*

# 检查 CAN (应该看到 can0)
ip link show can0

# 如果 can0 没起来
sudo ip link set can0 type can bitrate 125000
sudo ip link set can0 up

# 用 candump 看 CAN 数据（车要通电）
candump can0 -c -x
```

## ⚠️ 常见问题

- **SPI 没开** → 检查 `/boot/armbianEnv.txt`，确保有 `overlays=spi-spidev`
- **CAN 没起来** → 先 `sudo ip link set can0 down` 再重新 up
- **门锁没反应** → 你的车 CAN ID 可能不同，跑 CAN Sniffer 找正确值
