# initial module import
import minimalmodbus
import time
import requests

# Initialize the instruments 
def initialize_instruments(port, slave_adress):
    instrument = minimalmodbus.Instrument(port, slave_adress)
    instrument.serial.baudrate = 9600        # Baud rate
    instrument.serial.bytesize = 8           # Number of data bits
    instrument.serial.parity = minimalmodbus.serial.PARITY_NONE  # Parity (None, Even, Odd)
    instrument.serial.stopbits = 1           # Stop bits
    instrument.serial.timeout = 1            # Timeout in seconds
    instrument.mode = minimalmodbus.MODE_RTU # Set mode to RTU (which is typical for RS485)
    return instrument

# call the instruments 
instrument_wd = initialize_instruments('/dev/ttyUSB1', 2)  # port name, slave address of Wind Direction
instrument_ws = initialize_instruments('/dev/ttyUSB0', 2)  # port name, slave address of Wind Speed

# scan registers to find where the wind direction is stored 
# - this is not relevant for measuring, only for setting up the .read_register below 
for register in range(1):  
    try:
        value = instrument_wd.read_register(register, 0)  # Register number, 0 decimals
        print(f"Register Wind Direction {register}: {value}")
    except IOError:
        print(f"Failed to read register {register}")
    except Exception as e:
        print(f"Error: {e}")

# Scan multiple registers to find where the wind speed is stored
# - this is not relevant for measuring, only for setting up the .read_register below

for register in range(1): 
    try:
        value = instrument_ws.read_register(register, 0)  # Register number, 0 decimals
        print(f"Register Wind Speed {register}: {value}")
    except IOError:
        print(f"Failed to read register {register}")
    except Exception as e:
        print(f"Error: {e}")
# function for converting measured wind direction data into North-South values

def get_wind_direction(degrees_raw):
    # dictionary to group measurements:
    directions = {
        (0, 112): "North",
        (113, 337): "North-northeast",
        (338, 562): "Northeast",
        (563, 787): "East-northeast",
        (788, 1012): "East",
        (1013, 1237): "East-southeast",
        (1238, 1462): "Southeast",
        (1463, 1687): "South-southeast",
        (1688, 1912): "South",
        (1913, 2137): "South-southwest",
        (2138, 2362): "Southwest",
        (2363, 2587): "West-southwest",
        (2588, 2812): "West",
        (2813, 3037): "West-northwest",
        (3038, 3262): "Northwest",
        (3263, 3487): "North-northwest",
        (3488, 3600): "North"
    }
    # check which group of keys the measurement is part of
    for directions_keys, direction in directions.items():
        if directions_keys[0] <= degrees_raw >=  directions_keys[1]: # check lower and upper limit of keys
            return direction
        else: return "unknown"

# send data to weather underground: 
# set up variables
WUurl = "https://weatherstation.wunderground.com/weatherstation/updateweatherstation.php?"
WU_station_id = "IMOLLI25"
WU_station_pwd = "vdmVzZ6C"
WUcreds = f"ID={WU_station_id}&PASSWORD={WU_station_pwd}"
date_str = "&dateutc=now"
action_str = "&action=updateraw"

# create function to send both sensor values
def send_to_weatherunderground(parameter,value): # set up parameter and value to hold sensor measurements tracked below
    request_url = f"{WUurl}{WUcreds}{date_str}&{parameter}={value}{action_str}" # use variables 
    response = requests.get(request_url) # create get request
    print(f"Sent data to Weather Underground: {parameter}={value}, Status: {response.status_code}") # not required, only for checking

# function to collect measurements for 2 minutes, create average
def wind_twominute_avg(wind_speed_mph):
    twominute_sum = 0
    for i in range(5):
        twominute_sum += wind_speed_mph
        return twominute_sum/4

# function for wind gusts
def wind_gusts(wind_speed_mph):
    max_tenminutes = 0
    for i in range(11):
        tenminute_gusts = []
        tenminute_gusts += [int(wind_speed_mph)]
        max_tenminutes = max(tenminute_gusts)
    return max_tenminutes

# function for wind gusts directions
def windgust_directions(max_tenminutes):
    windgust_direction = get_wind_direction(max_tenminutes)
    return windgust_direction

# main loop for data collection and transmission
while True:
    try:
        # read and process wind direction
        wind_direction_raw = instrument_wd.read_register(0, 0, signed=False) # get raw values from instrument; ; register number, number of decimals
        wind_direction_deg = int(wind_direction_raw / 10) # divide by ten to get °
        wind_direction = get_wind_direction(wind_direction_raw) # call wind direction function to view raw data in degrees
        print(f"Wind Direction: {wind_direction_deg}° ({wind_direction})") # print wind direction in ° and words

        # call function to send wind direction data in degrees to weather underground
        # param = winddir, value = wind_direction_deg
        send_to_weatherunderground("winddir", wind_direction_deg) # [0-360 instantaneous wind direction]

        # read and process wind speed
        wind_speed_raw = instrument_ws.read_register(0, 1) # get raw values from instrument; register number, number of decimals
        wind_speed_mph = round(wind_speed_raw * 2.23694, 2)  # convert to mph and round 
        windspdmph_avg2m = wind_twominute_avg(wind_speed_mph)
        windgusts_mph = wind_gusts(wind_speed_mph)
        print(f"Wind Speed: {wind_speed_raw} m/s, {wind_speed_mph} mph") # print wind direction in m/s and mph
        # call function to send wind direction data in degrees to weather underground
        # param = windspeedmph, value = wind_speed_mph
        send_to_weatherunderground("windspeedmph", wind_speed_mph) # [mph instantaneous wind speed]
        send_to_weatherunderground("windspdmph_avg2m", windspdmph_avg2m) # [mph 2 minute average wind speed mph]
        send_to_weatherunderground("windgustmph_10m", windgusts_mph) # [mph past 10 minutes wind gust mph]

        windgustdir = windgust_directions(windgusts_mph) # unsure if this is correct 
        send_to_weatherunderground("windgustdir_10m", windgustdir) #  - [0-360 past 10 minutes wind gust direction]



    # set up expections
    except IOError:
        print("Failed to read from instrument")
        break
    except Exception as e:
        print(f"Error: {e}")
        break
   
    print(f"The 2 minute average is {wind_twominute_avg(wind_speed_mph)} mph.")
    print(f"The max wind speed over the last 10 minutes was {wind_gusts(wind_speed_mph)} mph.")

    # Wait for x seconds before the next measurement
    time.sleep(30) 
    




