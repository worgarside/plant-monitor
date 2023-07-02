#!/bin/bash

cp limit-updater.service /etc/systemd/system/
echo "Service file copied to /etc/systemd/system/limit-updater.service"
systemctl disable limit-updater.service
systemctl enable limit-updater.service
systemctl start limit-updater.service
