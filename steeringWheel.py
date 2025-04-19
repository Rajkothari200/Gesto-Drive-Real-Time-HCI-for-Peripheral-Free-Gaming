import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import time
import pydirectinput
import directinput

# Constants
FINGER_DISTANCE_THRESHOLD = 60
OPEN_HAND_TIME_THRESHOLD = 2
CLICK_DISTANCE_THRESHOLD = 30
STEERING_SENSITIVITY = 0.2

# Initialize
mp_drawing = mp.solutions.drawing_utils
mphands = mp.solutions.hands
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
hands = mphands.Hands()
flag = True
screen_width, screen_height = pyautogui.size()
mode = "fingerPointer"
open_hand_start_time = None

def write_text(img, text, x, y):
    font = cv2.FONT_HERSHEY_SIMPLEX
    pos = (x, y)
    fontScale = 1
    fontColor = (255, 255, 255)
    lineType = 2
    cv2.putText(img, text, pos, font, fontScale, fontColor, lineType)

def calculate_distance(x1, y1, x2, y2):
    return np.sqrt((x1 - x2)**2 + (y1 - y2)**2)

def is_hand_open(pinky_x, pinky_y, thumb_x, thumb_y, ring_x, ring_y, middle_x, middle_y):
    return calculate_distance(pinky_x, pinky_y, thumb_x, thumb_y) > FINGER_DISTANCE_THRESHOLD and \
           calculate_distance(ring_x, ring_y, thumb_x, thumb_y) > FINGER_DISTANCE_THRESHOLD and \
           calculate_distance(middle_x, middle_y, thumb_x, thumb_y) > FINGER_DISTANCE_THRESHOLD and \
           calculate_distance(pinky_x, pinky_y, ring_x, ring_y) > FINGER_DISTANCE_THRESHOLD and \
           calculate_distance(pinky_x, pinky_y, middle_x, middle_y) > FINGER_DISTANCE_THRESHOLD and \
           calculate_distance(ring_x, ring_y, middle_x, middle_y) > FINGER_DISTANCE_THRESHOLD

def handle_finger_pointer_mode(image, width, height, index_finger_x, index_finger_y, thumb_x, thumb_y, pinky_x, pinky_y, ring_x, ring_y, middle_x, middle_y):
    global mode, open_hand_start_time
    if is_hand_open(pinky_x, pinky_y, thumb_x, thumb_y, ring_x, ring_y, middle_x, middle_y):
        if open_hand_start_time is None:
            open_hand_start_time = time.time()
        elif time.time() - open_hand_start_time > OPEN_HAND_TIME_THRESHOLD:
            mode = "steeringWheel"
            open_hand_start_time = None
    else:
        open_hand_start_time = None
    cv2.circle(image, (index_finger_x, index_finger_y), 15, (255, 0, 0), -1)
    pyautogui.moveTo(index_finger_x * screen_width / width, index_finger_y * screen_height / height)
    if calculate_distance(pinky_x, pinky_y, thumb_x, thumb_y) < CLICK_DISTANCE_THRESHOLD:
        pyautogui.click()

def handle_steering_wheel_mode(image, width, height, left_hand_landmarks, right_hand_landmarks):
    global mode
    
    left_middle_finger_x, left_middle_finger_y = (left_hand_landmarks[11].x * width), (left_hand_landmarks[11].y * height)
    right_middle_finger_x, right_middle_finger_y = (right_hand_landmarks[11].x * width), (right_hand_landmarks[11].y * height)
    slope = ((right_middle_finger_y - left_middle_finger_y)/(right_middle_finger_x - left_middle_finger_x))
    
    # Get the coordinates of the fingers
    left_pinky_x, left_pinky_y = (left_hand_landmarks[20].x * width), (left_hand_landmarks[20].y * height)
    left_thumb_x, left_thumb_y = (left_hand_landmarks[4].x * width), (left_hand_landmarks[4].y * height)
    left_ring_x, left_ring_y = (left_hand_landmarks[16].x * width), (left_hand_landmarks[16].y * height)
    
    # Check if the hand is open
    if is_hand_open(left_pinky_x, left_pinky_y, left_thumb_x, left_thumb_y, left_ring_x, left_ring_y, left_middle_finger_x, left_middle_finger_y):
        mode = "fingerPointer"
        return
    
    if abs(slope) > STEERING_SENSITIVITY:
        if slope < 0:
            print("Turn left.")
            write_text(image, "Left.", 360, 360)
            directinput.release_key("w")
            directinput.release_key('a')
            directinput.press_key('a')
        if slope > 0:
            print("Turn right.")
            write_text(image, "Right.", 360, 360)
            directinput.release_key('w')
            directinput.release_key('a')
            directinput.press_key('d')
    if abs(slope) < STEERING_SENSITIVITY:
        print("Keeping straight.")
        write_text(image, "Straight.", 360, 360)
        directinput.release_key('a')
        directinput.release_key('d')
        directinput.press_key('w')

while True:
    success, image = cap.read()
    image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)
    results = hands.process(image)
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(image, hand_landmarks, mphands.HAND_CONNECTIONS)
            index_finger_tip = hand_landmarks.landmark[mphands.HandLandmark.INDEX_FINGER_TIP]
            thumb_tip = hand_landmarks.landmark[mphands.HandLandmark.THUMB_TIP]
            pinky_finger_tip = hand_landmarks.landmark[mphands.HandLandmark.PINKY_TIP]
            ring_finger_tip = hand_landmarks.landmark[mphands.HandLandmark.RING_FINGER_TIP]
            middle_finger_tip = hand_landmarks.landmark[mphands.HandLandmark.MIDDLE_FINGER_TIP]
            height, width, _ = image.shape
            index_finger_x = int(index_finger_tip.x * width)
            index_finger_y = int(index_finger_tip.y * height)
            thumb_x = int(thumb_tip.x * width)
            thumb_y = int(thumb_tip.y * height)
            pinky_x = int(pinky_finger_tip.x * width)
            pinky_y = int(pinky_finger_tip.y * height)
            ring_x = int(ring_finger_tip.x * width)
            ring_y = int(ring_finger_tip.y * height)
            middle_x = int(middle_finger_tip.x * width)
            middle_y = int(middle_finger_tip.y * height)
            if mode == "fingerPointer":
                handle_finger_pointer_mode(image, width, height, index_finger_x, index_finger_y, thumb_x, thumb_y, pinky_x, pinky_y, ring_x, ring_y, middle_x, middle_y)
            else:
                if len(results.multi_hand_landmarks) == 2:
                    handle_steering_wheel_mode(image, width, height, results.multi_hand_landmarks[1].landmark, results.multi_hand_landmarks[0].landmark)
    cv2.imshow('HandTracker', image)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
cap.release()
cv2.destroyAllWindows()