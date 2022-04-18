# withings-influxdbv2
Docker container to fetch data from the Withings API and place it in your influxdb. Uses a modified version of https://github.com/vangorra/python_withings_api to allow access to further paramaters from withings API https://developer.withings.com/api-reference/. 

## Withings API Token
- Go to: https://developer.withings.com
- Sign up.
- Get your client id and client secret.
- Setup your callback URL

## InfluxDBv2 Setup

Setup InfluxDBv2, create bucket and create a token with write permissions for said bucket.

## Docker Setup
```
$ docker run -d \
 -e WITHINGS_CLIENT_ID="<WITHINGS CLIENT ID>" \
 -e WITHINGS_CLIENT_SECRET="<WITHINGS CLIENT SECRET>" \
 -e WITHINGS_AUTH_CODE="INIT/<WITHINGS_AUTH_CODE>/-" \
 -e INFLUXDB2_HOST="<INFLUXDBv2 SERVER>" \
 -e INFLUXDB2_PORT="8086" \
 -e INFLUXDB2_ORG="Home" \
 -e INFLUXDB2_TOKEN="" \
 -e INFLUXDB2_BUCKET="DEV" \
 --name "Withings-InfluxDBv2" \
dbsqp/withings-influxdbv2:latest
```
Start container WITHINGS_AUTH_CODE="INIT", this will generate URL in log. Goto URL, authenticate and copy authorisation code. Restart container with WITHINGS_AUTH_CODE="received authorisation code". Check log to ensure oauth authorisation worked and token created. This can take multiple trys for some reason. Once workng reset WITHINGS_AUTH_CODE="" and restart. Token is stored in directory for easy removal via docker volume.

## Debug
To report out further details in the log enable debug:
```
 -e DEBUG="true"
```
