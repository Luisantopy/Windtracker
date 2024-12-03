# command in shell to run program in background:
# $ sudo apt screen install
# session erstellen und skript ausführen: 
# $ screen -S Wind_Tracking_Burnair_RPItemp
# $ python3 Wind_Tracking_Burnair_RPItemp.py
# wieder zur session verbinden:
# $ screen -r Wind_Tracking_Burnair_RPItemp.py

# # initial module import
import minimalmodbus
import time
import requests
import statistics
import board
import adafruit_dht
from gpiozero import CPUTemperature


# Initialize the instruments 
# for wind:
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
instrument_wd = initialize_instruments('/dev/ttyUSB0', 2)  # port name, slave address of Wind Direction
instrument_ws = initialize_instruments('/dev/ttyUSB1', 2)  # port name, slave address of Wind Speed

# Initialize the instruments
# for temperature: the dht device
# dhtDevice = adafruit_dht.DHT11(board.D17)

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
# - this is not relevant for sending data to wu, only for logging data to terminal

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
        if directions_keys[0] <= degrees_raw <=  directions_keys[1]: # check lower and upper limit of keys
            return direction
    return "unknown"

# send data to weather underground: 
# set up variables
WUurl = "https://weatherstation.wunderground.com/weatherstation/updateweatherstation.php?"
WU_station_id = "IMOLLI27"
WU_station_pwd = "jEzgBS2a"
WUcreds = f"ID={WU_station_id}&PASSWORD={WU_station_pwd}"
date_str = "&dateutc=now"
action_str = "&action=updateraw"

# send different sensor values
def send_to_weatherunderground(parameter,value): # set up parameter and value to hold sensor measurements tracked below
    request_url = f"{WUurl}{WUcreds}{date_str}&{parameter}={value}{action_str}" # use variables 
    response = requests.get(request_url) # create get request
    print(f"Sent data to Weather Underground: {parameter}={value}, Status: {response.status_code}") # not required, only for checking

# main loop for data collection and transmission

send_data_counter = 0       # Counter to track 10-minute interval for sending data to Burnair
store_speeds = []   # set up list to store wind speed sensor readings
store_directions = []   # set up list to store wind direction sensor readings
store_temperatures = []

while True:
    try: # outer loop runs every 1 seconds
        
        # read temperature and humidity every 1 seconds
        indoortemp_c = CPUTemperature()
        indoortempf = indoortemp_c.temperature * (9 / 5) + 32
        #temperature_c = dhtDevice.temperature
        #temperature_f = temperature_c * (9 / 5) + 32
        #humidity = dhtDevice.humidity
        #print(f"Temperature: {temperature_c}°C")
        #print(f"Humidity: {humidity}")
        print(f"RPi CPU Temperature: {indoortemp_c}°C")

        # store wind values for wind direction 2 min avg readings 
        store_temperatures.append(indoortempf)
        print(store_temperatures)

        # call function to send data to weather underground every iteration
        # param = winddir, value = wind_direction_deg 
        #send_to_weatherunderground("indoortempf", indoortempf) # [F outdoor temperature]

        #send_to_weatherunderground("humidity", humidity)#  - [% outdoor humidity 0-100%]

        #send_to_weatherunderground("windspeedmph", wind_speed_mph) # [mph instantaneous wind speed]
        #send_to_weatherunderground("winddir", wind_direction_deg) # [0-360 instantaneous wind direction]

        # increment counter
        send_data_counter += 1 # Add 1 seconds for each iteration
        print(send_data_counter)
        
        # send data to Burnair every 10 minutes
        if send_data_counter >= 600: # 600 seconds = 10 minutes, 120 seconds = 2 minutes

            # 10min average temperature
            rpi_temp_avg = statistics.mean(store_temperatures) # get avg value from stored values 
            print(f"CPU 10 min avg temperature: {rpi_temp_avg}°C") # print 10min avg CPU temp 
            send_to_weatherunderground("tempf", indoortempf) # [F outdoor temperature]

            send_data_counter = 0 # Reset counter after sending
            store_temperatures = [indoortempf] # Reset list of stored values to latest wind speed reading after 2 minutes 

    # set up exceptions
    except RuntimeError as error:
        # Errors happen fairly often, DHT's are hard to read, just keep going
        print(error.args[0])
        #time.sleep(2.0)
        continue
    except IOError:
        print("Failed to send data")
        #break
    except Exception as e:
        print(f"Error: {e}")
        break

    # Wait for x seconds before the next measurement
    time.sleep(1) 