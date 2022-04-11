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
    echo "Sleep 120"
    sleep 120
  fi
  date
  echo "Sleep 60"
  sleep 60
done
