import cv2
import mediapipe as mp
import pyautogui
import random
import util
from pynput.mouse import Button, Controller
import time
import subprocess
import platform

mouse = Controller()

screen_width, screen_height = pyautogui.size()

# Variables for drag & drop and scroll gestures
drag_active = False
last_scroll_time = 0
scroll_threshold = 0.05  # Minimum hand movement for scroll
last_index_y = None

mpHands = mp.solutions.hands
hands = mpHands.Hands(
    static_image_mode=False,
    model_complexity=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7,
    max_num_hands=1
)

def find_finger_tip(processed):
    if processed.multi_hand_landmarks:
        hand_landmarks = processed.multi_hand_landmarks[0]  # Assuming only one hand is detected
        index_finger_tip = hand_landmarks.landmark[mpHands.HandLandmark.INDEX_FINGER_TIP]
        return index_finger_tip
    return None


def move_mouse(index_finger_tip):
    if index_finger_tip is not None:
        x = int(index_finger_tip.x * screen_width)
        y = int(index_finger_tip.y / 2 * screen_height)
        pyautogui.moveTo(x, y)


def is_left_click(landmark_list, thumb_index_dist):
    return (
            util.get_angle(landmark_list[5], landmark_list[6], landmark_list[8]) < 50 and
            util.get_angle(landmark_list[9], landmark_list[10], landmark_list[12]) > 90 and
            thumb_index_dist > 50
    )


def is_right_click(landmark_list, thumb_index_dist):
    return (
            util.get_angle(landmark_list[9], landmark_list[10], landmark_list[12]) < 50 and
            util.get_angle(landmark_list[5], landmark_list[6], landmark_list[8]) > 90  and
            thumb_index_dist > 50
    )


def is_double_click(landmark_list, thumb_index_dist):
    return (
            util.get_angle(landmark_list[5], landmark_list[6], landmark_list[8]) < 50 and
            util.get_angle(landmark_list[9], landmark_list[10], landmark_list[12]) < 50 and
            thumb_index_dist > 50
    )


def is_screenshot(landmark_list, thumb_index_dist):
    return (
            util.get_angle(landmark_list[5], landmark_list[6], landmark_list[8]) < 50 and
            util.get_angle(landmark_list[9], landmark_list[10], landmark_list[12]) < 50 and
            thumb_index_dist < 50
    )


def is_scroll_gesture(landmark_list):
    # Scroll gesture: Index finger pointing up, other fingers closed
    return (
            util.get_angle(landmark_list[5], landmark_list[6], landmark_list[8]) < 30 and  # Index finger straight
            util.get_angle(landmark_list[9], landmark_list[10], landmark_list[12]) > 100 and  # Middle finger closed
            util.get_angle(landmark_list[13], landmark_list[14], landmark_list[16]) > 100 and  # Ring finger closed
            util.get_angle(landmark_list[17], landmark_list[18], landmark_list[20]) > 100    # Pinky finger closed
    )


def is_drag_gesture(landmark_list, thumb_index_dist):
    # Drag gesture: Index and middle fingers pointing, thumb close to index
    return (
            util.get_angle(landmark_list[5], landmark_list[6], landmark_list[8]) < 50 and  # Index finger straight
            util.get_angle(landmark_list[9], landmark_list[10], landmark_list[12]) < 50 and  # Middle finger straight
            util.get_angle(landmark_list[13], landmark_list[14], landmark_list[16]) > 90 and   # Ring finger closed
            util.get_angle(landmark_list[17], landmark_list[18], landmark_list[20]) > 90 and   # Pinky finger closed
            thumb_index_dist < 80  # Thumb close to index finger
    )


def is_volume_up_gesture(landmark_list):
    # Volume up: Thumb tip (4) close to pinky tip (20), and middle finger tip (12) close to ring finger tip (16)
    thumb_pinky_dist = util.get_distance([landmark_list[4], landmark_list[20]])
    middle_ring_dist = util.get_distance([landmark_list[12], landmark_list[16]])
    return thumb_pinky_dist < 50 and middle_ring_dist < 50


def is_volume_down_gesture(landmark_list):
    # Volume down: Thumb tip (4) close to middle finger tip (12), and middle finger tip (12) close to ring finger tip (16)
    thumb_middle_dist = util.get_distance([landmark_list[4], landmark_list[12]])
    middle_ring_dist = util.get_distance([landmark_list[12], landmark_list[16]])
    return thumb_middle_dist < 50 and middle_ring_dist < 50


def set_volume(increase=True):
    try:
        if platform.system() == "Windows":
            # Windows volume control using nircmd (if available) or PowerShell
            if increase:
                subprocess.run(['powershell', '-Command', '(New-Object -comObject WScript.Shell).SendKeys([char]175)'], capture_output=True)
            else:
                subprocess.run(['powershell', '-Command', '(New-Object -comObject WScript.Shell).SendKeys([char]174)'], capture_output=True)
        elif platform.system() == "Darwin":  # macOS
            if increase:
                subprocess.run(['osascript', '-e', 'set volume output volume (output volume of (get volume output settings) + 10)'], capture_output=True)
            else:
                subprocess.run(['osascript', '-e', 'set volume output volume (output volume of (get volume output settings) - 10)'], capture_output=True)
        elif platform.system() == "Linux":
            if increase:
                subprocess.run(['amixer', 'set', 'Master', '5%+'], capture_output=True)
            else:
                subprocess.run(['amixer', 'set', 'Master', '5%-'], capture_output=True)
    except Exception as e:
        print(f"Volume control error: {e}")


def detect_gesture(frame, landmark_list, processed):
    global drag_active, last_scroll_time, last_index_y
    
    if len(landmark_list) >= 21:

        index_finger_tip = find_finger_tip(processed)
        thumb_index_dist = util.get_distance([landmark_list[4], landmark_list[5]])

        if util.get_distance([landmark_list[4], landmark_list[8]]) < 50  and util.get_angle(landmark_list[5], landmark_list[6], landmark_list[8]) > 90:
            print("Mouse movement gesture detected!")
            move_mouse(index_finger_tip)
            cv2.putText(frame, "MOVING MOUSE", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            # drag_active = False  # Reset drag when moving mouse
        # elif is_scroll_gesture(landmark_list):
        #     print("Scroll gesture detected!")
        #     handle_scroll_gesture(frame, index_finger_tip)
            # drag_active = False  # Reset drag when scrolling
        elif is_drag_gesture(landmark_list, thumb_index_dist):
            print("Drag gesture detected!")
            handle_drag_gesture(frame, index_finger_tip)
        elif is_volume_up_gesture(landmark_list):
            set_volume(increase=True)
            cv2.putText(frame, "Volume Up", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            drag_active = False
        elif is_volume_down_gesture(landmark_list):
            set_volume(increase=False)
            cv2.putText(frame, "Volume Down", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            drag_active = False
        elif is_left_click(landmark_list,  thumb_index_dist):
            mouse.press(Button.left)
            mouse.release(Button.left)
            cv2.putText(frame, "Left Click", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            drag_active = False
        elif is_right_click(landmark_list, thumb_index_dist):
            mouse.press(Button.right)
            mouse.release(Button.right)
            cv2.putText(frame, "Right Click", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            drag_active = False
        elif is_double_click(landmark_list, thumb_index_dist):
            pyautogui.doubleClick()
            cv2.putText(frame, "Double Click", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
            drag_active = False
        elif is_screenshot(landmark_list,thumb_index_dist ):
            im1 = pyautogui.screenshot()
            label = random.randint(1, 1000)
            im1.save(f'my_screenshot_{label}.png')
            cv2.putText(frame, "Screenshot Taken", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
            drag_active = False


def handle_scroll_gesture(frame, index_finger_tip):
    global last_scroll_time, last_index_y
    
    current_time = time.time()
    
    if index_finger_tip is not None and (current_time - last_scroll_time) > 0.1:  # Throttle scroll events
        current_y = index_finger_tip.y
        
        if last_index_y is not None:
            y_diff = last_index_y - current_y
            
            if abs(y_diff) > scroll_threshold:
                if y_diff > 0:  # Hand moved up = scroll up
                    pyautogui.scroll(3)
                    cv2.putText(frame, "Scroll Up", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                else:  # Hand moved down = scroll down
                    pyautogui.scroll(-3)
                    cv2.putText(frame, "Scroll Down", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                
                last_scroll_time = current_time
        
        last_index_y = current_y


def handle_drag_gesture(frame, index_finger_tip):
    global drag_active
    
    if index_finger_tip is not None:
        x = int(index_finger_tip.x * screen_width)
        y = int(index_finger_tip.y * screen_height)
        
        if not drag_active:
            # Start drag
            mouse.position = (x, y)
            mouse.press(Button.left)
            drag_active = True
            cv2.putText(frame, "Drag Started", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2)
        else:
            # Continue drag
            mouse.position = (x, y)
            cv2.putText(frame, "Dragging...", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2)


def main():
    draw = mp.solutions.drawing_utils
    cap = cv2.VideoCapture(0)

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)
            frameRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            processed = hands.process(frameRGB)

            landmark_list = []
            if processed.multi_hand_landmarks:
                hand_landmarks = processed.multi_hand_landmarks[0]  # Assuming only one hand is detected
                draw.draw_landmarks(frame, hand_landmarks, mpHands.HAND_CONNECTIONS)
                for lm in hand_landmarks.landmark:
                    landmark_list.append((lm.x, lm.y))
            # Debug: show hand detection status
            if processed.multi_hand_landmarks:
                cv2.putText(frame, "HAND DETECTED", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            else:
                cv2.putText(frame, "NO HAND DETECTED", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            detect_gesture(frame, landmark_list, processed)
            cv2.namedWindow('Frame', cv2.WINDOW_NORMAL)
            cv2.moveWindow('Frame', 10, 10)
            cv2.resizeWindow('Frame', 640, 480)

            cv2.imshow('Frame', frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break 
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()