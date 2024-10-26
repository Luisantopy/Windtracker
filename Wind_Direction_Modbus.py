# initial module import
import minimalmodbus
import time
import requests

# Initialize the instrument (Modbus RTU device)
instrument = minimalmodbus.Instrument('/dev/ttyUSB1', 2)  # port name, slave address

# Configure Modbus communication parameters according to wiki
instrument.serial.baudrate = 9600        # Baud rate
instrument.serial.bytesize = 8           # Number of data bits
instrument.serial.parity = minimalmodbus.serial.PARITY_NONE  # Parity (None, Even, Odd)
instrument.serial.stopbits = 1           # Stop bits
instrument.serial.timeout = 1            # Timeout in seconds 

# Set mode to RTU (which is typical for RS485)
instrument.mode = minimalmodbus.MODE_RTU


# Scan registers to find where the wind direction is stored 
# - this is not relevant for measuring, only for setting up the .read_register below
for register in range(1):  
    try:
        value = instrument.read_register(register, 0)  # Register number, 0 decimals
        print(f"Register {register}: {value}")
    except IOError:
        print(f"Failed to read register {register}")
    except Exception as e:
        print(f"Error: {e}")


# Now read the register
while True: # Read until an invalid measurement is logged or manually stopped in terminal with ctrl z
    try:
        # Read raw integer value (make sure it's interpreted as an integer, not a float)
        raw_value = instrument.read_register(0, 0, signed=False)  # Unsigned integer (0 decimals)
        #print(f"Raw Value (Integer): {raw_value}")
        #hex_value = hex(raw_value)  # Convert raw integer to hexadecimal 
        #print(f"Raw Value (Hexadecimal): {hex_value}")
        
        wind_direction_degree = int(raw_value/10) # divide raw_value by ten to get degrees
        print(f"The wind direction is {wind_direction_degree}°.")

        # the if - else part is only for checking measurements locally, not relevant for data sent to weather underground

        if raw_value < 112 and raw_value >= 0:
            wind_direction = "North" 
        elif raw_value < 337 and raw_value >= 112:
            wind_direction = "North-northeast"
        elif raw_value < 562 and raw_value >= 337:
            wind_direction = "Northeast"
        elif raw_value < 787 and raw_value >= 562:
            wind_direction = "East-northeast"
        elif raw_value < 1012 and raw_value >= 787:
            wind_direction = "East"
        elif raw_value < 1237 and raw_value >= 1012:
            wind_direction = "East-southeast"
        elif raw_value < 1462 and raw_value >= 1237:
            wind_direction = "Southeast"
        elif raw_value < 1687 and raw_value >= 1462:
            wind_direction = "South-southeast"
        elif raw_value < 1912 and raw_value >= 1687:
            wind_direction = "South"
        elif raw_value < 2137 and raw_value >= 1912:
            wind_direction = "South-southwest"
        elif raw_value < 2362 and raw_value >= 2137:
            wind_direction = "Southwest"
        elif raw_value < 2587 and raw_value >= 2362:
            wind_direction = "West-southwest"
        elif raw_value < 2812 and raw_value >= 2587:
            wind_direction = "West"
        elif raw_value < 3037 and raw_value >= 2812:
            wind_direction = "West-northwest"    
        elif raw_value < 3262 and raw_value >= 3037:
            wind_direction = "Northwest"  
        elif raw_value < 3487 and raw_value >= 3262:
            wind_direction = "North-northwest"  
        elif raw_value < 3600 and raw_value >= 3487:
            wind_direction = "North"  
        else: break # to exit 
    #   wind_direction = instrument.read_register(0, 2)  # Register number, number of decimals
        print(f"Wind Direction: {wind_direction}")

    except IOError:
        print("Failed to read from instrument")
    except Exception as e:
        print(f"Error: {e}")
    
    #url = "https://weatherstation.wunderground.com/weatherstation/updateweatherstation.php?ID=IMOLLI25&PASSWORD=vdmVzZ6C&dateutc=now&winddir=360&action=updateraw"
    #response = requests.get(url)
    #print(f"Status: {response.status_code}, {response.text}")

    # create a string to hold the first part of the URL
    WUurl = "https://weatherstation.wunderground.com/weatherstation/updateweatherstation.php?"
    WU_station_id = "IMOLLI25" # PWS ID
    WU_station_pwd = "vdmVzZ6C" # Key
    WUcreds = "ID=" + WU_station_id + "&PASSWORD="+ WU_station_pwd
    date_str = "&dateutc=now"
    action_str = "&action=updateraw"

    r= requests.get(
        WUurl +
        WUcreds +
        date_str +
        "&winddir=" + str(wind_direction_degree) + # send wind direction measurements in degrees
        action_str)
    #print("Received " + str(r.status_code) + " " + str(r.text))

    # Wait for 10 seconds before the next measurement
    time.sleep(10)



