#!/bin/bash

cp waterer.service /etc/systemd/system/
echo "Service file copied to /etc/systemd/system/waterer.service"
systemctl reenable waterer.service
systemctl start waterer.service