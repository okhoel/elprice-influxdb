# elprice-influxdb
Docker container for getting electricity prices for Norway and push it to an InfluxDB.

# Background
Uses the API at https://www.hvakosterstrommen.no/ to get the electricity prices for a price region in Norway.
You can specify one date to get the prices for that day, or one month to get the prices for all days that month. If neither is specified a task will be set up that twice a day will get the prices for the current day and the next day.
All the collected prices will be written to an InfluxDB that you need to provide. The InfluxDB needs to be version 1.8 or later. 

Data in the API is available from 2021-12-01.

# Supported tags and Dockerfile links
- [`1`, `1.1`, `1.1.0`, `latest`](https://github.com/okhoel/elprice-influxdb/blob/v1.1.0/Dockerfile)
- [`1.0`](https://github.com/okhoel/elprice-influxdb/blob/v1.0.0/Dockerfile)

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
docker exec -d influxdb /usr/bin/influx -execute 'create database elprice'
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
A standard run that will set up the scheduled job could look like this:
```bash
docker run -d \
 -e INFLUXDB_HOST=influxdb \
 -e PRICE_REGION=NO3 \
 -e INFLUXDB_TOKEN=ThisIsTheTokenYouFoundWhenListingItAfterCreatingTheInfluxDBVersion2== \
 --name elprice \
 --network mybridge \
 --restart always \
 ohkay/elpriceinfluxdb:latest
```
If you want to get the prices for a specific day you can use the environment variable PRICE_DATE:
```bash
docker run -d --rm \
 -e INFLUXDB_HOST=influxdb \
 -e PRICE_DATE=2022-10-15 \
 -e PRICE_REGION=NO3 \
 -e INFLUXDB_TOKEN=ThisIsTheTokenYouFoundWhenListingItAfterCreatingTheInfluxDBVersion2== \
 --name elprice \
 --network mybridge \
 ohkay/elpriceinfluxdb:latest
```
If you want to get all the prices for a full month you can use the environment variable PRICE_MONTH:
```bash
docker run -d --rm \
 -e INFLUXDB_HOST=influxdb \
 -e PRICE_MONTH=2022-10 \
 -e PRICE_REGION=NO3 \
 -e INFLUXDB_TOKEN=ThisIsTheTokenYouFoundWhenListingItAfterCreatingTheInfluxDBVersion2== \
 --name elprice \
 --network mybridge \
 ohkay/elpriceinfluxdb:latest
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
| OVERRIDE_URL | | Web url to json file | Used to import data from a custom url - see note |

## Note on OVERRIDE_URL
In case you need to import data from a different source than the API at https://www.hvakosterstrommen.no/ you can specify it with this environment variable. Doing this will ignore any dates specified.  
A couple of things to remember:
* The format of the json file the url points to must be compatible with https://www.hvakosterstrommen.no/strompris-api
* You still have to specify a price region

### Example of usage
```docker run -d --rm \
 -e INFLUXDB_HOST=influxdb \
 -e OVERRIDE_URL "https://gist.github.com/okhoel/f1dbbe0788dbaa718eee2dce69926cf0/raw/c7584946654fe1ded7f23195c29274e3a53373e9/elprice_2022_10_30_NO3.json" \
 -e PRICE_REGION=NO3 \
 -e INFLUXDB_TOKEN=ThisIsTheTokenYouFoundWhenListingItAfterCreatingTheInfluxDBVersion2== \
 --name elprice \
 --network mybridge \
 ohkay/elpriceinfluxdb:latest
```

### Error in data at https://www.hvakosterstrommen.no/ related to the ending of DST on October 30th 2022
NOTE: The data in the API is fixed, but these files will be available to use as an example of how to use the OVERRIDE_URL.

The ending of daylight savings time on October 30th 2022 meant that this day was 25 hours long, and this introduced an error in the data at https://www.hvakosterstrommen.no/strompris-api. Before the data in the API was fixed the OVERRIDE_URL coul be used to correct this data. Corrected json files for each region can be found here:
| Region | URL |
| -- | -- |
| NO1 | https://gist.github.com/okhoel/e13bcb8713374d121eaf5101da79a917/raw/cf790c3b2b64653416010ee978513cf24029138a/elprice_2022_10_30_NO1.json |
| NO2 | https://gist.github.com/okhoel/ba55d5ee8f71df73e1d574fb704d7aec/raw/8e441bf77812f91cb5cea099037526791cab0454/elprice_2022_10_30_NO2.json |
| NO3 | https://gist.github.com/okhoel/f1dbbe0788dbaa718eee2dce69926cf0/raw/c7584946654fe1ded7f23195c29274e3a53373e9/elprice_2022_10_30_NO3.json |
| NO4 | https://gist.github.com/okhoel/31b15cfa6dfc622c0ca22dc4c65d2def/raw/eb6f440b84222f60f5415fbb1785554a7e209646/elprice_2022_10_30_NO4.json |
| NO5 | https://gist.github.com/okhoel/3da25ce540c283da3c7dc105b3e33e35/raw/053ef5d3d82418c82cc4bc3dfc590da80260b909/elprice_2022_10_30_NO5.json |

# Version history
## 1.1.0
* Added support for getting data from a custom url - OVERRIDE_URL
* Built containers for linux/arm in addition to linux/amd64
## 1.0.0
* Initial version
