# withings-influxdbv2
Docker container to fetch data from the Withings API and place it in your influxdb. Uses https://github.com/vangorra/python_withings_api

## Withings API Token
- Go to: https://developer.withings.com
- Sign up.
- Get your client id and client secret.
- Get your Callback URL

## InfluxDBv2 Setup

Setup InfluxDBv2, create bucket and create a token with write permissions for said bucket.

## Docker Setup
```
$ docker run -d \
 -e WITHINGS_CLIENT_ID="<WITHINGS CLIENT ID>" \
 -e WITHINGS_CLIENT_SECRET="<WITHINGS CLIENT SECRET>" \
 -e WITHINGS_AUTH_CODE="<WITHINGS_AUTH_CODE>" \
 -e INFLUXDB2_HOST="<INFLUXDBv2 SERVER>" \
 -e INFLUXDB2_PORT="8086" \
 -e INFLUXDB2_ORG="Home" \
 -e INFLUXDB2_TOKEN="" \
 -e INFLUXDB2_BUCKET="DEV" \
 --name "Withings-InfluxDBv2" \
dbsqp/withings-influxdbv2:latest
```

## Debug
To report out further details in the log enable debug:
```
 -e DEBUG="true"
```
