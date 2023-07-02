#!/bin/bash

cp plant-monitor.service /etc/systemd/system/
echo "Service file copied to /etc/systemd/system/plant-monitor.service"
systemctl disable plant-monitor.service
systemctl enable plant-monitor.service
systemctl start plant-monitor.service
