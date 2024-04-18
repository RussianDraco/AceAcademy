import math, cv2, pyautogui
import mediapipe as mp
import numpy as np


full_hand_tracking = True
camera_width, camera_height = 640, 480


caption = cv2.VideoCapture(1)
caption.set(3, camera_width)
caption.set(4, camera_height)
while True:
    success, img = caption.read()

    cv2.imshow("Face_Cam", img)
            