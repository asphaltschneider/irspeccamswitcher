import irsdk
import time
from datetime import datetime
import configparser

# GroupName | GroupNum
# Nose | 1          Interesting
# Gearbox | 2       Interesting
# Roll Bar | 3
# LF Susp | 4
# LR Susp | 5
# Gyro | 6          Interesting
# RF Susp | 7
# RR Susp | 8
# Cockpit |

VERSION = "0.01"
configfile = "irspeccamswitcher.cfg"
CONFIG = configparser.ConfigParser()
CONFIG.read(configfile)

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


def loop():

    ir.freeze_var_buffer_latest()
    secondcar = 32
    switch_cam = 0
    if ir["DriverInfo"]:
        spec_on = ir["CamCarIdx"]
        #print("cam is on", spec_on)
        # print(secondcar, ir["CarIdxEstTime"][secondcar])
        # print(spec_on, ir["CarIdxEstTime"][spec_on])
        # print("estimated", ir["DriverInfo"]["DriverCarEstLapTime"])
        # print("half minus=", (-0.5 * ir["DriverInfo"]["DriverCarEstLapTime"]))
        # print("half plus =", (0.5 * ir["DriverInfo"]["DriverCarEstLapTime"]))
        # reltime = ir["CarIdxEstTime"][secondcar] - ir["CarIdxEstTime"][spec_on]
        #
        # print("initial reltime", reltime)
        # while reltime < (-0.5 * ir["DriverInfo"]["DriverCarEstLapTime"]):
        #     reltime += ir["DriverInfo"]["DriverCarEstLapTime"]
        # while reltime > (0.5 * ir["DriverInfo"]["DriverCarEstLapTime"]):
        #     reltime -= ir["DriverInfo"]["DriverCarEstLapTime"]
        # while reltime < 0:
        #     reltime += ir["DriverInfo"]["DriverCarEstLapTime"]
        # # if i > len(ir["DriverInfo"]["Drivers"]) / 2:
        # while reltime > 0:
        #     reltime -= ir["DriverInfo"]["DriverCarEstLapTime"]
        # print(reltime)
        pctspecon = ir["CarIdxLapDistPct"][spec_on] * 100

        for i in range(len(ir["CarIdxLapDistPct"])):
            if i != spec_on:
                if ir["CarIdxLapDistPct"][i] != -1:
                    pctdriver=(ir["CarIdxLapDistPct"][i] * 100) - pctspecon
                    #if pctdriver < 0:
                    #    pctdriver += 100
                    #print("   ", i, pctdriver)
                    if pctdriver < 1 and pctdriver > -0.2:
                        switch_cam = 1
                    elif pctdriver > -1 and pctdriver <= -0.2:
                        switch_cam = 2

            #elif i == spec_on:
            #    print("+++", i, 0)

        if switch_cam == 1:
            ir.cam_switch_num(2, 19, 0)
        elif switch_cam == 2:
            ir.cam_switch_num(2, 2, 0)
        else:
            ir.cam_switch_num(2, 10, 0)


    #print("-------------------------------------------------------------")
    #time.sleep(1)



def findDriver(uid):
    if ir["DriverInfo"]:
        for i in range(len(ir["DriverInfo"]["Drivers"])):
            if ir["DriverInfo"]["Drivers"][i]["UserID"] == int(uid):
                #print("+++ Number", ir["DriverInfo"]["Drivers"][i]["CarNumber"], "UID",
                #      ir["DriverInfo"]["Drivers"][i]["UserID"], "==", uid, ", Driver", ir["DriverInfo"]["Drivers"][i]["UserName"])
                return ir["DriverInfo"]["Drivers"][i]["CarNumber"]
            else:
                #print("    Number", ir["DriverInfo"]["Drivers"][i]["CarNumber"], "UID", ir["DriverInfo"]["Drivers"][i]["UserID"], "!=", uid, ", Driver", ir["DriverInfo"]["Drivers"][i]["UserName"])
                ir.cam_switch_num(2,10,0)
    return "none"

def cameras():
    # datetime object containing current date and time
    now = datetime.now()
    curtimestamp = now.strftime("%y-%m-%d %H:%M:%S")

    cameras = ()
    if ir["CameraInfo"]:
        cameras = ir["CameraInfo"]["Groups"]
        for i in cameras:
            print(curtimestamp, "Name:", i["GroupName"], "GroupNum", i["GroupNum"])


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
        while True:
            # check if we are connected to iracing
            check_iracing()
            # if we are, then process data
            if state.ir_connected:
                # identify the current session, the driver is in
                now = datetime.now()
                curtimestamp = now.strftime("%y-%m-%d %H:%M:%S")

                if read_cameras == 0:
                    cameras()

                    read_cameras = 1
                idx=-1
                # print some session infos
                if ir["SessionNum"] != sessionNum:
                    sessionNum = ir["SessionNum"]
                    sessionName = ir["SessionInfo"]["Sessions"][sessionNum]["SessionName"]
                    print(curtimestamp, "Current Session is ", sessionName)
                    idx=findDriver(druid)

                loop()
            # sleep for 1 second
            # maximum you can use is 1/60
            # cause iracing updates data with 60 fps
            time.sleep(10/60)
    except KeyboardInterrupt:
        # press ctrl+c to exit
        pass
