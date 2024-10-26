import serial 
import minimalmodbus
import time

ser = serial.Serial("/dev/ttyUSB1")
print(ser.name)
ser.write(b"hello")
ser.close()

# port name, slave address (in decimal)
instrument = minimalmodbus.Instrument('/dev/ttyUSB1', 1)

instrument.serial.baudrate = 9600      
instrument.serial.bytesize = 8
instrument.serial.stopbits = 1
instrument.serial.timeout  = 1          
instrument.mode = minimalmodbus.MODE_RTU  
instrument.clear_buffers_before_each_transaction = True
instrument.debug = True

while True:
    # Register number, number of decimals, function code
    # not sure what to expect on number of register, is it 31004, 31005?
    
    digit_count = instrument.read_register(255)
    print(digit_count)
    time.sleep(1) 

ser = serial.Serial()
ser.baudrate = 9600
ser.port = "/dev/ttyUSB1"
ser
ser.open()
ser.is_open
ser.close()
ser.is_open

instrument = minimalmodbus.Instrument('/dev/ttyUSB1', 1)  # port name, slave address (in decimal)
wind_direction = instrument.read_register(255)  # Registernumber, number of decimals
print(wind_direction)
