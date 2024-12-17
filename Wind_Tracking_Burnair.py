# requirements: python 13.11, .venv activated, ch340 driver installed, modules installed
# sudo reboot before running program, otherwise dht sensor won't read …
# 
# run program in background:
# $ sudo apt screen install
# create session and run skript: 
# $ screen -S filename
# $ python3 filename.py
# connect to session:
# $ screen -r filename.py

# initial module import
import minimalmodbus    # to read wind sensors
import time             
import requests         # to send data 
import statistics       # for avg and max values
import board            # for dht sensor
import adafruit_dht     # for dht sensor
from gpiozero import CPUTemperature # for tracking CPU temperature

# Initialize the instruments 
# for wind:
def initialize_instruments(port, slave_adress):
    instrument = minimalmodbus.Instrument(port, slave_adress)
    instrument.serial.baudrate = 9600        # Baud rate
    instrument.serial.bytesize = 8           # Number of data bits
    instrument.serial.parity = minimalmodbus.serial.PARITY_NONE  # Parity (None, Even, Odd)
    instrument.serial.stopbits = 1           # Stop bits
    instrument.serial.timeout = 1            # Timeout in seconds
    instrument.mode = minimalmodbus.MODE_RTU # Set mode to RTU (for RS485)
    return instrument

# call wind instruments (check slave address with sudo ls -l /dev)
instrument_wd = initialize_instruments('/dev/ttyUSB0', 2)  # port name, slave address of Wind Direction 
instrument_ws = initialize_instruments('/dev/ttyUSB1', 2)  # port name, slave address of Wind Speed

# Initialize the instruments
# for temperature: dht device
dhtDevice = adafruit_dht.DHT11(board.D17)

# scan registers to find where the wind direction is stored 
# - this is not relevant for measuring, only for setting up the .read_register below and ensuring correct use of registers
for register in range(1):  # increase range if register != 1
    try:
        value = instrument_wd.read_register(register, 0)  # Register number, 0 decimals
        print(f"Register Wind Direction {register}: {value}")
    except IOError:
        print(f"Failed to read register {register}")
    except Exception as e:
        print(f"Error: {e}")

# scan registers to find where the wind speed is stored
# - this is not relevant for measuring, only for setting up the .read_register below
for register in range(1): # increase range if register != 1
    try:
        value = instrument_ws.read_register(register, 0)  # Register number, 0 decimals
        print(f"Register Wind Speed {register}: {value}")
    except IOError:
        print(f"Failed to read register {register}")
    except Exception as e:
        print(f"Error: {e}")

# function for converting measured wind direction data into North-South values
# - this is not relevant for sending data to wu, only for reading data in terminal

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

# fahrenheit calculator
def celsius_to_fahrenheit(celsius):
    return celsius * (9 / 5) + 32

# data to weather underground: 
# set up variables
WUurl = "https://weatherstation.wunderground.com/weatherstation/updateweatherstation.php?"
WU_station_id = "IMOLLI28"
WU_station_pwd = "SZYeoboH"
WUcreds = f"ID={WU_station_id}&PASSWORD={WU_station_pwd}"
date_str = "&dateutc=now"
action_str = "&action=updateraw"
WU_station_id_R = "IMOLLI27" # 2nd station for tracking cpu temperature
WU_station_pwd_R = "jEzgBS2a"
WUcreds_R = f"ID={WU_station_id_R}&PASSWORD={WU_station_pwd_R}"

# function to send different sensor values
def send_to_weatherunderground(data): # accepts data values as dictionary 
    # send different sensor values with retry logic
    max_retries = 10
    retry_delay = 3  # seconds
    attempt = 0

    # Construct URL with multiple parameters
    parameters = "&".join([f"{key}={value}" for key, value in data.items()]) # send value
    request_url = f"{WUurl}{WUcreds}{date_str}&{parameters}{action_str}"

    while attempt < max_retries:
        try:
            response = requests.get(request_url) # create get request
            if response.status_code == 200:
                print(f"Sent data to Weather Underground: {data}, Status: {response.status_code}") 
                return True #successful send
            else: 
                print(f"Failed to send data: {data}, Status: {response.status_code}. Retrying...")
        except requests.RequestException as e: 
            print(f"Request failed: {e}. Retrying...")
        
        attempt += 1
        time.sleep(retry_delay)

        # If all retries fail, log failure and return False
    print(f"Failed to send data to Weather Underground after {max_retries} attempts.")
    return False

# function to send CPU temp 
def send_to_weatherunderground_R(parameter,value): # set up parameter and value to hold sensor measurements tracked below
    # Ensure the value has 1 decimal place
    value = round(value, 1)
    request_url = f"{WUurl}{WUcreds_R}{date_str}&{parameter}={value}{action_str}" 
    response = requests.get(request_url) # create get request
    print(f"Sent CPU temp to Weather Underground: {parameter}={value}, Status: {response.status_code}") 

'''
# funtion to store sensor readings for 10 minute avg/ max values
def store_readings(sensor_reading, store_values):
    store_values.append(sensor_reading)
    return store_values

# function to calculate the mean value from 10 minute stored readings
def mean_values(store_values):
    mean_value = statistics.mean(store_values)
    return mean_value

# function to calculate the max value from 10 minute stored readings
def max_values(store_values):
    max_value = max(store_values)
    return max_value

# function to reset list of stored values after 10 minutes
def reset(store_values):
    store_values = []
    return store_values
'''

# main loop for data collection and transmission

send_data_counter = 0       # Counter to track 10-minute interval for sending data 

# set up lists to store sensor readings
store_speeds = []           
store_directions = []       
store_temperatures = []
store_humidity = []
store_cpu_temperature = [] 

while True:
    try: # outer loop runs every 1 seconds
        # read and process wind direction 
        wind_direction_raw = instrument_wd.read_register(0, 0, signed=False) # get raw values from instrument; register number, number of decimals
        wind_direction_deg = int(wind_direction_raw / 10) # divide by ten to get ° - this value is required by the API
        wind_direction = get_wind_direction(wind_direction_raw) # call wind direction function to get raw data in degrees
        print(f"Wind Direction: {wind_direction_deg}° ({wind_direction})") 
        # store wind values for wind direction 10 min avg readings 
        #store_directions = store_readings(wind_direction_deg, store_directions)
        store_directions.append(wind_direction_deg)

        # read and process wind speed 
        wind_speed_raw = instrument_ws.read_register(0, 1) # get raw values from instrument; register number, number of decimals
        wind_speed_mph = round(wind_speed_raw * 2.23694, 2)  # convert to mph and round - this value is required by the API
        print(f"Wind Speed: {wind_speed_raw} m/s, {wind_speed_mph} mph") 
        # store wind values for wind gust and 10 min avg readings 
        #store_speeds = store_readings(wind_speed_mph, store_speeds)
        store_speeds.append(wind_speed_mph) 
        
        # read temperature and humidity 
        temperature_c = dhtDevice.temperature
        temperature_f = celsius_to_fahrenheit(temperature_c) # - this value is required by the API
        # exception handling for temperature because dht sensor often fails reading properly 
        try: 
            store_temperatures.append(temperature_f) # store temperature values for 10 min avg readings 
            #store_temperatures = store_readings(temperature_f, store_temperatures)
        except ValueError: 
            continue # back to main program, incorrect values not stored in list 

        print(f"Temperature: {temperature_c}°")

        humidity = dhtDevice.humidity  # - this value is required by the API
        #store_humidity = store_readings(humidity, store_humidity)
        store_humidity.append(humidity) # store humidity values for 10 min avg readings 
        print(f"Humidity: {humidity}")

        # read CPU temperature
        indoortemp_c = CPUTemperature()
        indoortempf = celsius_to_fahrenheit(indoortemp_c.temperature)
        #store_cpu_temperature = store_readings(indoortempf, store_cpu_temperature)
        store_cpu_temperature.append(indoortempf) # store temperature values for 10 min avg readings 

        # send avg/ max data to Weather Underground every 10 minutes
        # increment counter
        send_data_counter += 1 # Add 1 seconds for each iteration
        print(send_data_counter)

        if send_data_counter >= 600: # 600 seconds = 10 minutes

            # 10 min average speed
            #wind_10minavg = mean_values(store_speeds)
            wind_10minavg = statistics.mean(store_speeds) # get avg value from stored values 
            print(f"Wind Speed 10 min avg: {wind_10minavg} mph") 
            
            # 10 min process wind gusts
            #wind_gust_10avg = max_values(store_speeds)
            wind_gust_10avg = max(store_speeds) # get max value from stored values 
            print(f"Wind Gusts 10 min: {wind_gust_10avg} mph") 

            # 10 min avg wind direction
            #wind_direction_10avg = mean_values(store_directions)
            wind_direction_10avg = statistics.mean(store_directions) # get avg value from stored values
            print(f"Wind Direction 10 min avg: {wind_direction_10avg}°")  

            # 10 min avg temperature 
            #temperature_10avg = mean_values(store_temperatures)
            temperature_10avg = statistics.mean(store_temperatures) # get avg value from stored values
            print(f"Outside temperature 10min avg: {temperature_10avg}°F")

            # 10 min avg humidity
            humidity_10avg = statistics.mean(store_humidity) # get avg value from stored values
            print(f"Humidity 10min avg: {humidity_10avg}°F")

            # 10 min avg CPU temperature
            #cpu_temp_10avg = mean_values(store_cpu_temperature)
            cpu_temp_10avg = statistics.mean(store_cpu_temperature) # get avg value from stored values
            print(f"CPU 10 min avg temperature: {cpu_temp_10avg}°")
            send_to_weatherunderground_R("tempf", cpu_temp_10avg) # send cpu temp 10 min avg to weather underground

            # prepare values for sending
            # ensure the value has 1 decimal place
            data_to_send = {
                "tempf": round(temperature_10avg, 1),
                "humidity": round(humidity_10avg, 1),
                "windspeedmph": round(wind_10minavg, 1),
                "winddir": round(wind_direction_10avg, 1),
                "windgustmph": round(wind_gust_10avg, 1)
            }
            # send the data
            # send_to_weatherunderground(data_to_send)

            # if not successful send after 10 retries:
            if not send_to_weatherunderground(data_to_send):
                print("Data transmission failed. Continuing with the next cycle.")

            # reset counter and list of stored values after 10 minutes
            send_data_counter = 0 

            '''store_speeds = reset(store_speeds)
            store_directions = reset(store_directions)
            store_temperatures = reset(store_temperatures)
            store_humidity = reset(store_humidity)
            store_cpu_temperature = reset(store_cpu_temperature)'''

            store_speeds = [] 
            store_directions = []  
            store_temperatures = []
            store_humidity = []
            store_cpu_temperature = []

    # set up exceptions
    except RuntimeError as error:
        # Errors happen fairly often, DHT's are hard to read, just keep going
        print(error.args[0])
        continue
    except IOError:
        print("Failed to send data")
    except Exception as e:
        print(f"Error: {e}")

    # repeat interval for reading sensor values every second
    time.sleep(1) 