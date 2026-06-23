#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────
# Tesla Local Control — Orange Pi 4 Pro 一键部署
# 适用：2015 Model S 85D (CAN 总线方案)
# ──────────────────────────────────────────────────────────────────────
# 在 Orange Pi 上运行:
#   bash setup_orangepi.sh
#
# 作用：装依赖 → 启 SPI/CAN → 部署 Web 控制面板
# ──────────────────────────────────────────────────────────────────────

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
log()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }

echo "╔═══════════════════════════════════════════╗"
echo "║  Tesla Local Control — Orange Pi 4 Pro   ║"
echo "║  2015 Model S 85D · CAN 总线方案         ║"
echo "╚═══════════════════════════════════════════╝"

# ── 1. 系统依赖 ────────────────────────────────────────────────────
echo ""
echo "[1/5] 安装系统依赖"
sudo apt update
sudo apt install -y \
    python3-pip python3-venv python3-dev \
    git curl \
    can-utils \
    nginx
log "系统依赖安装完成"

# ── 2. 启用 SPI ────────────────────────────────────────────────────
echo ""
echo "[2/5] 启用 SPI 接口 (连接 MCP2515 CAN 模块)"
sudo apt install -y armbian-config 2>/dev/null || true

# RK3399 上 SPI 默认可能没开，手动设备树覆盖
# Orange Pi 4 Pro 的 SPI 引脚在 GPIO  header 上
if ! ls /dev/spidev* 2>/dev/null; then
    warn "未检测到 SPI 设备，尝试启用..."
    # 对于 Armbian，在 /boot/armbianEnv.txt 添加
    if [ -f /boot/armbianEnv.txt ]; then
        if ! grep -q "spi" /boot/armbianEnv.txt 2>/dev/null; then
            echo "overlays=spi-spidev" | sudo tee -a /boot/armbianEnv.txt
            log "已添加 SPI 设备树覆盖，需要重启生效"
        fi
    else
        warn "请手动检查你的系统如何启用 SPI"
        warn "Orange Pi 4 Pro: GPIO 引脚 19(MOSI)/21(MISO)/23(SCLK)/24(CS)"
    fi
else
    log "SPI 已就绪: $(ls /dev/spidev*)"
fi

# ── 3. 安装 Python 环境 ──────────────────────────────────────────
echo ""
echo "[3/5] 部署 Python 环境"
cd /opt
sudo mkdir -p tesla-control
sudo chown "$USER:$USER" tesla-control
python3 -m venv /opt/tesla-control/venv
source /opt/tesla-control/venv/bin/activate
pip install --upgrade pip
pip install flask flask-cors python-can
log "Python 环境就绪"

# ── 4. 部署控制代码 ──────────────────────────────────────────────
echo ""
echo "[4/5] 部署控制代码"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -d "$SCRIPT_DIR/app" ]; then
    cp -r "$SCRIPT_DIR/app/"* /opt/tesla-control/
    log "代码已部署到 /opt/tesla-control"
fi

# ── 5. CAN 接口自动拉起 ──────────────────────────────────────────
echo ""
echo "[5/5] 配置 CAN 接口自动拉起"
sudo tee /etc/systemd/system/can0-bringup.service > /dev/null <<'EOF'
[Unit]
Description=Bring up CAN0 interface for Tesla
After=network.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/sbin/ip link set can0 type can bitrate 125000
ExecStart=/sbin/ip link set can0 up
ExecStop=/sbin/ip link set can0 down

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable can0-bringup
log "CAN 自启服务已配置"

echo ""
echo "╔═══════════════════════════════════════════╗"
echo "║  ✅ 部署完成！                            ║"
echo "║                                           ║"
echo "║  接线：                                   ║"
echo "║  MCP2515 CAN_H → OBD pin 1 (BCAN_H)      ║"
echo "║  MCP2515 CAN_L → OBD pin 9 (BCAN_L)      ║"
echo "║  GND          → OBD pin 4                ║"
echo "║                                           ║"
echo "║  启动：                                   ║"
echo "║  sudo systemctl start tesla-control       ║"
echo "║  http://<opi-ip>:5000                     ║"
echo "║                                           ║"
echo "║  首次需要用 CAN Sniffer 找 CAN ID:        ║"
echo "║  cd /opt/tesla-control && python3 tools/  ║"
echo "╚═══════════════════════════════════════════╝"
