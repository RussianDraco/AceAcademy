import cv2
import numpy as np
import pyautogui
import time
import mediapipe as mp





class HandDetector:

    def __init__(self, mode=False, maxHands=2, detectionCon=0.5, trackCon=0.5):

        self.mode = mode
        self.maxHands = maxHands
        self.detectionCon = detectionCon
        self.trackCon = trackCon

        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands()
        self.mpDraw = mp.solutions.drawing_utils
        
        self.tipIds = [4, 8, 12, 16, 20]
   

    def analyse(self, frame):
        self.imgRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(self.imgRGB)

    def detection(self, frame, draw=True):
        
        if self.results.multi_hand_landmarks:
            for hand_landmarks in self.results.multi_hand_landmarks:
                                    
                if draw:
                    self.mpDraw.draw_landmarks(frame, hand_landmarks, self.mpHands.HAND_CONNECTIONS)
                    
        return frame


    def position(self, frame, handNo=0, draw=True):
        self.lmList = []
        
        if  self.results.multi_hand_landmarks:
            myHand = self.results.multi_hand_landmarks[handNo]
            for id, lm in enumerate(myHand.landmark):
                h, w, c = frame.shape
                cx, cy = int(lm.x*w), int(lm.y*h)
                self.lmList.append([id, cx, cy])
                if draw:
                    if id == 8:
                        cv2.circle(frame, (cx, cy), 15, (255,0,255), cv2.FILLED)
        return self.lmList

    def fingers_up(self):
        fingers = []
        # Thumb
        if self.lmList[self.tipIds[0]][1] > self.lmList[self.tipIds[0] - 1][1]:
            fingers.append(1)
        else:
            fingers.append(0)
        # 4 Fingers
        for id in range(1,5):
            if self.lmList[self.tipIds[id]][2] < self.lmList[self.tipIds[id] - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)
            
        return fingers

    def find_distance(self, point1, point2):
        x1, y1 = self.lmList[point1][1:]
        x2, y2 = self.lmList[point2][1:]
        distance = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        return distance


def main():
    
    pTime = 0
    cap = cv2.VideoCapture(0)
    
    detector = HandDetector()
    
    while True:
        ret, frame = cap.read()
        detector.analyse(frame)
        frame = detector.detection(frame)
        LmList = detector.position(frame)
        
    
        
        if not ret:
            break
        
        cTime = time.time()
        fps = 1/(cTime-pTime)
        pTime = cTime
        

        frame = cv2.flip(frame, 1)
        cv2.putText(frame, str(int(fps)), (20,50), cv2.FONT_HERSHEY_PLAIN, 3, (255,0,0), 3)
        cv2.imshow('Hand Mouse Control', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): #press q to kill 
            cap.release()
            cv2.destroyAllWindows()
            break

if __name__ == "__main__":
    main()