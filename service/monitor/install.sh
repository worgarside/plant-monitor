#!/bin/bash

cp plant-monitor.service /etc/systemd/system/
echo "Service file copied to /etc/systemd/system/plant-monitor.service"
systemctl reenable plant-monitor.service
systemctl start plant-monitor.service
