# Information: https://clover.coex.tech/programming

import math
import rospy
import cv2
from clover import srv
from std_srvs.srv import Trigger
from clover.srv import SetLEDEffect
from sensor_msgs.msg import Range
from pyzbar import pyzbar
from pyzbar.pyzbar import ZBarSymbol
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from clover import long_callback

rospy.init_node('flight')
bridge = CvBridge()

get_telemetry = rospy.ServiceProxy('get_telemetry', srv.GetTelemetry)
navigate = rospy.ServiceProxy('navigate', srv.Navigate)
navigate_global = rospy.ServiceProxy('navigate_global', srv.NavigateGlobal)
set_position = rospy.ServiceProxy('set_position', srv.SetPosition)
set_velocity = rospy.ServiceProxy('set_velocity', srv.SetVelocity)
set_attitude = rospy.ServiceProxy('set_attitude', srv.SetAttitude)
set_rates = rospy.ServiceProxy('set_rates', srv.SetRates)
land = rospy.ServiceProxy('land', Trigger)
set_effect = rospy.ServiceProxy('led/set_effect', SetLEDEffect)  # define proxy to ROS-service

telem = get_telemetry()

print('Battery: {}'.format(telem.voltage))
print('Connected: {}'.format(telem.connected))

def navigate_wait(x=0, y=0, z=1.5, yaw=float('nan'), speed=0.5, frame_id='aruco_map', auto_arm=False, tolerance=0.2):
    navigate(x=x, y=y, z=z, yaw=yaw, speed=speed, frame_id=frame_id, auto_arm=auto_arm)

    while not rospy.is_shutdown():
        telem = get_telemetry(frame_id='navigate_target')
        if math.sqrt(telem.x ** 2 + telem.y ** 2 + telem.z ** 2) < tolerance:
            break
        rospy.sleep(0.2)

def range_callback(msg):
    global h
    # Process data from the rangefinder
    h = msg.range


def range_callback(msg):
    global h
    h = msg.range

rospy.Subscriber('rangefinder/range', Range, range_callback)

@long_callback
def image_callback(msg):
    img = bridge.imgmsg_to_cv2(msg, 'bgr8')
    barcodes = pyzbar.decode(img, [ZBarSymbol.QRCODE])
    for barcode in barcodes:
        b_data = barcode.data.decode('utf-8')
        b_type = barcode.type
        (x, y, w, h) = barcode.rect
        xc = x + w/2
        yc = y + h/2
        print('Found {} with data {} with center at x={}, y={}'.format(b_type, b_data, xc, yc))

image_sub = rospy.Subscriber('main_camera/image_raw_throttled', Image, image_callback, queue_size=1)


print('Take off and hover 1 m above the ground')
navigate(x=0, y=0, z=1, frame_id='body', auto_arm=True)
navigate(x=0, y=0, z=1, frame_id='aruco_map', auto_arm=True)
print(get_telemetry())
print(h)

navigate_wait(x=1, y=0.5)
set_effect(r=255, g=255, b=255)
print(get_telemetry())
print(h)

navigate_wait(x=2.5, y=1)
set_effect(r=0, g=255, b=0)
print(get_telemetry())
print(h)
 
navigate_wait(x=2.5, y=2.5)
set_effect(r=0, g=255, b=0)

navigate_wait(x=1, y=2.5)
set_effect(r=0, g=255, b=0)
print(get_telemetry())

navigate_wait(x=0.5, y=0.5)
set_effect(r=0, g=255, b=0)
print(get_telemetry())
print(h)

report_team = "report.txt"
with open(report_team, 'w') as f:
    f.write(get_telemetry(),h)


print(f"Report generated: {report_team}")

rospy.sleep(5)

while True:
    try:
        print('type "range" for current range')
        print('type "land" to land')
        str = input()
        if str == 'range':
            print('Rangefinder distance: {}'.format(h))
            continue

        if str == 'land':
            break

        parts = str.split(',')
        if len(parts) != 3:
            print('You have made a wrong input. Please try again')
            continue

        x = int(parts[0])
        y = int(parts[1])
        z = int(parts[2])

        print('I am going to point (X:{},Y:{},Z:{})'.format(x, y, z))

        navigate(x=x, y=y, z=z, frame_id='aruco_map')
        rospy.sleep(5)
        print('Done!')

    except:
        print('Something went wrong')

print('Perform landing')
land()