#!/usr/bin/python3
# encoding=utf-8

from pytz import timezone
import datetime
from influxdb_client import InfluxDBClient, Point, WriteOptions
from influxdb_client.client.write_api import SYNCHRONOUS
import json
import os
import sys
import requests


# debug enviroment variables
showraw = False
debug_str=os.getenv("DEBUG", None)
if debug_str is not None:
    debug = debug_str.lower() == "true"
else:
    debug = False


# netatmo environment variables
withings_clientId=os.getenv('WITHINGS_CLIENT_ID', "")
withings_clientSecret=os.getenv('WITHINGS_CLIENT_SECRET', "")
withings_username=os.getenv('WITHINGS_USERNAME')
withings_password=os.getenv('WITHINGS_PASSWORD')


# influxDBv2 environment variables
influxdb2_host=os.getenv('INFLUXDB2_HOST', "localhost")
influxdb2_port=int(os.getenv('INFLUXDB2_PORT', "8086"))
influxdb2_org=os.getenv('INFLUXDB2_ORG', "org")
influxdb2_token=os.getenv('INFLUXDB2_TOKEN', "token")
influxdb2_bucket=os.getenv('INFLUXDB2_BUCKET', "netatmo")


# hard encoded environment variables


# report debug status
if debug:
    print ( " debug: TRUE" )
else:
    print ( " debug: FALSE" )


# netatmo
authorization = lnetatmo.ClientAuth(clientId=netatmo_clientId, clientSecret=netatmo_clientSecret, username=netatmo_username, password=netatmo_password)
devList = lnetatmo.WeatherStationData(authorization)


# influxDBv2
influxdb2_url="http://" + influxdb2_host + ":" + str(influxdb2_port)
if debug:
    print ( "influx: "+influxdb2_url )
    print ( "bucket: "+influxdb2_bucket )

client = InfluxDBClient(url=influxdb2_url, token=influxdb2_token, org=influxdb2_org)


# these keys are float
keylist=['Temperature', 'min_temp', 'max_temp', 'Pressure', 'AbsolutePressure', 'Rain', 'sum_rain_24', 'sum_rain_1']

# these keys are skipped
skiplistmod=['_id','station_name','date_setup','last_setup','type','last_status_store','module_name','firmware','last_message', 'last_seen', 'battery_vp','last_upgrade','co2_calibrating', 'data_type', 'place', 'home_id', 'home_name','dashboard_data', 'modules','reachable']
skiplistdsh=['temp_trend', 'pressure_trend', 'date_min_temp', 'date_max_temp', 'max_temp', 'min_temp', 'AbsolutePressure', 'time_utc','sum_rain_1','sum_rain_24']

# these keys are outside
outsidelist=['Rain','Wind']


# pass data to InfluxDB
def send_data(ds):    
    senddata={}
    dd=ds['dashboard_data']
    time = dd['time_utc']
    timeOut = datetime.datetime.fromtimestamp(time).strftime("%Y-%m-%dT%H:%M:%SZ") 

    # pass module data
    for key in ds:
        if key in skiplistmod:
            if debug and showraw:
                print ( "Skipped: "+key )
            continue

        if key == 'battery_percent':
            measurement="battery"
            time=ds['last_seen']
        
        if key == "rf_status":
            measurement="signal"
            time=ds['last_seen']

        if key == "wifi_status":
            measurement="signal"
            time=ds['last_status_store']
            
        timeOut = datetime.datetime.fromtimestamp(time).strftime("%Y-%m-%dT%H:%M:%SZ") 

        senddata["measurement"]=measurement
        senddata["time"]=timeOut
        senddata["tags"]={}
        senddata["tags"]["source"]="docker netatmo-influxdbv2"
        senddata["tags"]["origin"]="Netatmo"
        senddata["tags"]["sensor"]=ds['module_name']
        senddata["tags"]["hardware"]=ds['_id']
        senddata["fields"]={}
        senddata["fields"]["percent"]=float(ds[key])
        if debug:
            print ("INFLUX: "+influxdb2_bucket)
            print (json.dumps(senddata,indent=4))
        write_api.write(bucket=influxdb2_bucket, org=influxdb2_org, record=[senddata])

    # pass dashboard_data
    for key in dd:
        if key in skiplistdsh:
            if debug and showraw:
                print ( "Skipped: "+key )
            continue

        if key in keylist:
            value=float(dd[key])
        else:
            value=dd[key]    
   
        senddata["measurement"]=key.lower()
        senddata["time"]=timeOut
        senddata["tags"]={}
        senddata["tags"]["source"]="docker netatmo-influxdbv2"
        senddata["tags"]["origin"]="Netatmo"
        senddata["tags"]["sensor"]=ds['module_name']
        senddata["tags"]["hardware"]=ds['_id']
        senddata["fields"]={}

        if key == "Temperature":
            senddata["fields"]["temp"]=value

        if key == "Humidity":
            senddata["fields"]["percent"]=value

        if key == "CO2":
            senddata["fields"]["ppm"]=value

        if key == "Pressure":
            senddata["fields"]["mbar"]=value

        if key == "Noise":
            senddata["fields"]["dB"]=value

        if key == "Rain":
            senddata["fields"]["mm"]=value
  
        if debug:
            print ("INFLUX: "+influxdb2_bucket)
            print (json.dumps(senddata,indent=4))
        write_api.write(bucket=influxdb2_bucket, org=influxdb2_org, record=[senddata])


# pass stations
for station_id in devList.stations:
    ds=devList.stationById(station_id)
    if ds is None:
        continue
    if not 'dashboard_data' in ds:
        continue
    if debug:
        if 'station_name' in ds:
            print ("\nStation: "+ds['station_name']+" - "+station_id)
        else:
            print ("\nStation: "+station_id)
        if showraw:
            print ("RAW:")
            print (json.dumps(ds,indent=4))

    write_api = client.write_api(write_options=SYNCHRONOUS)
    send_data(ds)


# pass modules
for name in devList.modulesNamesList():
    ds=devList.moduleByName(name)
    if ds is None:
        continue
    if not 'dashboard_data' in ds:
        continue
    if debug:
        print ( "\nModule: "+ds['module_name']+" - "+ds['_id'])

    send_data(ds)
