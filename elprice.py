"""Get the norwegian electricity prices for a given period and push them to an InfluxDB"""
import os
import sys
from datetime import datetime, timedelta
from enum import Enum
import requests
from dateutil import tz
from influxdb_client import InfluxDBClient, rest
from influxdb_client.client.write_api import SYNCHRONOUS

class Region(Enum):
    """Class for validating region input"""
    NO1 = 1
    NO2 = 2
    NO3 = 3
    NO4 = 4
    NO5 = 5

def get_day_prices(date: datetime, region: str) -> str | None:
    """Get the electricity prices for a given date as json"""
    if hasattr(Region, region):
        date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        print("Collecting data for", date.strftime("%Y-%m-%d"))
        urldate = date.strftime('%Y/%m-%d_')
        url = "https://www.hvakosterstrommen.no/api/v1/prices/" + urldate + region + ".json"
        if debug:
            print(url)
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            responsejson = response.json()
            if debug:
                print(responsejson)
            returnjson = []
            for price in responsejson:
                element = {
                    "measurement": "price",
                    "tags": {
                        "region": region
                    },
                    "fields": price,
                    "time": price['time_start']
                }
                if debug:
                    print(element)
                returnjson.append(element)
            return returnjson
        else:
            print("WARNING: Status code", response.status_code,"when calling", url)
    else:
        print("ERROR: Illegal region", region, "provided")
        sys.exit(1)
    return None

def write_to_influx(s: str, bucket: str) -> None:
    """Writing data to InfluxDB"""
    if debug:
        print("Starting to write to InfluxDB on", influxhost)
    with InfluxDBClient(url=influxurl, token=influxtoken, org=influxorg) as client:
        writeclient = client.write_api(write_options=SYNCHRONOUS)
        try:
            print("Writing data points to InfluxDB")
            writeclient.write(record=s, bucket=bucket)
        except rest.ApiException:
            print("ERROR: Failure writing to database. Invalid token?")
        except requests.exceptions.ConnectionError:
            print("ERROR: Unable to connect to", influxhost, "for writing")
        except Exception as e:
            print("ERROR: Something went wrong when writing to database:", type(e).__name__)
        else:
            if debug:
                print("Succesfully written data to database")

# settings from EnvionmentValue
influxhost=os.getenv('INFLUXDB_HOST', "influxdb")
influxport=os.getenv('INFLUXDB_PORT', '8086')
influxuser=os.getenv('INFLUXDB_USER', 'root')
influxpw=os.getenv('INFLUXDB_PW', 'root')
influxtoken=os.getenv('INFLUXDB_TOKEN', influxuser+":"+influxpw)
influxorg=os.getenv('INFLUXDB_ORG', 'my-org')
influxdb=os.getenv('INFLUXDB_DATABASE', 'elprice')
influxbucket=os.getenv('INFLUXDB_BUCKET', influxdb)
influxurl="http://"+influxhost+":"+influxport
priceregion=os.getenv('PRICE_REGION', 'NO3')
pricedate=os.getenv('PRICE_DATE')
pricemonth=os.getenv('PRICE_MONTH')
debug=os.getenv('DEBUG', 'false').lower() == 'true'

if debug:
    print("Environment variables:")
    print(" InfluxDB host (v1):", influxuser + "@" + influxhost + ":" + str(influxport))
    print(" InfluxDB password (v1):", '*'*len(influxpw))
    print(" InfluxDB database (v1):", influxdb)
    print(" InfluxDB url (v2):", influxurl)
    print(" InfluxDB bucket (v2):", influxbucket)
    print(" InfluxDB org (v2):", influxorg)
    if influxtoken:
        print(" InfluxDB token length (v2):", len(influxtoken))
    else:
        print(" No InfluxDB token provided!")
    print(" Price region:", priceregion)
    if pricedate:
        print(" Chosen date:", pricedate)
    if pricemonth:
        print(" Chosen month:", pricemonth)

timezone = tz.gettz("Europe/Oslo")

if pricedate:
    print("Getting data for one day:", pricedate)
    try:
        date = datetime.strptime(pricedate, "%Y-%m-%d").replace(tzinfo=timezone)
        res = get_day_prices(date, priceregion)
        if res:
            write_to_influx(s=res, bucket=influxbucket)
    except ValueError:
        print("ERROR: Invalid date", pricedate)
    except Exception as e:
        print("ERROR: Something went wrong:", type(e).__name__)
elif pricemonth:
    print("Getting data for one month:", pricemonth)
    try:
        m = datetime.strptime(pricemonth, "%Y-%m").replace(tzinfo=timezone)
        numdays = ((m+timedelta(days=31)).replace(day=1)-m).days
        for day in range(1,numdays+1):
            date = m.replace(day=day)
            res = get_day_prices(date, priceregion)
            if res:
                write_to_influx(s=res, bucket=influxbucket)
    except ValueError:
        print("ERROR: Invalid month ", pricemonth)
    except Exception as e:
        print("ERROR: Something went wrong:", type(e).__name__)
else:
    print("Getting data for today and tomorrow")
    today = datetime.now(timezone)
    for date in [today, today+timedelta(days=1)]:
        res = get_day_prices(date, priceregion)
        if res:
            write_to_influx(s=res, bucket=influxbucket)
