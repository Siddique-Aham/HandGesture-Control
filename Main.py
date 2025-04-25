import cv2
import numpy as np
import mediapipe as mp
import pyautogui  # Cursor control ke liye
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# Screen ki width/height get karo (cursor movement ke liye)
screen_w, screen_h = pyautogui.size()

# MediaPipe Hands initialize karo
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)
mp_drawing = mp.solutions.drawing_utils

# System volume control setup (pycaw)
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))
vol_range = volume.GetVolumeRange()
min_vol, max_vol = vol_range[0], vol_range[1]

# Variables
vol = 0
vol_bar = 400
vol_per = 0
click_threshold = 30  # Click ke liye thumb-index distance

# Camera start karo
cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        continue
    
    # Frame ko flip karo (mirror effect)
    frame = cv2.flip(frame, 1)
    h, w, c = frame.shape
    
    # MediaPipe ko RGB frame do
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)
    
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Landmarks draw karo
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            # Saare landmarks ki positions nikaalo
            lm_list = []
            for id, lm in enumerate(hand_landmarks.landmark):
                cx, cy = int(lm.x * w), int(lm.y * h)
                lm_list.append([id, cx, cy])
            
            if len(lm_list) > 0:
                # Index finger (Cursor control)
                index_x, index_y = lm_list[8][1], lm_list[8][2]
                
                # Cursor move karo (Screen resolution ke hisaab se)
                cursor_x = np.interp(index_x, [50, w-50], [0, screen_w])
                cursor_y = np.interp(index_y, [50, h-50], [0, screen_h])
                pyautogui.moveTo(cursor_x, cursor_y, duration=0.1)
                
                # Thumb aur index ke beech ka distance
                thumb_x, thumb_y = lm_list[4][1], lm_list[4][2]
                distance = np.hypot(index_x - thumb_x, index_y - thumb_y)
                
                # Agar distance kam hai toh CLICK karo
                if distance < click_threshold:
                    pyautogui.click()
                    cv2.circle(frame, (index_x, index_y), 15, (0, 255, 0), cv2.FILLED)
                
                # Volume control (Thumb + Index up, baaki fingers down)
                if (lm_list[8][2] < lm_list[6][2] and  # Index finger up
                    lm_list[4][2] < lm_list[3][2] and  # Thumb up
                    lm_list[12][2] > lm_list[10][2] and  # Middle finger down
                    lm_list[16][2] > lm_list[14][2] and  # Ring finger down
                    lm_list[20][2] > lm_list[18][2]):    # Pinky down
                    
                    # Distance se volume set karo
                    vol = np.interp(distance, [50, 200], [min_vol, max_vol])
                    vol_bar = np.interp(distance, [50, 200], [400, 150])
                    vol_per = np.interp(distance, [50, 200], [0, 100])
                    volume.SetMasterVolumeLevel(vol, None)
                    
                    # Line draw karo (Thumb-Index ke beech)
                    cv2.line(frame, (thumb_x, thumb_y), (index_x, index_y), (255, 0, 255), 3)
    
    # Volume bar aur % dikhao
    cv2.rectangle(frame, (50, 150), (85, 400), (0, 255, 0), 3)
    cv2.rectangle(frame, (50, int(vol_bar)), (85, 400), (0, 255, 0), cv2.FILLED)
    cv2.putText(frame, f'{int(vol_per)}%', (40, 450), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    # Instructions dikhao
    cv2.putText(frame, "Cursor: Index Finger", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, "Click: Thumb + Index Touch", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, "Volume: Thumb+Index Up, Others Down", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # Frame dikhao
    cv2.imshow("Hand Cursor + Volume Control", frame)
    
    # 'Q' dabake exit karo
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Band karo
cap.release()
cv2.destroyAllWindows()
