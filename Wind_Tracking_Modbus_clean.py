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
"""
# Wind direction conversion (not required, only for converting wind direction to terminal in °)
def get_wind_direction(degrees_raw):
    # create dictionary to hold wind directions
    directions = {
        (0, 112): "North",
        (112, 337): "North-northeast",
        (337, 562): "Northeast",
        (562, 787): "East-northeast",
        (787, 1012): "East",
        (1012, 1237): "East-southeast",
        (1237, 1462): "Southeast",
        (1462, 1687): "South-southeast",
        (1687, 1912): "South",
        (1912, 2137): "South-southwest",
        (2137, 2362): "Southwest",
        (2362, 2587): "West-southwest",
        (2587, 2812): "West",
        (2812, 3037): "West-northwest",
        (3037, 3262): "Northwest",
        (3262, 3487): "North-northwest",
        (3487, 3600): "North"
    }
    for range_limits, direction in directions.items(): # check dictionary for values
        if range_limits[0] <= degrees_raw < range_limits[1]: # check if sensor value (degrees_raw) falls between index 0 and 1
            return direction # returns matching direction
    return "Unknown"
"""
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
        send_to_weatherunderground("winddir", wind_direction_deg) 

        # read and process wind speed
        wind_speed_raw = instrument_ws.read_register(0, 1) # get raw values from instrument; register number, number of decimals
        wind_speed_mph = round(wind_speed_raw * 2.23694, 2)  # convert to mph and round 
        print(f"Wind Speed: {wind_speed_raw} m/s, {wind_speed_mph} mph") # print wind direction in m/s and mph
        # call function to send wind direction data in degrees to weather underground
        # param = windspeedmph, value = wind_speed_mph
        send_to_weatherunderground("windspeedmph", wind_speed_mph)
    
    # set up expections
    except IOError:
        print("Failed to read from instrument")
        break
    except Exception as e:
        print(f"Error: {e}")
        break

    # Wait for x seconds before the next measurement
    time.sleep(60)  
