import irsdk
import time
from datetime import datetime

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

                # print some session infos
                if ir["SessionNum"] != sessionNum:
                    sessionNum = ir["SessionNum"]
                    sessionName = ir["SessionInfo"]["Sessions"][sessionNum]["SessionName"]
                    print(curtimestamp, "Current Session is ", sessionName)

                loop()
            # sleep for 1 second
            # maximum you can use is 1/60
            # cause iracing updates data with 60 fps
            time.sleep(10/60)
    except KeyboardInterrupt:
        # press ctrl+c to exit
        pass
