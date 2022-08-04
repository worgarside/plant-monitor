#!/bin/bash

repo_path=$(git rev-parse --show-toplevel)
bash_path=$(which bash)

mkdir -p "$HOME/logs/dep_updater" || :

#write out current crontab
crontab -l > tempcron
#echo new cron into cron file
echo "0 4 * * * ${bash_path} ${repo_path}/utilities/dep_updater/dep_updater.sh >> \"$HOME/logs/dep_updater/\$(date +20\%y-\%m-\%d).log\" 2>&1" >> tempcron
# install new cron file
crontab tempcron
rm tempcron
