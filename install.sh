#!/bin/bash

# Check if the script is being run as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root"
   exit 1
fi

# Install Python and pip
apt update
apt install -y python3 python3-pip

# Create a virtual environment and install the bot dependencies
cd src
cp -R . /opt/sound-cropper-bot
cd /opt/sound-cropper-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

ini_file="config.ini"
key="BOT_TOKEN"

# Check that ini file has token
if grep -q "^$key=" "$ini_file"; then
  echo "Key $key found in INI file."

  # Get the value associated with the key
  value=$(grep "^$key=" "$ini_file" | cut -d'=' -f2)

  # Check if the value is empty
  if [ -z "$value" ]; then
    echo "Value for key $key is empty."
    exit 1
  fi
else
  echo "Key $key not found in INI file."
  exit 1
fi

# Create a systemd service configuration file
cat <<EOF > /etc/systemd/system/sound-cropper-bot.service
[Unit]
Description=Audio Cropper Bot
After=network.target

[Service]
User=$SUDO_USER
WorkingDirectory=/opt/sound-cropper-bot
ExecStart=/bin/bash -c 'source venv/bin/activate && exec /usr/bin/python3 soundbar-bot.py'
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and start the bot service
systemctl daemon-reload
systemctl enable sound-cropper-bot.service
systemctl start sound-cropper-bot.service
