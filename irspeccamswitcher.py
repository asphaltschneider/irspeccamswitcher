import irsdk
import time
from datetime import datetime
import configparser
import re
import colorama
from colorama import Fore, Back, Style, Cursor
import pprint

# 20-12-27 23:42:04 Name: Nose GroupNum 1
# 20-12-27 23:42:04 Name: Gearbox GroupNum 2
# 20-12-27 23:42:04 Name: Roll Bar GroupNum 3
# 20-12-27 23:42:04 Name: LF Susp GroupNum 4
# 20-12-27 23:42:04 Name: LR Susp GroupNum 5
# 20-12-27 23:42:04 Name: Gyro GroupNum 6
# 20-12-27 23:42:04 Name: RF Susp GroupNum 7
# 20-12-27 23:42:04 Name: RR Susp GroupNum 8
# 20-12-27 23:42:04 Name: Cockpit GroupNum 9
# 20-12-27 23:42:04 Name: TV1 GroupNum 10
# 20-12-27 23:42:04 Name: TV2 GroupNum 11
# 20-12-27 23:42:04 Name: TV3 GroupNum 12
# 20-12-27 23:42:04 Name: Scenic GroupNum 13
# 20-12-27 23:42:04 Name: Pit Lane GroupNum 14
# 20-12-27 23:42:04 Name: Pit Lane 2 GroupNum 15
# 20-12-27 23:42:04 Name: Chopper GroupNum 16
# 20-12-27 23:42:04 Name: Blimp GroupNum 17
# 20-12-27 23:42:04 Name: Chase GroupNum 18
# 20-12-27 23:42:04 Name: Far Chase GroupNum 19
# 20-12-27 23:42:04 Name: Rear Chase GroupNum 20

VERSION = "0.03"
configfile = "irspeccamswitcher.cfg"
CONFIG = configparser.ConfigParser()
CONFIG.read(configfile)
CAMERAS = {}
SESSIONID = -1
SESSIONNAME = 'None'
DRIVER_DICT = {}
DRIVER_LIST = []
DRIVERTOSPECID = -1
DRIVERTOSPECNUMBER = -1

# this is our State class, with some helpful variables
class State:
    ir_connected = False
    last_car_setup_tick = -1
    global CAMERAS
    global SESSIONID
    global SESSIONNAME
    global DRIVER_DICT
    global DRIVER_LIST
    global DRIVERTOSPECID
    global DRIVERTOSPECNUMBER



# here we check if we are connected to iracing
# so we can retrieve some data
def check_iracing():
    if state.ir_connected and not (ir.is_initialized and ir.is_connected):
        state.ir_connected = False
        # don't forget to reset your State variables
        state.last_car_setup_tick = -1
        # we are shutting down ir library (clearing all internal variables)
        ir.shutdown()
        print('irsdk disconnected')
    elif not state.ir_connected and ir.startup() and ir.is_initialized and ir.is_connected:
        state.ir_connected = True
        print('irsdk connected')
        curtime = datetime.now()
        curtimestamp = curtime.strftime("%y-%m-%d %H:%M:%S")
        if ir['WeekendInfo']:
            print(curtimestamp, "The next events Category:", ir['WeekendInfo']['Category'])
            print(curtimestamp, "Track:", ir['WeekendInfo']['TrackDisplayName'], ",", ir['WeekendInfo']['TrackCity'],
                  ",", ir['WeekendInfo']['TrackCountry'])
            if ir['WeekendInfo']['WeekendOptions']['StandingStart'] == 1:
                standingstart = "standing"
            else:
                standingstart = "rolling"
            print(curtimestamp, "Start type is", standingstart, "start")
            #fillDriverDict()


def loop(carNum, last_epoch, prev_epoch, prev_pctspecon, DRIVERTOSPECNUMBER, SESSIONNAME, DRIVERTOSPECID):
    # calculate speed from prev vs current position

    ir.freeze_var_buffer_latest()
    switch_cam = 0
    switch_cam_number = '0'
    epoch_time = time.time()
    if ir["DriverInfo"]:
        spec_on = DRIVERTOSPECID
        pctspecon = ir["CarIdxLapDistPct"][DRIVERTOSPECID]
        #print("tracklength", ir["WeekendInfo"]["TrackLength"])
        tracklength = ir["WeekendInfo"]["TrackLength"]
        try:
            tracklength_km = re.search('([\d\.]+?)\ km.*$', tracklength).group(1)
        except AttributeError:
            tracklength_km = ''
        tracklength_m = float(tracklength_km) * 1000
        #print("tracklength", tracklength_m)
        cur_pctspecon = pctspecon
        if prev_pctspecon > 0.8 and cur_pctspecon < 0.2:
            cur_pctspecon += 1
            #print("over the line")
        cur_m_specon = tracklength_m * cur_pctspecon
        prev_m_specon = tracklength_m * prev_pctspecon
        diff_m_specon = cur_m_specon - prev_m_specon
        diff_epoch = epoch_time - prev_epoch
        calc_speed = diff_m_specon / diff_epoch
        calc_speed_kmh = int((calc_speed * 3600) / 1000)
        #print(f"\033[2J")
        #print("\r", Fore.RED, "travelled", diff_m_specon, "meters in", diff_epoch, "seconds - speed", calc_speed_kmh, "km/h", end="")


        # Method 1: Easy but not very precise way to calculate gaps
        # * Calculate distance fraction between 2 cars by substracting their CarIdxLapDistPct
        # * Multiply by track length to get distance in m
        # * Divide by speed to get time gap
        DRIVER_LIST = []
        driversindistance = 0
        for i in range(len(ir["CarIdxLapDistPct"])):
            #print("i=%i" % (i))
            if i != int(DRIVERTOSPECID) and i != 0:
                if ir["CarIdxLapDistPct"][i] != -1:
                    try:
                        pctdriver=(ir["CarIdxLapDistPct"][i] - pctspecon) * tracklength_m / calc_speed
                    except ZeroDivisionError:
                        pctdriver = (ir["CarIdxLapDistPct"][i] - pctspecon) * tracklength_m / 0.1
                    #if pctdriver < 0:
                    #    pctdriver += 100
                    #print("   ", i, pctdriver)
                    #print("Number", ir["DriverInfo"]["Drivers"][i]["CarNumber"], "UID",
                    #      ir["DriverInfo"]["Drivers"][i]["UserID"], ", Driver",
                    #      ir["DriverInfo"]["Drivers"][i]["UserName"])
                    if pctdriver <= (tracklength_m + 15):
                        tmpDict = {}
                        tmpDict["ID"] = i
                        tmpDict["DriverName"] = ir["DriverInfo"]["Drivers"][i]["UserName"]
                        tmpDict["UserID"] = ir["DriverInfo"]["Drivers"][i]["UserID"]
                        tmpDict["CarNumber"] = ir["DriverInfo"]["Drivers"][i]["CarNumber"]
                        tmpDict["Distance"] = pctdriver
                        DRIVER_LIST.append(tmpDict)
                    if pctdriver < 0.6 and pctdriver > -0.1:
                        if ir["DriverInfo"]["Drivers"][i]["CarNumber"] != DRIVERTOSPECNUMBER:
                            driversindistance += 1
                            switch_cam = 1
                            switch_cam_number = DRIVERTOSPECNUMBER
                            #print("opponent", ir["DriverInfo"]["Drivers"][i]["CarNumber"], "is infront     ", pctdriver, "driversindistance:", driversindistance)
                    elif pctdriver > -0.4 and pctdriver <= -0.1:
                        driversindistance += 1
                        switch_cam = 2
                        switch_cam_number = ir["DriverInfo"]["Drivers"][i]["CarNumber"]
                        #rint("opponent", switch_cam_number, "is close behind", pctdriver, "driversindistance:", driversindistance)
            elif ir["DriverInfo"]["Drivers"][i]["CarNumber"] != DRIVERTOSPECNUMBER:
                if ir["DriverInfo"]["Drivers"][i]["CarNumber"] != "0":
                    tmpDict = {}
                    tmpDict["ID"] = i
                    tmpDict["DriverName"] = ir["DriverInfo"]["Drivers"][i]["UserName"]
                    tmpDict["UserID"] = ir["DriverInfo"]["Drivers"][i]["UserID"]
                    tmpDict["CarNumber"] = ir["DriverInfo"]["Drivers"][i]["CarNumber"]
                    tmpDict["Distance"] = 0
                    DRIVER_LIST.append(tmpDict)

        #pp = pprint.PrettyPrinter(indent=2)
        #pp.pprint(DRIVER_LIST)

        relative_dict = sorted(DRIVER_LIST, key=lambda x: x['Distance'], reverse=True)

        #for i in relative_dict:
        #    print("#%s - %s\t - %.2f" % (i["CarNumber"], i["DriverName"], i["Distance"]))
        #print("-----------------------------")
        #pp.pprint(relative_dict[])

        if SESSIONNAME != 'QUALIFY':
            if epoch_time - last_epoch > 5:
                if switch_cam == 1 and driversindistance == 1:
                    #print("1,1 Switch Cam to", DRIVERTOSPECNUMBER, "Chase")
                    #ir.cam_switch_num(carNum, 19, 0)
                    ir.cam_switch_num(DRIVERTOSPECNUMBER, CAMERA_DICT["Chase"], 0)
                elif switch_cam == 2 and driversindistance == 1:
                    #print("2,1 Switch Cam to", switch_cam_number, "Gyro")
                    #ir.cam_switch_num(carNum, 2, 0)
                    ir.cam_switch_num(switch_cam_number, CAMERA_DICT["Gyro"], 0)
                elif switch_cam > 0 and driversindistance > 1:
                    #print(">0,>1 Switch Cam to", DRIVERTOSPECNUMBER, "Far Chase")
                    #ir.cam_switch_num(carNum, 16, 0)
                    ir.cam_switch_num(DRIVERTOSPECNUMBER, CAMERA_DICT["Far Chase"], 0)
                else:
                    #print("e Switch Cam to", DRIVERTOSPECNUMBER, "TV1")
                    #ir.cam_switch_num(carNum, 10, 0)
                    ir.cam_switch_num(DRIVERTOSPECNUMBER, CAMERA_DICT["TV1"], 0)
                return epoch_time, epoch_time, pctspecon, DRIVERTOSPECNUMBER, SESSIONNAME
        else:
            ir.cam_switch_num(DRIVERTOSPECNUMBER, CAMERA_DICT["Chase"], 0)
            return epoch_time, epoch_time, pctspecon, DRIVERTOSPECNUMBER, SESSIONNAME

    return last_epoch, epoch_time, pctspecon, DRIVERTOSPECNUMBER, SESSIONNAME


def findDriver(uid):
    found_driver = 0
    if ir["DriverInfo"]:
        for i in range(len(ir["DriverInfo"]["Drivers"])):
            if ir["DriverInfo"]["Drivers"][i]["UserID"] == int(uid):
                ir.cam_switch_num(ir["DriverInfo"]["Drivers"][i]["CarNumber"], CAMERA_DICT["Rear Chase"], 0)
                found_driver = 1
                DRIVERTOSPECNUMBER = ir["DriverInfo"]["Drivers"][i]["CarNumber"]
                DRIVERTOSPECID = i
                curtime = datetime.now()
                curtimestamp = curtime.strftime("%y-%m-%d %H:%M:%S")
                print(curtimestamp, "spotting Driver #%s - %s" % (DRIVERTOSPECNUMBER, ir["DriverInfo"]["Drivers"][i]["UserName"]))
                return ir["DriverInfo"]["Drivers"][i]["CarNumber"], DRIVERTOSPECID

    if found_driver == 0:
        print("Driver was not found! Please add your desired driver uid to irspeccamswitcher.cfg")
        print("---------------------------------------------------------------------------------")
        print("Starting field:")
        for i in range(len(ir["DriverInfo"]["Drivers"])):
            print("Number", ir["DriverInfo"]["Drivers"][i]["CarNumber"], "UID",
                  ir["DriverInfo"]["Drivers"][i]["UserID"], ", Driver",
                  ir["DriverInfo"]["Drivers"][i]["UserName"])
        input("Press any key to exit")
    return -1, -1

def fillDriverDict():
    if ir["DriverInfo"]:
        DRIVER_DICT = {}
        print("Reading the drivers")
        for i in range(len(ir["DriverInfo"]["Drivers"])):
            tmpDict = {}
            tmpDict["UserName"] = ir["DriverInfo"]["Drivers"][i]["UserName"]
            tmpDict["CarNumber"]= ir["DriverInfo"]["Drivers"][i]["CarNumber"]
            tmpDict["UserID"] = ir["DriverInfo"]["Drivers"][i]["UserID"]
            DRIVER_DICT[i] = {}
            DRIVER_DICT[i] = tmpDict
        pp = pprint.PrettyPrinter(indent=2)
        pp.pprint(DRIVER_DICT)

def cameras():
    # datetime object containing current date and time
    now = datetime.now()
    curtimestamp = now.strftime("%y-%m-%d %H:%M:%S")

    cameras = ()
    if ir["CameraInfo"]:
        cameras = ir["CameraInfo"]["Groups"]
        for i in cameras:
            #print(curtimestamp, "Name:", i["GroupName"], "GroupNum", i["GroupNum"])
            CAMERA_DICT[i["GroupName"]]=i["GroupNum"]


if __name__ == '__main__':

    colorama.init()
    print("Starting up irspeccamswitcher...")
    print("Version: ", VERSION)
    print("---------------------------------------------")
    print("Waiting...")
    print("---------------------------------------------")
    # initializing ir and state
    ir = irsdk.IRSDK()
    state = State()
    sessionNum = -1
    SESSIONNAME = "None"
    try:
        # who's interesting?
        druid=CONFIG["DRIVER"]["driverID"]

        # infinite loop
        read_cameras = 0
        carNum = -1
        camswitch_epoch = 1
        previous_epoch = 1
        previous_pctspecon = 0
        while True:
            # check if we are connected to iracing
            check_iracing()
            # if we are, then process data
            if state.ir_connected:
                # identify the current session, the driver is in
                now = datetime.now()
                curtimestamp = now.strftime("%y-%m-%d %H:%M:%S")

                if read_cameras == 0:
                    CAMERA_DICT={}
                    cameras()
                    read_cameras = 1

                # print some session infos
                if ir["SessionNum"] != sessionNum or SESSIONID != ir["SessionID"]:
                    SESSIONID = ir["SessionID"]
                    sessionNum = ir["SessionNum"]
                    SESSIONNAME = ir["SessionInfo"]["Sessions"][sessionNum]["SessionName"]
                    print(curtimestamp, "Current Session is ", SESSIONNAME)
                    #fillDriverDict()
                    DRIVERTOSPECNUMBER, DRIVERTOSPECID = findDriver(druid)
                    read_cameras
                    if(DRIVERTOSPECNUMBER == -1):
                        exit(0)

                camswitch_epoch, previous_epoch, previous_pctspecon, DRIVERTOSPECNUMBER, SESSIONNAME = loop(carNum, camswitch_epoch, previous_epoch, previous_pctspecon, DRIVERTOSPECNUMBER, SESSIONNAME, DRIVERTOSPECID)
            # sleep for 1 second
            # maximum you can use is 1/60
            # cause iracing updates data with 60 fps
            #time.sleep(1)
            time.sleep(10/60)
    except KeyboardInterrupt:
        # press ctrl+c to exit
        pass
