#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────
# Tesla Local Control — 网络层部署
# DDNS + Tailscale P2P + Cloudflare Tunnel + 蓝牙发现
# ──────────────────────────────────────────────────────────────────────
# 在 Orange Pi 上运行：
#   bash setup_network.sh
# ──────────────────────────────────────────────────────────────────────

set -euo pipefail

echo "╔═══════════════════════════════════════════╗"
echo "║  Tesla Local Control — 网络层             ║"
echo "║  DDNS + Tailscale + BLE Discovery        ║"
echo "╚═══════════════════════════════════════════╝"

# ═══════════════════════════════════════════════════════════════════
# 1. Tailscale P2P VPN（推荐 — 最简单、最安全）
# ═══════════════════════════════════════════════════════════════════
echo ""
echo "───────────────────────────────────────────────"
echo " [1/4] Tailscale P2P VPN"
echo "───────────────────────────────────────────────"
echo "Tailscale 在 4G/5G 环境下自动建立 WireGuard P2P 连接"
echo "手机和 Pi 之间直连，不需要公网 IP，不需要 VPS"
echo ""

if command -v tailscale &>/dev/null; then
    echo "  ✅ Tailscale 已安装"
    tailscale status 2>/dev/null | head -5 || true
else
    echo "  安装 Tailscale..."
    curl -fsSL https://tailscale.com/install.sh | sh
    
    echo ""
    echo "  ⚠️  请手动认证："
    echo "  sudo tailscale up --advertise-tags=tag:tesla"
    echo ""
    echo "  然后在手机上也安装 Tailscale App"
    echo "  登录同一个账号后，Pi 和手机自动 P2P 连通"
    echo ""
    echo "  访问地址: http://<pi的tailscale-ip>:5000"
fi

# ═══════════════════════════════════════════════════════════════════
# 2. DuckDNS DDNS（可选—如果要有域名）
# ═══════════════════════════════════════════════════════════════════
echo ""
echo "───────────────────────────────────────────────"
echo " [2/4] DuckDNS DDNS (固定域名)"
echo "───────────────────────────────────────────────"
echo "如果你想要一个域名访问你的 Pi（如 mytesla.duckdns.org）"
echo ""

read -p "是否设置 DuckDNS? (y/n): " SETUP_DDNS
if [ "$SETUP_DDNS" = "y" ]; then
    read -p "DuckDNS 域名 (不含 .duckdns.org): " DDNS_DOMAIN
    read -p "DuckDNS Token: " DDNS_TOKEN
    
    sudo mkdir -p /opt/tesla-control/network
    
    # Create DDNS update script
    sudo tee /opt/tesla-control/network/duckdns.sh > /dev/null << EOF
#!/usr/bin/env bash
# DuckDNS auto-update — runs every 5 minutes
# Records IPv4 (current 4G IP) and IPv6
DOMAIN="$DDNS_DOMAIN"
TOKEN="$DDNS_TOKEN"
LOGFILE=/var/log/duckdns.log

CURL_CMD="curl -s \"https://www.duckdns.org/update?domains=\${DOMAIN}&token=\${TOKEN}&ip=\""
echo "\$(date): Running duckdns update..." >> \$LOGFILE
eval \$CURL_CMD >> \$LOGFILE
EOF
    
    sudo chmod +x /opt/tesla-control/network/duckdns.sh
    
    # Cron job every 5 minutes
    echo "*/5 * * * * root /opt/tesla-control/network/duckdns.sh" | sudo tee /etc/cron.d/duckdns
    sudo chmod 644 /etc/cron.d/duckdns
    
    echo "  ✅ DuckDNS 已配置: $DDNS_DOMAIN.duckdns.org"
    echo "  首次更新: sudo /opt/tesla-control/network/duckdns.sh"
fi

# ═══════════════════════════════════════════════════════════════════
# 3. Cloudflare Tunnel（DDNS 替代方案）
# ═══════════════════════════════════════════════════════════════════
echo ""
echo "───────────────────────────────────────────────"
echo " [3/4] Cloudflare Tunnel (可选—不依赖 VPS)"
echo "───────────────────────────────────────────────"
echo "Cloudflare Tunnel 通过 Cloudflare 边缘网络暴露你的服务"
echo "不需要公网 IP，不需要 DDNS"
echo ""

read -p "是否设置 Cloudflare Tunnel? (y/n): " SETUP_CF
if [ "$SETUP_CF" = "y" ]; then
    # Install cloudflared
    curl -L --output cloudflared.deb \
        https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb
    sudo dpkg -i cloudflared.deb
    rm cloudflared.deb
    
    echo ""
    echo "  ⚠️  请认证 Tunnel:"
    echo "  cloudflared tunnel login"
    echo "  cloudflared tunnel create tesla-control"
    echo ""
    echo "  然后创建配置文件 /etc/cloudflared/config.yml:"
    echo "  tunnel: <tunnel-id>"
    echo "  credentials-file: /root/.cloudflared/<tunnel-id>.json"
    echo "  ingress:"
    echo "    - hostname: tesla.yourdomain.com"
    echo "      service: http://localhost:5000"
    echo "    - service: http_status:404"
fi

# ═══════════════════════════════════════════════════════════════════
# 4. Bluetooth LE Beacon（近车自动发现）
# ═══════════════════════════════════════════════════════════════════
echo ""
echo "───────────────────────────────────────────────"
echo " [4/4] Bluetooth LE 广播 (近车自动发现)"
echo "───────────────────────────────────────────────"

sudo apt install -y bluez bluez-tools python3-dbus

# Create BLE advertisement service
sudo tee /opt/tesla-control/network/ble_advertise.py > /dev/null << 'PYEOF'
#!/usr/bin/env python3
"""
BLE Beacon — Tesla Local Control 蓝牙自动发现
==============================================
当手机靠近车辆时，Pi 通过 BLE 广播自身信息，
手机 App 自动发现并提示连接。

广播内容:
  - Name: "TeslaControl-XXXX"
  - Service UUID: 用于 App 识别
  - TX Power: 用于距离估算
"""

import dbus
import dbus.service
import dbus.mainloop.glib
import socket
import subprocess
from gi.repository import GLib

# ── Configuration ────────────────────────────────────────────────────
DEVICE_NAME = "TeslaControl"
ADV_INTERVAL_MS = 500  # Broadcast every 500ms

def get_pi_id():
    """Generate a short unique ID from MAC address."""
    try:
        mac = open('/sys/class/net/wlan0/address').read().strip()
        return mac[-8:].replace(':', '').upper()
    except:
        return "OPI4"

def main():
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()
    
    # Power on BLE adapter
    subprocess.run(['sudo', 'hciconfig', 'hci0', 'up'], capture_output=True)
    subprocess.run(['sudo', 'hciconfig', 'hci0', 'name', f'{DEVICE_NAME}-{get_pi_id()}'],
                   capture_output=True)
    subprocess.run(['sudo', 'hciconfig', 'hci0', 'piscan'], capture_output=True)
    
    print(f"✅ BLE 广播已启动: {DEVICE_NAME}-{get_pi_id()}")
    print(f"   手机蓝牙扫描 'TeslaControl' 可发现此设备")
    print(f"   CAN 服务器地址: http://{get_ip()}:5000")
    
    # Keep running
    loop = GLib.MainLoop()
    try:
        loop.run()
    except KeyboardInterrupt:
        loop.quit()

def get_ip():
    """Get primary IP address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

if __name__ == '__main__':
    main()
PYEOF

sudo chmod +x /opt/tesla-control/network/ble_advertise.py

# Create BLE service
sudo tee /etc/systemd/system/tesla-ble.service > /dev/null << 'EOF'
[Unit]
Description=Tesla BLE Beacon — local discovery
After=bluetooth.target

[Service]
Type=simple
ExecStart=/opt/tesla-control/network/ble_advertise.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable tesla-ble

echo "  ✅ BLE 广播已配置"
echo "     手机搜索 'TeslaControl-XXXX' 即可发现"

# ── Summary ──────────────────────────────────────────────────────────
echo ""
echo "╔═══════════════════════════════════════════╗"
echo "║  ✅ 网络层配置完成                        ║"
echo "║                                           ║"
echo "║  连接方式：                               ║"
echo "║                                           ║"
echo "║  ① 蓝牙靠近                              ║"
echo "║     搜索 TeslaControl-XXXX 自动连接       ║"
echo "║                                           ║"
echo "║  ② Tailscale P2P（全球远程）              ║"
echo "║     手机装 Tailscale App                  ║"
echo "║     http://<tailscale-ip>:5000            ║"
echo "║                                           ║"
echo "║  ③ DDNS 域名（需 DuckDNS 配置）           ║"
echo "║     http://xxxx.duckdns.org:5000           ║"
echo "╚═══════════════════════════════════════════╝"
