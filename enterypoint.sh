
#!/bin/bash

# Start the run once job.
echo "Docker container started"
date

declare -p | grep -Ev 'BASHOPTS|BASH_VERSINFO|EUID|PPID|SHELLOPTS|UID' > /container.env

# Setup a cron schedule
echo "SHELL=/bin/bash
BASH_ENV=/container.env
0 * * * * python3 /withings2influxdb.py > /dev/stdout
# This extra line makes it a valid cron" > scheduler.txt

crontab scheduler.txt
cron -f
