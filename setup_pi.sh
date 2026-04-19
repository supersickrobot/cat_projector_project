#!/bin/bash
# Setup script for the Cat Projector on Raspberry Pi 4
# Run this on the Pi after copying project files over.

set -e

echo "=========================================="
echo "  🐱 Cat Projector - Pi Setup"
echo "=========================================="

# Update system packages
echo ""
echo "--- Updating system packages ---"
sudo apt update

# Install VLC for video playback
echo ""
echo "--- Installing VLC ---"
sudo apt install -y vlc

# Install ffmpeg (in case we want to generate videos on the Pi too)
echo ""
echo "--- Installing ffmpeg ---"
sudo apt install -y ffmpeg

# Install Python dependencies
echo ""
echo "--- Installing Python packages ---"
pip3 install --user flask twilio

# Create project directories
echo ""
echo "--- Creating project directories ---"
mkdir -p ~/cat_project/videos

# Download and install ngrok for exposing the webhook
echo ""
echo "--- Installing ngrok ---"
if ! command -v ngrok &> /dev/null; then
    echo "Downloading ngrok..."
    curl -s https://ngrok-agent.s3.amazonaws.com/ngrok-v3-stable-linux-arm64.tgz -o /tmp/ngrok.tgz
    sudo tar -xzf /tmp/ngrok.tgz -C /usr/local/bin
    rm /tmp/ngrok.tgz
    echo "ngrok installed to /usr/local/bin/ngrok"
else
    echo "ngrok already installed."
fi

# Create systemd service for auto-start on boot (optional)
echo ""
echo "--- Creating systemd service (optional) ---"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

cat > /tmp/cat-projector.service << EOF
[Unit]
Description=Cat Projector WhatsApp Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$SCRIPT_DIR
ExecStart=/usr/bin/python3 $SCRIPT_DIR/whatsapp_bot.py
Restart=on-failure
RestartSec=10
Environment=DISPLAY=:0

[Install]
WantedBy=multi-user.target
EOF

sudo cp /tmp/cat-projector.service /etc/systemd/system/cat-projector.service
sudo systemctl daemon-reload

echo ""
echo "=========================================="
echo "  ✅ Setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Copy your video files to ~/cat_project/videos/"
echo "   Example: scp fish.mp4 pi@$(hostname -I | awk '{print $1}'):~/cat_project/videos/"
echo ""
echo "2. Set up Twilio WhatsApp sandbox:"
echo "   - Sign up at https://twilio.com"
echo "   - Activate WhatsApp sandbox"
echo "   - Set environment variables:"
echo "     export TWILIO_ACCOUNT_SID='your_sid'"
echo "     export TWILIO_AUTH_TOKEN='your_token'"
echo ""
echo "3. Start the bot:"
echo "   python3 whatsapp_bot.py"
echo ""
echo "4. In another terminal, start ngrok:"
echo "   ngrok http 5000"
echo "   Copy the HTTPS URL and set it as your Twilio webhook:"
echo "   https://xxxx.ngrok.io/whatsapp"
echo ""
echo "5. (Optional) Enable auto-start on boot:"
echo "   sudo systemctl enable cat-projector"
echo "   sudo systemctl start cat-projector"
echo ""
echo "6. Send 'help' to your Twilio WhatsApp number to test!"
echo ""
