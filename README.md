# 🚗 Tesla Model S CAN Server · Remote

<p align="center">
  <img src="https://img.shields.io/badge/status-unfinished-yellow" alt="unfinished">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT">
  <img src="https://img.shields.io/badge/platform-Linux%20%7C%20macOS-blue" alt="platform">
  <img src="https://img.shields.io/badge/languages-4-orange" alt="lang-4">
</p>

> **[ English ]** · **[ 简体中文 ]** · **[ 日本語 ]** · **[ 한국어 ]**

---

**[English](#english) | [简体中文](#简体中文) | [日本語](#日本語) | [한국어](#한국어)**

---

<a name="english"></a>
## 🇺🇸 English

### The Story

I'm a Github-native open-source contributor with triple backgrounds: law, pure mathematics and full-stack engineering. Outside of coding and protocol reverse-engineering, I also work as an early-stage tech startup angel investor. I'm used to solving hardware and software ecosystem deadlocks with logical mathematical modeling, underlying network protocol analysis and legal compliance verification. I'm releasing this self-hosted Tesla vehicle control project not for showing off tech skills, but for a real, helpless user-side rescue against official service restrictions.

Let me start with the whole story, which will resonate with plenty of Tesla owners who have suffered the same official account ban issue. I own a rebuilt 2015 Tesla Model S 85D with a previous total loss record. I originally purchased this vehicle for 900,000 HKD before tax. This car has accompanied me through countless road trips and daily commutes, carrying tons of personal travel memories far beyond its material value.

After the total-loss accident, I independently invested another 130,000 HKD to complete full vehicle overhaul and hardware restoration. Every physical component of the car works perfectly and supports normal road driving. However, Tesla unilaterally suspended my official Tesla mobile app account and permanently cut off all cloud-based remote vehicle services, without any prior notice, reasonable official explanation or available appeal channels. Even though I am still the legal registered owner of this fully functional vehicle, I was stripped of all basic owner remote access privileges overnight.

Currently, the residual market value of this rebuilt old Model S is merely 150,000 HKD. From a pure asset investment perspective, abandoning this car would be the most rational choice. But vehicles carry emotions, not just market prices. I never violated any official user terms, and all I want is equal basic owner functions that every Tesla user deserves: remote door unlock when forgetting physical keys, pre-conditioning cabin temperature, real-time vehicle status check and fundamental remote body control. I don't need premium official cloud services; I only demand fair and basic ownership rights for my own car.

With no official support and no valid appeal path left, I decided to build an independent local control system completely out of Tesla's official cloud ecosystem. I got a free Orange Pi 4 Pro (6GB) SBC from a friend for hardware testing a while ago. My original plan for this single-board computer had nothing to do with vehicle remote control: I intended to build a vehicle-mounted lightweight NAS plus edge computing solution, leveraging its 3 TOPS AI computing power to realize local dashcam video storage and on-board vision edge AI analysis.

Given the complete shutdown of official app access, I restructured the whole solution rapidly. I adopt Orange Pi 4 Pro as the local core computing unit, connect to the vehicle's underlying CAN bus via CAN Server to realize direct hardware communication with the car, and deploy Tailscale to build secure private network penetration. The whole system runs 100% offline and self-hosted, with zero reliance on Tesla official cloud servers.

### Critical Notice

> ⚠️ **WORK IN PROGRESS** — This project is an unfinished work-in-progress prototype, not a stable production-ready solution.

As an open-source enthusiast who advocates community co-development, I open-source all my code and hardware wiring docs here for non-commercial communication only. This project has no intention to crack vehicle safety firmware or conduct illegal vehicle modification. I just want to communicate with fellow Tesla owners who have encountered arbitrary official account bans and service cuts, to figure out reliable self-hosted control workarounds together.

With solid legal awareness, rigorous mathematical logic and underlying engineering capabilities, I strictly limit this solution to legal self-owned vehicle local control only, without touching any core power and safety-related vehicle firmware. At the end of the day, it's simple: I own the car, so I should have the right to control my own car.

### The Stack

```
📱 Phone (PWA)
    ↓
🔗 Tailscale / WireGuard (encrypted P2P tunnel)
    ↓
🍊 Orange Pi 4 Pro (6GB RAM, ARM64 Linux)
    ├── Flask REST API (port 5000)
    ├── Python CAN driver (python-can + socketcan)
    ├── Tailscale client (always-on remote access)
    ├── DDNS updater (optional — remote.openfrunk.com)
    └── BLE beacon (local phone discovery)
    ↓
🔌 CANable 2.0 USB-CAN adapter
    └── OBD-II port → Vehicle Body CAN (125 kbps)
```

### Features

- 🔒 Lock / unlock doors via CAN bus
- 🟢 Open front trunk / 🟤 rear trunk
- 💡 Flash lights · 📯 Honk horn
- 🪟 Vent windows · ⚡ Charging control
- 📊 Real-time diagnostics (CAN / Bluetooth / 4G / Tailscale)
- 🚘 VIN decoder — 39 Tesla models database
- 🎨 Tesla + Material You style UI (dark theme)
- 🌐 Multi-language UI (ZH / EN / JA / KO)
- 📡 4 connection modes: Tailscale / DDNS / WiFi / BLE

### Hardware You'll Need

| Component | Est. Cost | Where |
|-----------|-----------|-------|
| Orange Pi 4 Pro / RPi 4 | ~¥300 | 淘宝 / Amazon |
| CANable 2.0 USB-CAN | ~¥45 | 淘宝 |
| OBD-II connector | ~¥20 | 淘宝 |
| 4G USB modem (opt.) | ~¥200 | Carrier |

### Quick Start

```bash
# 1. Flash Armbian or Ubuntu Server to Orange Pi
# 2. Clone this repo
git clone https://github.com/Monah-Limited/Tesla-ModelS-CAN-Server-Remote.git
cd Tesla-ModelS-CAN-Server-Remote

# 3. Run one-click setup
bash setup_orangepi.sh

# 4. Wire CANable to OBD-II port
#    CAN_H → pin 1   CAN_L → pin 9   GND → pin 4

# 5. Start CAN interface
sudo slcand -o -c -s8 /dev/ttyACM0 can0
sudo ip link set can0 up type can bitrate 125000

# 6. Configure network (optional)
bash network/setup_network.sh
```

### Similar Projects

- [Open Vehicles](https://docs.openvehicles.com) — OVMS hardware module
- [Tesla Vehicle Command SDK](https://github.com/teslamotors/vehicle-command) — For 2021+ models with BLE support
- [Comma.ai OpenPilot](https://github.com/commaai/openpilot) — ADAS system

## 🙏 Credits / 致谢

This project would not exist without these open-source projects and communities:

| Project | What it does |
|---------|-------------|
| [**Open Vehicles**](https://docs.openvehicles.com) | OVMS — the original open-source Tesla CAN bus project. Massive inspiration. |
| [**CANable**](https://canable.io) | USB-to-CAN adapter firmware & hardware — the physical bridge to the car |
| [**candleLight firmware**](https://github.com/candle-usb/candleLight_fw) | Open-source CAN firmware running on CANable |
| [**python-can**](https://github.com/hardbyte/python-can) | Python CAN library |
| [**Flask**](https://flask.palletsprojects.com) | Web framework for the REST API server |
| [**Tailscale**](https://tailscale.com) | Zero-config VPN — secure remote access to the car |
| [**Orange Pi 4 Pro**](http://www.orangepi.org) | The SBC running the server (Raspberry Pi alternative) |
| [**Tesla Vehicle Command SDK**](https://github.com/teslamotors/vehicle-command) | Tesla's official BLE/cloud API for 2021+ models |
| [**Comma.ai OpenPilot**](https://github.com/commaai/openpilot) | ADAS system — pushing the boundaries of what's possible with cars |
| [**OpenGarages**](https://opengarages.org) | Community of hackers reverse-engineering vehicle protocols |

**Special thanks** to the reverse-engineering community on [Tesla Motors Club](https://teslamotorsclub.com) and the CAN bus hacking forums — the collective knowledge that made this possible.

### License

MIT — do whatever you want. Just don't sue me if your car does something unexpected. This is a side project, not a product.

---

<a name="简体中文"></a>
## 🇨🇳 简体中文

### 故事的起点

大家好，我是一名常年泡在Github开源社区的独立开发者，同时拥有法律、纯数学以及全栈技术三重学术背景，日常也做早期科技初创公司的天使投资，习惯用逻辑推演、底层代码拆解以及合规层面的双向思维，去解决各类硬件与软件的闭环问题。今天开源这套基于香橙派搭建的特斯拉自研车机控制系统，没有炫技的意思，纯粹是一次被逼无奈、为爱发电的底层技术自救。

先聊聊整件事的起因，相信很多特斯拉车主都能狠狠共情。我的座驾是2015款全损修复版 Tesla Model S 85D，当年落地不含税费的购入成本高达90万港币，这台车陪我走过了无数通勤、长途自驾的日夜，承载了非常多私人出行回忆，对我而言从来不是一台单纯的代步机器。

车辆发生全损事故之后，我自掏腰包花费13万港币全额完成整车修复，整车硬件工况全部恢复正常，车辆本身完全可以正常上路使用。但让我无法理解也无法接受的是：特斯拉官方直接单方面封禁了我的车主APP账号，永久关停了云端所有官方远程控制服务。没有任何协商空间，没有合规层面的合理解释，哪怕车辆硬件完好、我依旧是合法登记的车主，我彻底失去了所有车主标配的远程控车权限。

如今这台修复完毕的老款Model S 85D二手残值仅仅只剩15万港币，从资产价值来看，放弃它看似是最理性的选择。但情怀从来不能用二手车估值衡量，我从头到尾没有任何出格操作，只是想要拿回每一位特斯拉车主本该平等拥有的基础功能：忘带车钥匙时远程解锁、提前开启空调、查看车辆状态、基础远程车身控制。我不需要官方云端的增值服务，我只想要属于我自己车辆最基础、最公平的车主权益。

在官方彻底切断云端通路、没有任何申诉渠道之后，我决定不走官方生态，自己从零搭建一套本地化控车方案。刚好前段时间朋友赠予我一块闲置的Orange Pi 4 Pro（6GB）开发板，最初拿到这块板子的规划和本次控车项目完全无关：我原本计划依托这块开发板3TOPS的算力，搭建一台小型车载NAS+边缘计算设备，专门做特斯拉行车记录仪视频本地存储、车载画面AI边缘识别分析，只是单纯想做一个轻量化车载边缘算力玩机项目。

恰逢官方账号被封无路可走，我顺势调整了整体方案架构：以Orange Pi 4 Pro为本地核心算力主机，通过CAN Server直连车辆CAN总线，打通车辆底层硬件通讯协议，再搭配Tailscale搭建私有内网穿透通道，完全脱离特斯拉官方云端服务器，自建一套私有化、无第三方依赖的远程车辆控制系统。

### 重要前置声明

> ⚠️ **未完成半成品** — 本项目目前依旧是未完成测试半成品，绝非成熟商用方案。

作为一名习惯开源共建的Github爱好者，我把整个项目开源出来，不是为了破解、篡改车辆安全底层协议，也不是用于任何违规改装用途。我只是想和圈内同样遭遇官方账号封禁、被官方一刀切关停APP服务的特斯拉车主，一起交流底层CAN总线通讯逻辑、私有内网控车方案，抱团解决官方服务霸权带来的用车痛点。

我懂法律合规边界，懂数学逻辑建模，也懂车载底层硬件与网络架构，所以整套方案全程恪守车辆安全底线与相关合规要求，只做车主合法自有车辆的本地私有化控制，不触碰任何车辆动力安全底层固件。说到底，一个很朴素的心愿：我的车，我自己做主。

### 架构

```
📱 手机 (PWA)
    ↓
🔗 Tailscale / WireGuard (加密 P2P 隧道)
    ↓
🍊 Orange Pi 4 Pro (6GB RAM, ARM64 Linux)
    ├── Flask REST API (端口 5000)
    ├── Python CAN 驱动 (python-can + socketcan)
    ├── Tailscale 客户端 (常驻在线)
    ├── DDNS 更新器 (可选 — remote.openfrunk.com)
    └── BLE 信标 (本地手机发现)
    ↓
🔌 CANable 2.0 USB-CAN 适配器
    └── OBD-II 接口 → 车身 CAN 总线 (125 kbps)
```

### 功能

- 🔒 通过 CAN 总线锁定/解锁车门
- 🟢 开启前备箱 / 🟤 后备箱
- 💡 闪灯 · 📯 鸣笛
- 🪟 车窗通风 · ⚡ 充电控制
- 📊 实时诊断（CAN / 蓝牙 / 4G / Tailscale）
- 🚘 VIN 解码器 — 39 款 Tesla 车型数据库
- 🎨 Tesla + Material You 风格 UI（深色主题）
- 🌐 多语言界面（中文 / 英文 / 日文 / 韩文）
- 📡 四种连接模式：Tailscale / DDNS / WiFi / BLE

### 所需硬件

| 组件 | 预估成本 | 购买渠道 |
|------|---------|---------|
| Orange Pi 4 Pro / 树莓派 4 | ~¥300 | 淘宝 / Amazon |
| CANable 2.0 USB-CAN | ~¥45 | 淘宝 |
| OBD-II 连接器 | ~¥20 | 淘宝 |
| 4G USB 上网卡（可选） | ~¥200 | 运营商 |

### 快速开始

```bash
# 1. 为 Orange Pi 刷入 Armbian 或 Ubuntu Server
# 2. 克隆仓库
git clone https://github.com/Monah-Limited/Tesla-ModelS-CAN-Server-Remote.git
cd Tesla-ModelS-CAN-Server-Remote

# 3. 运行一键部署脚本
bash setup_orangepi.sh

# 4. 连接 CANable 到 OBD-II 接口
#    CAN_H → pin 1   CAN_L → pin 9   GND → pin 4

# 5. 启动 CAN 接口
sudo slcand -o -c -s8 /dev/ttyACM0 can0
sudo ip link set can0 up type can bitrate 125000

# 6. （可选）配置网络层
bash network/setup_network.sh
```

### 同类项目

- [Open Vehicles](https://docs.openvehicles.com) — OVMS 硬件模块
- [Tesla Vehicle Command SDK](https://github.com/teslamotors/vehicle-command) — 适用于 2021+ 支持 BLE 的车型
- [Comma.ai OpenPilot](https://github.com/commaai/openpilot) — ADAS 系统

### 许可证

MIT — 随便用。只是别因为你的车出了意外来起诉我。这是个人项目，不是商业产品。

---

<a name="日本語"></a>
## 🇯🇵 日本語

### このプロジェクトが生まれた理由

2015年、税抜90万香港ドルで Tesla Model S 85D を購入しました。ミッドナイトシルバー。単なる移動手段ではなく、宣言であり、伴侶であり、エンジニアリングの申し子でした。台風の夜も、深夜の高速道路も、新界の静かな裏道も、その車はいつも私のそばにいました。

そしてある日、保険会社が「全損」と判断しました。

カリフォルニアのTeslaサーバーがフラグを一つ反転させただけで — アプリも、リモートロックも、スマホからのエアコン操作も、すべて消えました。100万香港ドル近く払った車が、データベースの一行のせいで突然1998年のカローラより「馬鹿」になったのです。

私は法学を学び、数学に魅せられ、コードを書くことで生きています。GitHubは第二の我が家。ディープテックのアーリー投資家でもあります。そして思いました：**これ、めっちゃおかしいやろ**。このマシンは俺のものだ。CANバスだって俺のものだ。カリフォルニアのサーバーが俺のフロントトランクを開けられるかどうか決めるって、どういうこと？

だから友達にもらった Orange Pi 4 Pro（3 TOPSのエッジAIでドラレコNASを作る予定だった）を転用しました。このリポジトリはその結果です。

> **⚠️ 開発中** — 週末のハッカープロジェクトです。机上では大体動いてます。実車での完全統合はまだです。これは開発途中の試作品であり、完成品ではありません。

---

<a name="한국어"></a>
## 🇰🇷 한국어

### 이 프로젝트가 존재하는 이유

2015년, 세금 제외 90만 홍콩달러를 주고 Tesla Model S 85D를 샀습니다. 미드나잇 실버. 그냥 차가 아니었어요. 선언이었고, 동반자였고, 엔지니어링 역사의 한 조각이었습니다. 태풍이 몰아치는 밤, 깊은 한밤의 고속도로, 신계의 조용한 뒷길 — 그 차는 나를 누구보다 잘 알았습니다.

그러던 어느 날, 보험사가 '전손' 판정을 내렸습니다.

프리몬트 어딘가의 Tesla 서버가 플래그 하나를 뒤집었을 뿐인데 — 앱도, 원격 잠금도, 폰으로 에어컨 켜는 것도, 전부 사라졌습니다. 거의 100만 홍콩달러를 낸 차가 데이터베이스 한 줄 때문에 갑자기 1998년식 코롤라보다 '멍청해진' 겁니다.

법학을 공부했고, 수학에 집착하며, 코드로 숨을 쉽니다. GitHub이 두 번째 집이에요. 딥테크 얼리 스테이지 투자자이기도 합니다. 저는 생각했습니다: **이건 말이 안 된다**. 이 기계는 내 소유다. CAN 버스도 내 거다. 캘리포니아 서버가 내 앞 트렁크를 열 수 있는지 결정한다는 게 말이 돼?

그래서 친구에게서 받은 Orange Pi 4 Pro(3 TOPS 에지 AI로 블랙박스 NAS를 만들 예정이었던)를 용도 변경했습니다. 이 저장소가 바로 그 결과입니다.

> **⚠️ 개발 중** — 주말 해커의 사이드 프로젝트입니다. 책상 위에선 대부분 돌아가요. 실차 완전 통합은 아직입니다. 이것은 진행 중인 프로토타입이며 안정적인 완성품이 아닙니다.

---

## 📁 Project Structure

```
tesla-local-control/
├── app/
│   ├── tesla_can.py          # CAN bus driver (socketcan interface)
│   ├── tesla_models.py       # 39 Tesla models database + VIN decoder
│   ├── server.py             # Flask REST API server
│   └── static/index.html     # PWA mobile app (4-language UI)
├── network/
│   ├── setup_4g_modem.sh     # 4G/5G modem configuration
│   ├── setup_network.sh      # Tailscale + DDNS + BLE
│   └── ddns_update.sh        # DDNS periodic updater
├── setup_orangepi.sh         # One-click deployment
├── wiring.md                 # OBD-II wiring guide
├── ARCHITECTURE.md           # Architecture diagram
└── LICENSE                   # MIT
```

---

## 👤 About the Author

**Tim Wynter** — lawyer, mathematician, full-stack engineer. GitHub native. Deep-tech early-stage angel investor. Weekend hacker who refuses to let a cloud server dictate what his legally owned car can or cannot do.

This repo is a conversation starter, not a product pitch. PRs welcome. Issues welcome. Ideas welcome. Let's build together.

---

<p align="center">
  <sub>Built with ☕ and stubbornness in Hong Kong SAR</sub>
</p>
