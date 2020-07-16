from pprint import pprint
# Modules for use with the Arduino/formatting.
import sys
import time
import serial

s = None
s2 = None
s3 = None

#Serial reading stuff
try:
    assign = {"TEMP":None,"GPS":None,"DISP":None}
    s = serial.Serial('/dev/ttyUSB0',9600)
    s2 = serial.Serial('/dev/ttyUSB1',9600)
    s3 = serial.Serial('/dev/ttyUSB2',9600)
except serial.serialutil.SerialException:
    #If the above devices fail, they're NoneType
    print("Not all devices are connected. Will attempt to continue anyways.")
except Exception as e:
    print(e)
    print("Check to make sure that all sensors are plugged in.")
    print("Unplug all connected devices, wait ten seconds, then replug only the sensors.")
    print("The program will exit in 30 seconds, or you can exit manually.")
    time.sleep(30)
    exit()

time.sleep(5)

def determine_ports():
    print("Attempting to (re)assign ports...")
    if s != None:
        while True:
            c = str(s.read_until()).split("|")
            if len(c) < 2:
                continue
            if c[1] == "TEMP":
                assign["TEMP"] = "s"
                print("/USB0 = TEMP")
                break
            elif c[1] == "GPS":
                assign["GPS"] = "s"
                print("/USB0 = GPS")
                break
            elif c[1] == "DISP":
                assign["DISP"] = "s"
                print("/USB0 = DISP")
                break
    else:
        print("No device available at /USB0.")
    if s2 != None:
        while True:
            c = str(s2.read_until()).split("|")
            if len(c) < 2:
                continue
            if c[1] == "TEMP":
                assign["TEMP"] = "s2"
                print("/USB1 = TEMP")
                break
            elif c[1] == "GPS":
                assign["GPS"] = "s2"
                print("/USB1 = GPS")
                break
            elif c[1] == "DISP":
                assign["DISP"] = "s2"
                print("/USB1 = DISP")
                break
    else:
        print("No device available at /USB1.")
    if s3 != None:
        while True:
            c = str(s3.read_until()).split("|")
            if len(c) < 2:
                continue
            if c[1] == "TEMP":
                assign["TEMP"] = "s3"
                print("/USB2 = TEMP")
                break
            elif c[1] == "GPS":
                assign["GPS"] = "s3"
                print("/USB2 = GPS")
                break
            elif c[1] == "DISP":
                assign["DISP"] = "s3"
                print("/USB2 = DISP")
                break
    else:
        print("No device available at /USB2.")
        
determine_ports()
time.sleep(40)      
#time.sleep(5) #Wait for serial to initialize, should only be necessary if writing, not reading

submitlist = [] #main list for submission
cachelist = [] #in the event internet connection is lost, this is used instead

#function for uploading data
def submit_list():
    value_range_body = {
        'values': submitlist
    }

    request = service.spreadsheets().values().append(spreadsheetId=SPREADSHEET_ID, range=append_range, valueInputOption=value_input_option, insertDataOption=insert_data_option, body=value_range_body)
    response = request.execute()

    pprint(response)
    
def upload_main(): #Writes to both local DB and GSheets.
    global submitlist
    while True:
        base_list = []
        temp_data = eval("str(%s.read_until())"%assign["TEMP"])
        gyro_data = eval("str(%s.read_until())"%assign["GYRO"])
        gps_data = eval("str(%s.read_until())"%assign["GPS"])
        temp_parsed = temp_data.split("|")
        gyro_parsed = gyro_data.split("|")
        gps_parched = gps_data.split("|")
        base_list.append(int(time.time()))
        for i in range(2,4):
            base_list.append(temp_parsed[i])
        for i in range(2,8):
            base_list.append(gyro_parsed[i])
        if gps_parched[2] == "NO_ENCODE":
            for i in range (2,7):
                base_list.append("NO_ENCODE")
        else:
            for i in range (2,7):
                base_list.append(gps_parched[i])
        submitlist.append(base_list)
        if len(submitlist) > 5:
            try:
                submit_list()
            except:
                print("Something went wrong connecting to Google Sheets, forcing fallback")
                upload_fallback()
                break
            #SQL commits are only made at the same time Google Sheets performs an action.
            c.executemany("INSERT INTO Data VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", submitlist)
            conn.commit()
            submitlist = []

def upload_fallback(): #Writes to only local DB.
    global submitlist
    global cachelist
    while True:
        base_list = []
        temp_data = eval("str(%s.read_until())"%assign["TEMP"])
        gyro_data = eval("str(%s.read_until())"%assign["GYRO"])
        gps_data = eval("str(%s.read_until())"%assign["GPS"])
        temp_parsed = temp_data.split("|")
        gyro_parsed = gyro_data.split("|")
        gps_parched = gps_data.split("|")
        base_list.append(int(time.time()))
        for i in range(2,4):
            base_list.append(temp_parsed[i])
        for i in range(2,8):
            base_list.append(gyro_parsed[i])
        if gps_parched[2] == "NO_ENCODE":
            for i in range (2,7):
                base_list.append("NO_ENCODE")
        else:
            for i in range (2,7):
                base_list.append(gps_parched[i])
        submitlist.append(base_list)
        cachelist.append(base_list)
        if len(cachelist) > 5:
            try:
                submit_list()
                submitlist = []
                upload_main()
                print("Reestablished connection, using standard loop instead")
                break
            except:
                pass
            c.executemany("INSERT INTO Data VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", cachelist)
            conn.commit()
            cachelist = []

def go():
    determine_ports()
    upload_main()
    
go()
