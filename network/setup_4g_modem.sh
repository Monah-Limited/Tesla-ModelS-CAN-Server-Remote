#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────
# Tesla Local Control — 4G/5G Modem + 始终在线
# ──────────────────────────────────────────────────────────────────────
# 在 Orange Pi 上运行：
#   bash setup_4g_modem.sh
#
# 支持：华为 E3372 / E8372 / 中兴 MF833 / 通用 RNDIS
# ──────────────────────────────────────────────────────────────────────

set -euo pipefail

echo "╔═══════════════════════════════════════════╗"
echo "║  Tesla 4G/5G Modem Setup                 ║"
echo "╚═══════════════════════════════════════════╝"

# ── Install tools ───────────────────────────────────────────────────
sudo apt update
sudo apt install -y \
    usb-modeswitch usb-modeswitch-data \
    network-manager modemmanager \
    curl wget

sudo systemctl enable ModemManager
sudo systemctl start ModemManager

# ── Detect modem ────────────────────────────────────────────────────
echo ""
echo "🔍 检测 USB Modem..."
lsusb | grep -i -E "modem|huawei|zte|quectel|simcom|rndis|ecm" || true
echo ""
echo "网络接口:"
ip link show | grep -E "^[0-9]" | awk '{print $2}' | sed 's/://'

# ── Auto-switch to modem mode ───────────────────────────────────────
echo ""
echo "📡 配置 Modem 模式切换..."
# Most Huawei sticks need mode switch via usb-modeswitch
sudo mkdir -p /etc/usb_modeswitch.d

# Huawei E3372 (12d1:1c05)
cat << 'EOF' | sudo tee /etc/usb_modeswitch.d/12d1:1c05 > /dev/null
# Huawei E3372
DefaultVendor=0x12d1
DefaultProduct=0x1c05
MessageEndpoint=0x01
MessageContent="55534243123456780000000000000011062000000100000000000000000000"
EOF

# ── NM connection ───────────────────────────────────────────────────
echo ""
echo "📶 创建自动 4G 连接..."
# NetworkManager will auto-detect the modem, but we pre-create APN config
# Edit this for your HK carrier:
#   CMHK:  cmhk
#   CSL:   mobile
#   3HK:   mobile.three.com.hk
#   SmarTone: smartone

read -p "请输入 APN (香港: cmhk/mobile/mobile.three.com.hk/smartone): " APN
APN=${APN:-cmhk}

nmcli con add \
    type gsm \
    ifname "*" \
    con-name "tesla-4g" \
    apn "$APN" \
    connection.autoconnect yes \
    ipv4.method auto

echo ""
echo "✅ 4G 配置完成"
echo "   检查: nmcli con show tesla-4g"
echo "   连接: nmcli con up tesla-4g"
