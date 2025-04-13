import cv2 
import numpy as np 
import time 
import pickle 
def nothing(x): 
  pass 
img2 = np.zeros((300,512,3), np.uint8) 
cv2.namedWindow('image') 
 
# create trackbars for color change 
cv2.createTrackbar('H_low','image',0,255,nothing) 
cv2.createTrackbar('H_high','image',255,255,nothing) 
cv2.createTrackbar('S_low','image',0,255,nothing) 
cv2.createTrackbar('S_high','image',255,255,nothing) 
cv2.createTrackbar('V_low','image',0,255,nothing) 
cv2.createTrackbar('V_high','image',255,255,nothing) 
 
imcap = cv2.VideoCapture('nvarguscamerasrc ! video/x-raw(memory:NVMM), width=640, height=480, format=(string)NV12, framerate=(fraction)30/1 ! nvvidconv ! video/x-raw, format=(string)BGRx ! videoconvert ! video/x-raw, format=(string)BGR ! appsink' , cv2.CAP_GSTREAMER) 

imcap.set(cv2.CAP_PROP_BRIGHTNESS, 60) 
imcap.set(3, 480) # set width as 640 
imcap.set(4, 360) # set height as 480 
kernal = np.ones((5,5)) 
while(1): 
  H_high = cv2.getTrackbarPos('H_high','image') 
  H_low = cv2.getTrackbarPos('H_low','image') 
  S_high = cv2.getTrackbarPos('S_high','image') 
  S_low = cv2.getTrackbarPos('S_low','image') 
  V_high = cv2.getTrackbarPos('V_high','image') 
  V_low = cv2.getTrackbarPos('V_low','image') 
  success, img = imcap.read() 
  hls = cv2.cvtColor(img, cv2.COLOR_BGR2HSV) 
  hls_low = np.array([H_low, S_low, V_low]) 
  hls_high = np.array([H_high, S_high, V_high]) 
   
  mask = cv2.inRange(hls, hls_low, hls_high) 
  mask = cv2.dilate(mask,kernal,iterations=1) 
  res = cv2.bitwise_and(img, img, mask=mask) 
     
  cv2.imshow('image',res) 
  if cv2.waitKey(30) & 0xFF == 27:  
    break 
cv2.destroyAllWindows() 