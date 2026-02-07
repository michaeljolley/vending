#!/bin/bash
# Kiosk mode setup script for Raspberry Pi
# Run this once to configure the Pi for kiosk mode

echo "Setting up kiosk mode for Valentine's Candy Machine..."

# Install required packages
sudo apt-get update
sudo apt-get install -y chromium-browser unclutter

# Create autostart directory if it doesn't exist
mkdir -p ~/.config/autostart

# Create autostart entry for Chromium in kiosk mode
cat > ~/.config/autostart/candy-kiosk.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=Candy Machine Kiosk
Exec=/bin/bash -c 'sleep 10 && chromium-browser --kiosk --noerrdialogs --disable-infobars --no-first-run --enable-features=OverlayScrollbar --start-fullscreen http://localhost:8000'
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
EOF

# Create autostart entry to hide cursor
cat > ~/.config/autostart/unclutter.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=Unclutter
Exec=unclutter -idle 0.5 -root
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
EOF

# Disable screen blanking
if ! grep -q "xserver-command=X -s 0 -dpms" /etc/lightdm/lightdm.conf 2>/dev/null; then
    sudo sed -i 's/\[Seat:\*\]/[Seat:*]\nxserver-command=X -s 0 -dpms/' /etc/lightdm/lightdm.conf 2>/dev/null || true
fi

echo ""
echo "Kiosk mode configured!"
echo "The browser will auto-start in fullscreen mode on boot."
echo "Press Alt+F4 to exit kiosk mode if needed."
echo ""
echo "Reboot to test the kiosk setup."
