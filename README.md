# elprice-influxdb
Docker container for getting electricity prices for Norway and push it to an InfluxDB.

# Background
Uses the API at https://www.hvakosterstrommen.no/ to get the electricity prices for a price region in Norway.
You can specify one date to get the prices for that day, or one month to get the prices for all days that month. If neither is specified a task will be set up that twice a day will get the prices for the current day and the next day.
All the collected prices will be written to an InfluxDB that you need to provide. The InfluxDB needs to be version 1.8 or later. 

Due to the way the timestamp is collected, only prices on or after 2022-10-02 are available.

# Quickstart
If you don't have an InfluxDB you can create one in Docker. This is done slightly different with version 1 and version 2.
Also a custom bridge network is created to make it easy to connect to the database, and this will also eliminate the need to expose any ports unless it should be available outside of docker. All containers will be set up to use this network.
## Create InfluxDB version 1.8
```bash
#Create network
docker network create mybridge
#Start InfluxDB
docker run -d --name influxdb --network mybridge --restart always -v influxdb2:/var/lib/influxdb influxdb:1.8
#Create database
docker exec -d influxdb18 /usr/bin/influx -execute 'create database elprice'
```
## Create InfluxDB version 2.4
```bash
#Create network
docker network create mybridge
#Start InfluxDB
docker run -d --name influxdb --network mybridge --restart always -v influxdb2:/var/lib/influxdb2 influxdb:2.4
#Create user and bucket
docker exec influxdb influx setup --username 'influxuser' --password 'MySecretPa$$w0rd' --org 'my-org' --bucket 'elprice' --retention 0 --force
#Get access token
docker exec influxdb influx auth list --user 'influxuser' --hide-headers | cut -f 3
```
## Set up elprice-influxdb
You need to provide the hostname for the InfluxDB. You should also give the price region you are interested in. If you have InfluxDB version 2 you also need to provide the access token.
A standard run that wil set up the scheduled job could look like this:
```bash
docker run -d \
 -e INFLUXDB_HOST=influxdb \
 -e PRICE_REGION=NO3 \
 -e INFLUXDB_TOKEN=ThisIsTheTokenYouFoundWhenListingItAfterCreatingTheInfluxDBVersion2== \
 --name elprice \
 --network mybridge \
 --restart always \
 okhoel/elpriceinfluxdb:latest
```
If you want to get the prices for a specific day you can use the environment variable PRICE_DATE:
```bash
docker run -d \
 -e INFLUXDB_HOST=influxdb \
 -e PRICE_DATE=2022-10-15 \
 -e INFLUXDB_TOKEN=ThisIsTheTokenYouFoundWhenListingItAfterCreatingTheInfluxDBVersion2== \
 --name elprice \
 --network mybridge \
 okhoel/elpriceinfluxdb:latest
```
If you want to get all the prices for a full month you can use the environment variable PRICE_MONTH:
```bash
docker run -d \
 -e INFLUXDB_HOST=influxdb \
 -e PRICE_MONTH=2022-10 \
 -e INFLUXDB_TOKEN=ThisIsTheTokenYouFoundWhenListingItAfterCreatingTheInfluxDBVersion2== \
 --name elprice \
 --network mybridge \
 okhoel/elpriceinfluxdb:latest
```
If you specify the date or month the container will stop after the run (unless debugging is turned on). If you specify both date and month only the date is used.

# Environment variables
There are some environment variables that can be used to customize the container. Most of them have a default value that can be used.

A special note on the INFLUXDB_TOKEN:  
This must be specified if you are using InfluxDB version 2, but should not be specified for InfluxDB version 1.  
If it is not specified it will be set to a combination of INFLUXDB_USER and INFLUXDB_PW.

## All the available environment variables
| Name | Default value | Format | Comment |
| ---- | ------------- | ------ | ------- |
| INFLUXDB_HOST | influxdb | Hostname / DNS name | 
| INFLUXDB_PORT | 8086 | Port number |
| INFLUXDB_USER | root | Username | Only used with InfluxDB v1 |
| INFLUXDB_PW | root | Password | Only used with InfluxDB v1 |
| INFLUXDB_TOKEN | $INFLUXDB_USER:$INFLUXDB_PW | Token | Must be specified with InfluxDB v2. |
| INFLUXDB_DATABASE | elprice | Database name | The name of the database created for InfluxDB v1 |
| INFLUXDB_BUCKET | $INFLUXDB_DATABASE | Bucket name | The name of the bucket created for InfluxDB v2. If not specified the value for INFLUXDB_DATABASE will be used |
| INFLUXDB_ORG | my-org | A string | Only for v2. Must be the same as the org given when creating the bucket |
| PRICE_REGION | NO3 | NO1 / NO2 / NO3 / NO4 / NO5 | One of the five price regions in Norway |
| PRICE_DATE | | YYYY-MM-DD | |
| PRICE_MONTH | | YYYY-MM | |
| DEBUG | False | True / False | Will turn on more logging, and leave the container running after getting one date or month |
