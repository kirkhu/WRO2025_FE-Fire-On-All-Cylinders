#!/bin/bash

mkdir -p ~/.auto_start

cd ~/.auto_start

echo "Download Auto Run Code Script."

curl -fsSL -u "if0_39931049:microhack188" -o "open-mode.sh" "ftp://ftpupload.net/htdocs/UserData/WRO2025-Orin/open-mode.sh"

curl -fsSL -u "if0_39931049:microhack188" -o "open-mode.service" "ftp://ftpupload.net/htdocs/UserData/WRO2025-Orin/open-mode.service"

echo "Copy file to the target directory."

sudo cp open-mode.service /etc/systemd/system/
cp open-mode.sh /home/user/code/

echo "Set auto run code."

sudo chmod +x /home/user/code/open-mode.sh

sudo systemctl daemon-reload
sudo systemctl enable open-mode
sudo systemctl start open-mode

sudo rm -rf ~/.auto_start/
