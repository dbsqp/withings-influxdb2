
#!/bin/bash

# Start the run once job.
echo "container started"
date

declare -p | grep -Ev 'BASHOPTS|BASH_VERSINFO|EUID|PPID|SHELLOPTS|UID' > /container.env

# Setup a cron schedule
echo "SHELL=/bin/bash
BASH_ENV=/container.env
00 * * * * python3 /withings2influxdb.py > /proc/1/fd/1 2>&1
# This extra line makes it a valid cron" > scheduler.txt

echo "crontab:"
grep withings scheduler.txt
echo
crontab scheduler.txt
cron -f
