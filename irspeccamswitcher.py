import irsdk
import time
from datetime import datetime
import configparser

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

VERSION = "0.01"
configfile = "irspeccamswitcher.cfg"
CONFIG = configparser.ConfigParser()
CONFIG.read(configfile)
CAMERAS = {}

# this is our State class, with some helpful variables
class State:
    ir_connected = False
    last_car_setup_tick = -1


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


def loop(carNum, last_epoch):

    ir.freeze_var_buffer_latest()
    switch_cam = 0
    epoch_time = int(time.time())
    if ir["DriverInfo"]:
        spec_on = ir["CamCarIdx"]
        pctspecon = ir["CarIdxLapDistPct"][spec_on] * 100

        driversindistance = 0
        for i in range(len(ir["CarIdxLapDistPct"])):
            if i != spec_on:
                if ir["CarIdxLapDistPct"][i] != -1:
                    pctdriver=(ir["CarIdxLapDistPct"][i] * 100) - pctspecon
                    #if pctdriver < 0:
                    #    pctdriver += 100
                    #print("   ", i, pctdriver)
                    if pctdriver < 0.5 and pctdriver > -0.2:
                        driversindistance += 1
                        switch_cam = 1
                    elif pctdriver > -0.5 and pctdriver <= -0.2:
                        driversindistance += 1
                        switch_cam = 2

        if epoch_time - last_epoch > 3:
            if switch_cam == 1 and driversindistance == 1:
                #print("1 Switch Cam to", carNum)
                #ir.cam_switch_num(carNum, 19, 0)
                ir.cam_switch_num(carNum, CAMERA_DICT["Far Chase"], 0)
            elif switch_cam == 2 and driversindistance == 1:
                #print("2 Switch Cam to", carNum)
                #ir.cam_switch_num(carNum, 2, 0)
                ir.cam_switch_num(carNum, CAMERA_DICT["Gearbox"], 0)
            elif switch_cam > 0 and driversindistance > 1:
                #ir.cam_switch_num(carNum, 16, 0)
                ir.cam_switch_num(carNum, CAMERA_DICT["Chopper"], 0)
            else:
                #print("e Switch Cam to", carNum)
                #ir.cam_switch_num(carNum, 10, 0)
                ir.cam_switch_num(carNum, CAMERA_DICT["TV1"], 0)
            return epoch_time

    return last_epoch


def findDriver(uid):
    if ir["DriverInfo"]:
        for i in range(len(ir["DriverInfo"]["Drivers"])):
            if ir["DriverInfo"]["Drivers"][i]["UserID"] == int(uid):
                print("+++ Number", ir["DriverInfo"]["Drivers"][i]["CarNumber"], "UID",
                      ir["DriverInfo"]["Drivers"][i]["UserID"], "==", uid, ", Driver", ir["DriverInfo"]["Drivers"][i]["UserName"])
                ir.cam_switch_num(ir["DriverInfo"]["Drivers"][i]["CarNumber"], 10, 0)
                return ir["DriverInfo"]["Drivers"][i]["CarNumber"]
            #else:
                #print("    Number", ir["DriverInfo"]["Drivers"][i]["CarNumber"], "UID", ir["DriverInfo"]["Drivers"][i]["UserID"], "!=", uid, ", Driver", ir["DriverInfo"]["Drivers"][i]["UserName"])

    print("Driver was not found!")
    return -1


def cameras():
    # datetime object containing current date and time
    now = datetime.now()
    curtimestamp = now.strftime("%y-%m-%d %H:%M:%S")

    cameras = ()
    if ir["CameraInfo"]:
        cameras = ir["CameraInfo"]["Groups"]
        for i in cameras:
            print(curtimestamp, "Name:", i["GroupName"], "GroupNum", i["GroupNum"])
            CAMERA_DICT[i["GroupName"]]=i["GroupNum"]


if __name__ == '__main__':
    print("Starting up irspeccamswitcher...")
    print("Version: ", VERSION)
    print("---------------------------------------------")
    print("Waiting...")
    print("---------------------------------------------")
    # initializing ir and state
    ir = irsdk.IRSDK()
    state = State()
    sessionNum = -1
    sessionName = "None"
    try:
        # who's interesting?
        druid=CONFIG["DRIVER"]["driverID"]

        # infinite loop
        read_cameras = 0
        carNum = -1
        camswitch_epoch = 1
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
                if ir["SessionNum"] != sessionNum:
                    sessionNum = ir["SessionNum"]
                    sessionName = ir["SessionInfo"]["Sessions"][sessionNum]["SessionName"]
                    print(curtimestamp, "Current Session is ", sessionName)
                    carNum=findDriver(druid)

                camswitch_epoch = loop(carNum, camswitch_epoch)
            # sleep for 1 second
            # maximum you can use is 1/60
            # cause iracing updates data with 60 fps
            time.sleep(10/60)
    except KeyboardInterrupt:
        # press ctrl+c to exit
        pass
