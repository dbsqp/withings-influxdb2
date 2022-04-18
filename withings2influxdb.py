#!/usr/bin/python3
# encoding=utf-8

from pytz import timezone
from datetime import datetime, timedelta
from influxdb_client import InfluxDBClient, Point, WriteOptions
from influxdb_client.client.write_api import SYNCHRONOUS
import json
import os
import array

from os import path
from typing import cast
import pickle
from typing_extensions import Final
from oauthlib.oauth2.rfc6749.errors import MissingTokenError

#from withings_api import WithingsAuth, WithingsApi, AuthScope
#from withings_api.common import CredentialsType, get_measure_value, MeasureType, GetSleepField, GetSleepSummaryField, MeasureGetMeasGroupCategory

from python_withings_api.withings_api import WithingsAuth, WithingsApi, AuthScope
from python_withings_api.withings_api.common import CredentialsType, get_measure_value, MeasureType, GetSleepField, GetSleepSummaryField, MeasureGetMeasGroupCategory



# debug enviroment variables
debug_str=os.getenv("DEBUG", None)
if debug_str is not None:
    debug = debug_str.lower() == "true"
else:
    debug = False
    
showRaw = False

# netatmo environment variables
withings_clientId=os.getenv('WITHINGS_CLIENT_ID', "")
withings_clientSecret=os.getenv('WITHINGS_CLIENT_SECRET', "")
withings_callback=os.getenv('WITHINGS_CALLBACK', "")
withings_auth_code=os.getenv('WITHINGS_AUTH_CODE', "")

# influxDBv2 environment variables
influxdb2_host=os.getenv('INFLUXDB2_HOST', "localhost")
influxdb2_port=int(os.getenv('INFLUXDB2_PORT', "8086"))
influxdb2_org=os.getenv('INFLUXDB2_ORG', "org")
influxdb2_token=os.getenv('INFLUXDB2_TOKEN', "token")
influxdb2_bucket=os.getenv('INFLUXDB2_BUCKET', "withings")


# hard encoded environment variables
if os.path.exists('private-api.py'):
    print("included: private-api.py")
    exec(compile(source=open('private-api.py').read(), filename='private-api.py', mode='exec'))
    withings_auth_code="INIT"
    debug = True


# report debug status
if debug:
    print ( "   debug: TRUE" )
else:
    print ( "   debug: FALSE" )



# setup withings API
tokenPath = path.abspath(path.join(path.dirname(path.abspath(__file__)), "./oauth"))

os.makedirs(tokenPath, exist_ok=True)
tokenFile = tokenPath+"/token"

def save_credentials(credentials: CredentialsType) -> None:
    print("saving token to:", tokenFile)
    with open(tokenFile, "wb") as file_handle:
        pickle.dump(credentials, file_handle)

def load_credentials() -> CredentialsType:
    print("reading token from:", tokenFile)
    with open(tokenFile, "rb") as file_handle:
        return cast(CredentialsType, pickle.load(file_handle))

auth = WithingsAuth(
    client_id=withings_clientId,
    consumer_secret=withings_clientSecret,
    callback_uri=withings_callback,
    scope=(
        AuthScope.USER_ACTIVITY,
        AuthScope.USER_METRICS,
    )
)

if withings_auth_code == "INIT":
    authorise_url = auth.get_authorize_url()
    print("Goto this URL to authorise:\n\n",authorise_url)
    quit()
else:
    if withings_auth_code != "":
        print("Getting oauth token with auth code:", withings_auth_code)        
        save_credentials(auth.get_credentials(withings_auth_code))
        withings_auth_code=""

read_api = WithingsApi(load_credentials(), refresh_cb=save_credentials)

print("Refreshing token...")
old_token = read_api.get_credentials().access_token

read_api.refresh_token()

if old_token != read_api.get_credentials().access_token:
    print("NO Refresh: old and new token are the same!")
else:
    print("Refresh: old and new are different")




# setup influxDBv2
influxdb2_url="http://" + influxdb2_host + ":" + str(influxdb2_port)
if debug:
    print ( "influxdb: "+influxdb2_url+" bucket: "+influxdb2_bucket )

client = InfluxDBClient(url=influxdb2_url, token=influxdb2_token, org=influxdb2_org)
write_api = client.write_api(write_options=SYNCHRONOUS)

def write_influxdb():
    if showRaw:
        print ("INFLUX: "+influxdb2_bucket)
        print (json.dumps(senddata,indent=4))
    write_api.write(bucket=influxdb2_bucket, org=influxdb2_org, record=[senddata])



# setup time ranges
now=datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
ago=(datetime.utcnow()+timedelta(days=-2)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
start=(datetime.utcnow()+timedelta(days=-15*365)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')



# get height
print("Getting height...")
heights = read_api.measure_get_meas(
    category=MeasureGetMeasGroupCategory.REAL,
    startdate=start,
    enddate=now,
    lastupdate=None,
)

height=0
for measurement in heights.measuregrps:
    for measure in measurement.measures:
        if measure.type == MeasureType.HEIGHT:
            height = round(measure.value * 10 ** measure.unit, 2)

if debug:
    print("RAW:\n  HEIGHT ",height)



# get weight/bp/temp
print("Getting weight/bp/temp...")
measurements = read_api.measure_get_meas(
    category=MeasureGetMeasGroupCategory.REAL,
    startdate=ago,
    enddate=now,
    lastupdate=None,
)

# pass weight/bp/temp
for measurement in measurements.measuregrps:
    weight=0
    fat=0
    sys=0
    body=0

    time = measurement.date.strftime("%Y-%m-%dT%H:%M:%SZ")

    if debug:
        print("RAW:\n  time ",time)
    for measure in measurement.measures:
        value = round(measure.value * 10 ** measure.unit, 2)

        if measure.type == MeasureType.WEIGHT:                weight = value
        if measure.type == MeasureType.FAT_RATIO:                fat = value
        if measure.type == MeasureType.FAT_MASS_WEIGHT:    weightFat = value
        if measure.type == MeasureType.FAT_FREE_MASS:     weightLean = value
        if measure.type == MeasureType.HEART_RATE:                hr = value
        if measure.type == MeasureType.DIASTOLIC_BLOOD_PRESSURE: dia = value
        if measure.type == MeasureType.SYSTOLIC_BLOOD_PRESSURE:  sys = value
        if measure.type == MeasureType.BODY_TEMPERATURE:        body = value
        if measure.type == MeasureType.SKIN_TEMPERATURE:        skin = value
        if debug:
            print(" ",measure.type.name, value)

    senddata={}
    senddata["measurement"]="weight"
    senddata["time"]=time
    senddata["tags"]={}
    senddata["tags"]["source"]="docker withings-influxdbv2"
    senddata["tags"]["origin"]="Withings"
    senddata["fields"]={}

    if weight !=0:
        senddata["tags"]["type"]="total"
        senddata["fields"]["kg"]=round(float(weight),1)

        if height > 0:
            senddata["fields"]["bmi"]=round(weight/(height*height),1)
            write_influxdb()
            del senddata["fields"]["bmi"]

            senddata["tags"]["type"]="overweight"
            senddata["fields"]["kg"]=round(weight-(25*height*height),1)
            write_influxdb()
        else:
            write_influxdb()

        del senddata["fields"]["kg"]
        del senddata["tags"]["type"]

    if fat !=0:
        senddata["tags"]["type"]="fat"
        senddata["fields"]["kg"]=float(weightFat)
        senddata["fields"]["percent"]=round(float(fat),1)
        write_influxdb()

        senddata["tags"]["type"]="lean"
        senddata["fields"]["kg"]=round(float(weightLean),1)
        senddata["fields"]["percent"]=round(float(100-fat),1)
        write_influxdb()
        del senddata["fields"]["kg"]
        del senddata["fields"]["percent"]
        del senddata["tags"]["type"]

    if sys !=0:
        senddata["measurement"]="heart"
        senddata["tags"]["type"]="systolic"
        senddata["fields"]["bp"]=float(sys)
        write_influxdb()

        senddata["tags"]["type"]="diastolic"
        senddata["fields"]["bp"]=float(dia)
        write_influxdb()
        del senddata["fields"]["bp"]

        senddata["tags"]["type"]="resting"
        senddata["fields"]["bpm"]=float(hr)
        write_influxdb()
        del senddata["fields"]["bpm"]
        del senddata["tags"]["type"]

    if body !=0:
        senddata["measurement"]="temperature"
        senddata["tags"]["sensor"]="Body"
        senddata["fields"]["temp"]=float(body)
        write_influxdb()

        senddata["tags"]["sensor"]="Skin"
        senddata["fields"]["temp"]=float(skin)
        write_influxdb()



# get sleep summary
# note GetSleepSummaryField is NOT complate
print("Getting sleep summary...")
sleepSummary = read_api.sleep_get_summary(
    data_fields=GetSleepSummaryField,
    startdateymd=ago,
    enddateymd=now,
    lastupdate=None,
)

# pass sleep summary
for serie in sleepSummary.series:
    hrAvg=0

    time = serie.date.strftime("%Y-%m-%dT%H:%M:%SZ")

    if debug:
         print("RAW:\n  time ",time)

    for data in serie.data:
        if debug:
            print(" ",data[0]," = ",data[1])

        if data[0] == "hr_average": hrAvg = data[1]
        if data[0] == "hr_max":     hrMax = data[1]
        if data[0] == "hr_min":     hrMin = data[1]
        if data[0] == "rr_average": rrAvg = data[1]
        if data[0] == "rr_max":     rrMax = data[1]
        if data[0] == "rr_min":     rrMin = data[1]

        if data[0] == "deepsleepduration":     dDeep = data[1]
        if data[0] == "lightsleepduration":    dLite = data[1]
        if data[0] == "remsleepduration":       dREM = data[1]
        if data[0] == "wakeupduration":       dAwake = data[1]

        if data[0] == "snoring":            dSnoring = data[1]
        if data[0] == "waso":                dWokeup = data[1]
        if data[0] == "total_sleep_time":     dSleep = data[1]
        if data[0] == "total_timeinbed":      dInBed = data[1]

        if data[0] == "sleep_latency":        lSleep = data[1]
        if data[0] == "wakeup_latency":      lWakeup = data[1]

        if data[0] == "wakeupcount":         nWakeup = data[1]
        if data[0] == "snoringepisodecount":  nSnore = data[1]
        if data[0] == "nb_rem_episodes":        nREM = data[1]
        if data[0] == "out_of_bed_count":    nOutBed = data[1]

        if data[0] == "sleep_score":           score = data[1]
        if data[0] == "sleep_efficiency": efficiency = data[1]

        if data[0] == "breathing_disturbances_intensity": disturbed = data[1]
        if data[0] == "apnea_hypopnea_index":    ahi = data[1]

        ## Depreciated
        #if data[0] == "durationtowakeup":    dToWake = data[1]
        #if data[0] == "durationtosleep":    dToSleep = data[1]

    senddata={}
    senddata["time"]=time
    senddata["tags"]={}
    senddata["tags"]["source"]="docker withings-influxdbv2"
    senddata["tags"]["origin"]="Withings"
    senddata["fields"]={}

    if rrAvg !=0:
        senddata["measurement"]="respiration"
        senddata["tags"]["type"]="sleeping"

        senddata["fields"]["ahi"]=float(ahi)
        write_influxdb()
        del senddata["fields"]["ahi"]

        senddata["fields"]["disturbed"]=float(disturbed)
        write_influxdb()
        del senddata["fields"]["disturbed"]

        senddata["tags"]["mode"]="avg"
        senddata["fields"]["bpm"]=float(rrAvg)
        write_influxdb()

        senddata["tags"]["mode"]="max"
        senddata["fields"]["bpm"]=float(rrMax)
        write_influxdb()

        senddata["tags"]["mode"]="min"
        senddata["fields"]["bpm"]=float(rrMin)
        write_influxdb()


        del senddata["fields"]["bpm"]
        del senddata["tags"]["mode"]

    if hrAvg !=0:
        senddata["measurement"]="heart"
        senddata["tags"]["type"]="sleeping"
        senddata["tags"]["mode"]="avg"
        senddata["fields"]["bpm"]=float(hrAvg)
        write_influxdb()

        senddata["tags"]["mode"]="max"
        senddata["fields"]["bpm"]=float(hrMax)
        write_influxdb()

        senddata["tags"]["mode"]="min"
        senddata["fields"]["bpm"]=float(hrMin)
        write_influxdb()

        del senddata["fields"]["bpm"]
        del senddata["tags"]["mode"]

    if dDeep !=0:
        senddata["measurement"]="sleep"
        senddata["tags"]["type"]="deep"
        senddata["tags"]["mode"]="total"
        senddata["fields"]["duration"]=round(dDeep/3600,2)
        write_influxdb()

        senddata["tags"]["type"]="light"
        senddata["fields"]["duration"]=round(dLite/3600,2)
        write_influxdb()

        senddata["tags"]["type"]="rem"
        senddata["fields"]["duration"]=round(dREM/3600,1)
        write_influxdb()

        #senddata["tags"]["type"]="wakeup"
        #senddata["fields"]["duration"]=round(dToWake/3600,2)
        #write_influxdb()

        #senddata["tags"]["type"]="tosleep"
        #senddata["fields"]["duration"]=round(dToSleep/3600,2)
        #write_influxdb()

        senddata["tags"]["type"]="snoring"
        senddata["fields"]["duration"]=round(dSnoring/3600,2)
        write_influxdb()

        senddata["tags"]["type"]="woke"
        senddata["fields"]["duration"]=round(dWokeup/3600,2)
        write_influxdb()

        senddata["tags"]["type"]="sleep"
        senddata["fields"]["duration"]=round(dSleep/3600,2)
        write_influxdb()

        senddata["tags"]["type"]="inbed"
        senddata["fields"]["duration"]=round(dInBed/3600,2)
        write_influxdb()

        senddata["tags"]["type"]="awake"
        senddata["fields"]["duration"]=round(dAwake/3600,2)
        write_influxdb()
        del senddata["fields"]["duration"]
        del senddata["tags"]["mode"]


        senddata["tags"]["type"]="sleep"
        senddata["fields"]["latency"]=round(lSleep/3600,2)
        write_influxdb()

        senddata["tags"]["type"]="wakeup"
        senddata["fields"]["latency"]=round(lWakeup/3600,2)
        write_influxdb()
        del senddata["fields"]["latency"]


        senddata["tags"]["type"]="snoring"
        senddata["fields"]["count"]=int(nSnore)
        write_influxdb()

        senddata["tags"]["type"]="rem"
        senddata["fields"]["count"]=int(nREM)
        write_influxdb()

        senddata["tags"]["type"]="wakeup"
        senddata["fields"]["count"]=int(nWakeup)
        write_influxdb()

        senddata["tags"]["type"]="outofbed"
        senddata["fields"]["count"]=int(nOutBed)
        write_influxdb()
        del senddata["fields"]["count"]


        senddata["tags"]["type"]="score"
        senddata["fields"]["percent"]=float(score)
        write_influxdb()

        senddata["tags"]["type"]="efficiency"
        senddata["fields"]["percent"]=float(efficiency)
        write_influxdb()
        del senddata["fields"]["percent"]




# get sleep
print("Getting sleep raw...")
sleepRaw = read_api.sleep_get(
    data_fields=GetSleepField,
    startdate=ago,
    enddate=now,
    )


# pass sleep
senddata={}
senddata["tags"]={}
senddata["tags"]["source"]="docker withings-influxdbv2"
senddata["tags"]["origin"]="Withings"
senddata["fields"]={}


for serie in sleepRaw.series:
    hrAvg=0

    senddata["measurement"]="heart"
    senddata["tags"]["type"]="sleeping"

    for record in serie.hr:
        if debug:
            print(" ",record.timestamp," HR = ",record.value)
        time = record.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
        senddata["time"]=time
        senddata["tags"]["mode"]="raw"
        senddata["fields"]["bpm"]=float(record.value)
        write_influxdb()

    for record in serie.sdnn_1:
        if debug:
            print(" ",record.timestamp," SD = ",record.value)
        time = record.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
        senddata["time"]=time
        senddata["tags"]["mode"]="sdev"
        senddata["fields"]["bpm"]=float(record.value)
        write_influxdb()

    for record in serie.rmssd:
        if debug:
            print(" ",record.timestamp,"RMS = ",record.value)
        time = record.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
        senddata["time"]=time
        senddata["tags"]["mode"]="rms"
        senddata["fields"]["bpm"]=float(record.value)
        write_influxdb()

    senddata["measurement"]="respiration"
    senddata["tags"]["mode"]="raw"

    for record in serie.rr:
        if debug:
            print(" ",record.timestamp," RR = ",record.value)
        time = record.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
        senddata["time"]=time
        senddata["fields"]["bpm"]=float(record.value)
        write_influxdb()

    del senddata["fields"]["bpm"]
    senddata["measurement"]="sleep"
    senddata["tags"]["type"]="snoring"
    senddata["tags"]["mode"]="raw"

    for record in serie.snoring:
        if debug:
            print(" ",record.timestamp," SN = ",record.value)
        time = record.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
        senddata["time"]=time
        senddata["fields"]["duration"]=round(record.value/3600,2)
        write_influxdb()

    del senddata["fields"]["duration"]

print("Done")
exit(0)