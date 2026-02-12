#!/bin/bash
# Kiosk mode setup script for Raspberry Pi
# Run this once to configure the Pi for kiosk mode

echo "Setting up kiosk mode for Valentine's Candy Machine..."

# Install required packages (chromium on newer Pi OS, chromium-browser on older)
sudo apt-get update
sudo apt-get install -y chromium unclutter fonts-noto-color-emoji || sudo apt-get install -y chromium-browser unclutter fonts-noto-color-emoji

# Create autostart directory if it doesn't exist
mkdir -p ~/.config/autostart

# Detect which chromium binary is available
CHROMIUM_BIN=$(which chromium || which chromium-browser)

# Create autostart entry for Chromium in kiosk mode
cat > ~/.config/autostart/candy-kiosk.desktop << EOF
[Desktop Entry]
Type=Application
Name=Candy Machine Kiosk
Exec=/bin/bash -c 'sleep 10 && $CHROMIUM_BIN --kiosk --noerrdialogs --disable-infobars --no-first-run --enable-features=OverlayScrollbar --start-fullscreen --password-store=basic --disable-features=LockProfileCookieDatabase http://localhost:8000'
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

# Configure display rotation for vertical mode (optional - uncomment if needed)
# echo "display_rotate=1" | sudo tee -a /boot/config.txt

echo ""
echo "Kiosk mode configured!"
echo "The browser will auto-start in fullscreen mode on boot."
echo "Press Alt+F4 to exit kiosk mode if needed."
echo ""
echo "To rotate display to vertical, add 'display_rotate=1' to /boot/config.txt"
echo ""
echo "Reboot to test the kiosk setup."
