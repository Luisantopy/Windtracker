# initial module import
import minimalmodbus
import time
import requests

# Initialize the instrument (Modbus RTU device)
instrument = minimalmodbus.Instrument('/dev/ttyUSB0', 2)  # port name, slave address

# Configure Modbus communication parameters
instrument.serial.baudrate = 9600        # Baud rate
instrument.serial.bytesize = 8           # Number of data bits
instrument.serial.parity = minimalmodbus.serial.PARITY_NONE  # Parity (None, Even, Odd)
instrument.serial.stopbits = 1           # Stop bits
instrument.serial.timeout = 1            # Timeout in seconds (adjust if necessary)

# Set mode to RTU (which is typical for RS485)
instrument.mode = minimalmodbus.MODE_RTU


# Scan multiple registers to find where the wind speed is stored
# - this is not relevant for measuring, only for setting up the .read_register below

for register in range(1): 
    try:
        value = instrument.read_register(register, 0)  # Register number, 0 decimals
        print(f"Register {register}: {value}")
    except IOError:
        print(f"Failed to read register {register}")
    except Exception as e:
        print(f"Error: {e}")


# Now try to read the register
while True: # Read until manually stopped
    try:
        # Read raw integer value (make sure it's interpreted as an integer, not a float)
        raw_value = instrument.read_register(0, 0, signed=False)  # Unsigned integer (0 decimals)
        #print(f"Raw Value (Integer): {raw_value}")
    
        wind_speed = instrument.read_register(0, 1)  # Register number, number of decimals
        wind_speed_mph = wind_speed * 2.23694
        print(f"Wind Speed: {wind_speed} ms, {wind_speed_mph} mph")
    except IOError:
        print("Failed to read from instrument")
    except Exception as e:
        print(f"Error: {e}")
    
    # create a string to hold the first part of the URL
    WUurl = "https://weatherstation.wunderground.com/weatherstation/updateweatherstation.php?"
    WU_station_id = "IMOLLI25" # PWS ID
    WU_station_pwd = "vdmVzZ6C" # Key
    WUcreds = "ID=" + WU_station_id + "&PASSWORD="+ WU_station_pwd
    date_str = "&dateutc=now"
    action_str = "&action=updateraw"

    # set up get request to send data wo weather underground
    r= requests.get(
        WUurl +
        WUcreds +
        date_str +
        "&windspeedmph=" + str(wind_speed_mph) + # send wind speed measurements in mph
        action_str)
    # print("Received " + str(r.status_code) + " " + str(r.text))

    # Wait for 2 seconds before the next measurement
    time.sleep(2)