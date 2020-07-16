'''Consider using async in the future so blocking from god knows what doesn't make the whole thing run slowly and fall out of sync
'''

# Modules for use with Google Sheets.
from __future__ import print_function
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
from pprint import pprint

# Modules for use with the Arduino/formatting.
import sys
import serial
import time
import sqlite3 #The table should be pre-created. Base it off of the "test.db" file using the SQLite browser.

# Setup the Sheets API (don't touch any of these!)
SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
store = file.Storage('credentials.json')
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
    creds = tools.run_flow(flow, store)
service = build('sheets', 'v4', http=creds.authorize(Http()))

# Target spreadsheet ID; easily found by looking at the URL of the gsheet
SPREADSHEET_ID = '1K_3HoLemrF0fYTmdT47LxnZcyGHhU7nC4pLsQebIU0s'

# Used with spreadsheets.values.append
value_input_option = 'USER_ENTERED' # RAW/USER_ENTERED; raw = raw values, user_entered = as if entered by hand (i.e. formulas will work in this mode, will fail in RAW)
insert_data_option = 'INSERT_ROWS' # OVERWRITE/INSERT_ROWS; overwrite = overwrite, insert_rows = append
# target sheet and range; multiple ranges can be done by creating new append_ranges and using a conditional in the append function
append_range = 'Data!A2:C2' # where to either start appending or overwriting data

# Set up stuff for sqlite3 (multiple cursors can technically be made)
conn = sqlite3.connect('live.db')
c = conn.cursor()

# Serial reading stuff
try:
    s = serial.Serial('/dev/ttyUSB0',9600)
    s2 = serial.Serial('/dev/ttyUSB1',9600)
    s3 = serial.Serial('/dev/ttyUSB2',9600)
    assign = {"TEMP":"","GPS":"","GYRO":""}
    #perhaps use this and x = eval() statements for parsing?
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
    global s
    global s2
    global s3
    gyro_found = False
    a = str(s.read(15))
    if "|" not in a:
        assign["GYRO"] = "s"
        print("/USB0 = GYRO")
        gyro_found = True
        s.close()
        s = serial.Serial('/dev/ttyUSB0',115200)
    else:
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
    b = str(s2.read(15))
    if not gyro_found:
        if "|" not in b:
            assign["GYRO"] = "s2"
            print("/USB1 = GYRO")
            gyro_found = True
            s2.close()
            s2 = serial.Serial('/dev/ttyUSB1',115200)
        else:
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
    e = str(s3.read(15))
    if not gyro_found:
        assign["GYRO"] = "s3"
        print("/USB2 = GYRO")
        s3.close()
        s3 = serial.Serial('/dev/ttyUSB2',115200)
    else:
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
        
#time.sleep(5) #Wait for serial to initialize, should only be necessary if writing, not reading

submitlist = [] #main list for submission

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
            submit_list()
            submitlist = []
            #SQL commits are only made at the same time Google Sheets performs an action.
            converted = tuple(base_list)
            c.execute("INSERT INTO Data VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", converted)
            conn.commit()
            
def upload_fallback(): #Writes to only local DB.
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
            submitlist = []
            converted = tuple(base_list)
            c.execute("INSERT INTO Data VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", converted)
            conn.commit() 

def go():
    determine_ports()
    upload_main()
    
go()
