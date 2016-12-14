#!/usr/bin/env python
import cv2
import rospy
import rospkg
from datetime import datetime
from sensor_msgs.msg import Image
from laser_clustering.msg import ClustersMsg
from cv_bridge import CvBridge, CvBridgeError
from laser_analysis.msg import Analysis4MetersMsg

input_clusters_topic = ""
someone_passing = False
image_subscriber = None
bridge = CvBridge()
analysis_topic = ""
subscribed = False
last_callback = 0
image_buffer = []
time_buffer = []
image_topic = ""
img_path = ""


def image_callback(msg):
    global last_callback, image_buffer, time_buffer, someone_passing
    if someone_passing:
        dt = datetime.now()
        now = dt.minute*60000000 + dt.second*1000000 + dt.microsecond
        if now - last_callback > 10000000:
            image_buffer = []
            time_buffer = []
            print 'Cleared image buffer due to late callback'
        last_callback = now
        try:
            cv2_img = bridge.imgmsg_to_cv2(msg, "bgr8")
            image_buffer.append(cv2_img)
            time_buffer.append(last_callback)
            print 'Got a new image!' + str(now)
        except CvBridgeError, e:
            print(e)

def clusters_callback(msg):
    global image_topic, image_subscriber, subscribed, someone_passing
    if len(msg.x) > 0:
        if not subscribed:
            print 'Enabling image subscriber'
            image_subscriber = rospy.Subscriber(image_topic, Image, image_callback)
            subscribed = True
        someone_passing = True
    else:
        someone_passing = False

def analysis_callback(msg):
    global image_subscriber, image_buffer, time_buffer, img_path, subscribed
    print 'Disabling image subscriber'
    image_subscriber.unregister()
    subscribed = False
    image_buffer_ = list(image_buffer)
    image_buffer = []
    time_buffer_ = list(time_buffer)
    time_buffer = []
    print 'Cleared image buffer due to 4 meters event'
    for i in range(len(image_buffer_)):
        cv2.imwrite(img_path+"img_"+str(time_buffer_[i])+".jpeg", image_buffer_[i])


def main():
    global image_topic, analysis_topic, input_clusters_topic, img_path, rospack
    rospy.init_node('images_if_4_meters')
    rospack = rospkg.RosPack()
    img_path = rospack.get_path('images_if_4_meters')+'/saved_images/'
    analysis_topic = rospy.get_param("~analysis_topic", "/laser_analysis/results4meters")
    input_clusters_topic = rospy.get_param("~input_clusters_topic", "/laser_overlap_trace/clusters")
    image_topic = rospy.get_param("~image_topic", "/xtion_pro_cam/rgb/image_raw")
    
    rospy.Subscriber(input_clusters_topic, ClustersMsg, clusters_callback)
    rospy.Subscriber(analysis_topic, Analysis4MetersMsg, analysis_callback)
    rospy.spin()

if __name__ == '__main__':
    main()