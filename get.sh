#!/bin/bash

while :
do
  date
  echo "--- Start Call API"
  python3 withings2influxdb.py
  RET=$?
  if [ ${RET} -ne 0 ];
  then
    echo "Exit status not 0"
    echo "Sleep 3600"
    sleep 3600
  fi
  date
  echo "Sleep 6 hrs"
  sleep 21600
done
