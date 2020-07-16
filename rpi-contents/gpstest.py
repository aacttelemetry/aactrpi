import serial
import time

#because this test only implements the GPS sensor, there is no need to determine baud rates and ports
try:
    serial_1 = serial.Serial('/dev/ttyUSB0',9600) 
    assign = {"TEMP":"","GPS":"","GYRO":""}
except Exception as e:
    print(e)
    print("Check to make sure that all sensors are plugged in.")
    print("Unplug all connected devices, wait ten seconds, then replug only the sensors.")
    print("The program will exit in 30 seconds, or you can exit manually.")
    time.sleep(30)
    exit()

while True:
    try:  
        while True:
            temp_data = str(serial_1.read_until())
            print(temp_data)
            temp_parsed = temp_data.split("|")
            print(temp_parsed)
            time.sleep(1)
    except Exception as e:
        print(e)
    # Close the connection with the client 