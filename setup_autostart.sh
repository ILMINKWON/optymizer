#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
AUTOSTART_DIR="$HOME/.config/autostart"
DESKTOP_FILE="$AUTOSTART_DIR/system-optimizer.desktop"

mkdir -p "$AUTOSTART_DIR"

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=System Optimizer
Exec=python3 $SCRIPT_DIR/optimizer.py
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
EOF

echo "자동 실행 등록 완료: $DESKTOP_FILE"
