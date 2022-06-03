#!/bin/bash

cp limit-updater.service /etc/systemd/system/
echo "Service file copied to /etc/systemd/system/limit-updater.service"
systemctl reenable limit-updater.service
systemctl start limit-updater.service