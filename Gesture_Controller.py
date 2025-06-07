import cv2
import mediapipe as mp
import pyautogui
import math
from enum import IntEnum
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from google.protobuf.json_format import MessageToDict
import screen_brightness_control as sbcontrol

pyautogui.FAILSAFE = False
mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands


class Gest(IntEnum):
    FIST = 0
    PINKY = 1
    RING = 2
    MID = 4
    LAST3 = 7
    INDEX = 8
    FIRST2 = 12
    LAST4 = 15
    THUMB = 16
    PALM = 31
    V_GEST = 33
    TWO_FINGER_CLOSED = 34
    PINCH_MAJOR = 35
    PINCH_MINOR = 36
    THREE_FINGERS = 14


class HLabel(IntEnum):
    MINOR = 0
    MAJOR = 1


class HandRecog:
    def __init__(self, hand_label):
        self.finger = 0
        self.ori_gesture = Gest.PALM
        self.prev_gesture = Gest.PALM
        self.frame_count = 0
        self.hand_result = None
        self.hand_label = hand_label

    def update_hand_result(self, hand_result):
        self.hand_result = hand_result

    def get_signed_dist(self, point):
        sign = -1
        if self.hand_result.landmark[point[0]].y < self.hand_result.landmark[point[1]].y:
            sign = 1
        dist = (self.hand_result.landmark[point[0]].x - self.hand_result.landmark[point[1]].x) ** 2
        dist += (self.hand_result.landmark[point[0]].y - self.hand_result.landmark[point[1]].y) ** 2
        return math.sqrt(dist) * sign

    def get_dist(self, point):
        dist = (self.hand_result.landmark[point[0]].x - self.hand_result.landmark[point[1]].x) ** 2
        dist += (self.hand_result.landmark[point[0]].y - self.hand_result.landmark[point[1]].y) ** 2
        return math.sqrt(dist)

    def get_dz(self, point):
        return abs(self.hand_result.landmark[point[0]].z - self.hand_result.landmark[point[1]].z)

    def set_finger_state(self):
        if self.hand_result is None:
            return
        points = [[8, 5, 0], [12, 9, 0], [16, 13, 0], [20, 17, 0]]
        self.finger = 0
        self.finger = self.finger | 0
        for idx, point in enumerate(points):
            dist = self.get_signed_dist(point[:2])
            dist2 = self.get_signed_dist(point[1:])
            try:
                ratio = round(dist / dist2, 1)
            except:
                ratio = round(dist / 0.01, 1)
            self.finger = self.finger << 1
            if ratio > 0.5:
                self.finger = self.finger | 1

    def get_gesture(self):
        if self.hand_result is None:
            return Gest.PALM

        current_gesture = Gest.PALM
        if self.finger in [Gest.LAST3, Gest.LAST4] and self.get_dist([8, 4]) < 0.05:
            current_gesture = Gest.PINCH_MINOR if self.hand_label == HLabel.MINOR else Gest.PINCH_MAJOR
        elif self.finger == Gest.FIRST2:
            dist1 = self.get_dist([8, 12])
            dist2 = self.get_dist([5, 9])
            ratio = dist1 / dist2
            if ratio > 1.7:
                current_gesture = Gest.V_GEST
            else:
                current_gesture = Gest.TWO_FINGER_CLOSED if self.get_dz([8, 12]) < 0.1 else Gest.MID
        else:
            current_gesture = self.finger

        if current_gesture == self.prev_gesture:
            self.frame_count += 1
        else:
            self.frame_count = 0

        self.prev_gesture = current_gesture
        if self.frame_count > 4:
            self.ori_gesture = current_gesture

        # ✅ DEBUG print to see what gesture is being detected
        print(
            f"[DEBUG] Finger bitmask: {bin(self.finger)} | Detected Gesture: {Gest(self.ori_gesture).name if isinstance(self.ori_gesture, Gest) else self.ori_gesture}")

        return self.ori_gesture


class Controller:
    tx_old = 0
    ty_old = 0
    trial = True
    flag = False
    grabflag = False
    pinchmajorflag = False
    pinchminorflag = False
    fistflag = False  # New flag for fist gesture
    fist_selected = False  # Track selection state
    fist_drag_mode = False  # Track if we're in drag mode
    pinchstartxcoord = None
    pinchstartycoord = None
    pinchdirectionflag = None
    prevpinchlv = 0
    pinchlv = 0
    framecount = 0
    prev_hand = None
    pinch_threshold = 0.3
    volume_muted = False

    @staticmethod
    def getpinchylv(hand_result):
        return round((Controller.pinchstartycoord - hand_result.landmark[8].y) * 10, 1)

    @staticmethod
    def getpinchxlv(hand_result):
        return round((hand_result.landmark[8].x - Controller.pinchstartxcoord) * 10, 1)

    @staticmethod
    def changesystembrightness():
        try:
            brightness_list = sbcontrol.get_brightness(display=0)
            if not brightness_list:
                return
            currentBrightnessLv = brightness_list[0] / 100.0
            currentBrightnessLv += Controller.pinchlv / 50.0
            currentBrightnessLv = min(max(currentBrightnessLv, 0.0), 1.0)
            sbcontrol.fade_brightness(int(100 * currentBrightnessLv), start=brightness_list[0])
        except Exception as e:
            print(f"[Brightness Error] {e}")

    @staticmethod
    def changesystemvolume():
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        currentVolumeLv = volume.GetMasterVolumeLevelScalar()
        currentVolumeLv += Controller.pinchlv / 50.0
        currentVolumeLv = min(max(currentVolumeLv, 0.0), 1.0)
        volume.SetMasterVolumeLevelScalar(currentVolumeLv, None)

    @staticmethod
    def scrollVertical():
        pyautogui.scroll(120 if Controller.pinchlv > 0.0 else -120)

    @staticmethod
    def scrollHorizontal():
        pyautogui.keyDown('shift')
        pyautogui.keyDown('ctrl')
        pyautogui.scroll(-120 if Controller.pinchlv > 0.0 else 120)
        pyautogui.keyUp('ctrl')
        pyautogui.keyUp('shift')

    @staticmethod
    def get_position(hand_result):
        point = 9
        position = [hand_result.landmark[point].x, hand_result.landmark[point].y]
        sx, sy = pyautogui.size()
        x_old, y_old = pyautogui.position()
        x = int(position[0] * sx)
        y = int(position[1] * sy)
        if Controller.prev_hand is None:
            Controller.prev_hand = x, y
        delta_x = x - Controller.prev_hand[0]
        delta_y = y - Controller.prev_hand[1]
        distsq = delta_x ** 2 + delta_y ** 2
        ratio = 0 if distsq <= 25 else (0.07 * (distsq ** 0.5) if distsq <= 900 else 2.1)
        Controller.prev_hand = [x, y]
        return (x_old + delta_x * ratio, y_old + delta_y * ratio)

    @staticmethod
    def pinch_control_init(hand_result):
        Controller.pinchstartxcoord = hand_result.landmark[8].x
        Controller.pinchstartycoord = hand_result.landmark[8].y
        Controller.pinchlv = 0
        Controller.prevpinchlv = 0
        Controller.framecount = 0

    @staticmethod
    def pinch_control(hand_result, controlHorizontal, controlVertical):
        if Controller.framecount == 5:
            Controller.framecount = 0
            Controller.pinchlv = Controller.prevpinchlv
            if Controller.pinchdirectionflag is True:
                controlHorizontal()
            elif Controller.pinchdirectionflag is False:
                controlVertical()
        lvx = Controller.getpinchxlv(hand_result)
        lvy = Controller.getpinchylv(hand_result)
        if abs(lvy) > abs(lvx) and abs(lvy) > Controller.pinch_threshold:
            Controller.pinchdirectionflag = False
            Controller.framecount = Controller.framecount + 1 if abs(
                Controller.prevpinchlv - lvy) < Controller.pinch_threshold else 0
            Controller.prevpinchlv = lvy
        elif abs(lvx) > Controller.pinch_threshold:
            Controller.pinchdirectionflag = True
            Controller.framecount = Controller.framecount + 1 if abs(
                Controller.prevpinchlv - lvx) < Controller.pinch_threshold else 0
            Controller.prevpinchlv = lvx

    @staticmethod
    def toggle_mute_volume():
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            new_mute_state = not Controller.volume_muted
            volume.SetMute(int(new_mute_state), None)
            Controller.volume_muted = new_mute_state
            print(f"Volume {'muted' if new_mute_state else 'unmuted'}.")
        except Exception as e:
            print(f"[Toggle Mute Error] {e}")

    @staticmethod
    def handle_fist_selection():
        """Handle fist gesture for selection/deselection and drag functionality"""
        if not Controller.fist_selected:
            # Fist closed - select/start drag
            Controller.fist_selected = True
            Controller.fist_drag_mode = True
            pyautogui.mouseDown(button="left")
            print("[FIST] Selection started - Left mouse button down")
        else:
            # This case shouldn't happen as we handle deselection when gesture changes
            pass

    @staticmethod
    def handle_fist_deselection():
        """Handle when fist is opened (gesture changes from FIST)"""
        if Controller.fist_selected:
            Controller.fist_selected = False
            Controller.fist_drag_mode = False
            pyautogui.mouseUp(button="left")
            print("[FIST] Selection ended - Left mouse button up")

    @staticmethod
    def handle_controls(gesture, hand_result):
        x, y = None, None
        if gesture != Gest.PALM:
            x, y = Controller.get_position(hand_result)

        # Handle fist gesture for selection and drag
        if gesture == Gest.FIST:
            if not Controller.fistflag:
                Controller.fistflag = True
                Controller.handle_fist_selection()
            # Move mouse while fist is closed (drag functionality)
            if Controller.fist_drag_mode and x is not None and y is not None:
                pyautogui.moveTo(x, y, duration=0.1)
        else:
            # Fist opened - handle deselection
            if Controller.fistflag:
                Controller.fistflag = False
                Controller.handle_fist_deselection()

        # Mute/Unmute on three fingers (LAST3) - modified to avoid conflict with fist drag
        if gesture == Gest.THREE_FINGERS:
            if not Controller.grabflag and not Controller.fist_drag_mode:  # Don't interfere with fist drag
                Controller.grabflag = True
                Controller.toggle_mute_volume()
                pyautogui.mouseDown(button="left")
            if not Controller.fist_drag_mode:  # Only move if not in fist drag mode
                pyautogui.moveTo(x, y, duration=0.1)
        else:
            if Controller.grabflag:
                Controller.grabflag = False
                pyautogui.mouseUp(button="left")

        # Reset pinch flags when not in pinch gestures
        if gesture != Gest.PINCH_MAJOR and Controller.pinchmajorflag:
            Controller.pinchmajorflag = False
        if gesture != Gest.PINCH_MINOR and Controller.pinchminorflag:
            Controller.pinchminorflag = False

        # Existing gesture controls
        if gesture == Gest.V_GEST:
            Controller.flag = True
            pyautogui.moveTo(x, y, duration=0.1)
        elif gesture == Gest.MID and Controller.flag:
            pyautogui.click()
            Controller.flag = False
        elif gesture == Gest.INDEX and Controller.flag:
            pyautogui.click(button='right')
            Controller.flag = False
        elif gesture == Gest.TWO_FINGER_CLOSED and Controller.flag:
            pyautogui.doubleClick()
            Controller.flag = False
        elif gesture == Gest.PINCH_MINOR:
            if not Controller.pinchminorflag:
                Controller.pinch_control_init(hand_result)
                Controller.pinchminorflag = True
            Controller.pinch_control(hand_result, Controller.scrollHorizontal, Controller.scrollVertical)
        elif gesture == Gest.PINCH_MAJOR:
            if not Controller.pinchmajorflag:
                Controller.pinch_control_init(hand_result)
                Controller.pinchmajorflag = True
            Controller.pinch_control(hand_result, Controller.changesystembrightness, Controller.changesystemvolume)


class GestureController:
    gc_mode = 0
    cap = None
    CAM_HEIGHT = None
    CAM_WIDTH = None
    hr_major = None
    hr_minor = None
    dom_hand = True

    def __init__(self):
        GestureController.gc_mode = 1
        GestureController.cap = cv2.VideoCapture(0)
        GestureController.CAM_HEIGHT = GestureController.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        GestureController.CAM_WIDTH = GestureController.cap.get(cv2.CAP_PROP_FRAME_WIDTH)

    @staticmethod
    def classify_hands(results):
        left, right = None, None
        try:
            handedness_dict = MessageToDict(results.multi_handedness[0])
            if handedness_dict['classification'][0]['label'] == 'Right':
                right = results.multi_hand_landmarks[0]
            else:
                left = results.multi_hand_landmarks[0]
        except:
            pass
        try:
            handedness_dict = MessageToDict(results.multi_handedness[1])
            if handedness_dict['classification'][0]['label'] == 'Right':
                right = results.multi_hand_landmarks[1]
            else:
                left = results.multi_hand_landmarks[1]
        except:
            pass
        if GestureController.dom_hand:
            GestureController.hr_major = right
            GestureController.hr_minor = left
        else:
            GestureController.hr_major = left
            GestureController.hr_minor = right

    def start(self):
        handmajor = HandRecog(HLabel.MAJOR)
        handminor = HandRecog(HLabel.MINOR)

        print("=== GESTURE CONTROLS ===")
        print("FIST: Select/Deselect and Drag")
        print("V_GEST: Move cursor")
        print("MID (after V_GEST): Left click")
        print("INDEX (after V_GEST): Right click")
        print("TWO_FINGER_CLOSED (after V_GEST): Double click")
        print("THREE_FINGERS: Toggle mute and drag")
        print("PINCH_MINOR: Scroll")
        print("PINCH_MAJOR: Volume/Brightness control")
        print("ESC: Exit")
        print("========================")

        with mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.5, min_tracking_confidence=0.5) as hands:
            while GestureController.cap.isOpened() and GestureController.gc_mode:
                success, image = GestureController.cap.read()
                if not success:
                    print("Ignoring empty camera frame.")
                    continue
                image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)
                image.flags.writeable = False
                results = hands.process(image)
                image.flags.writeable = True
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

                if results.multi_hand_landmarks:
                    GestureController.classify_hands(results)
                    handmajor.update_hand_result(GestureController.hr_major)
                    handminor.update_hand_result(GestureController.hr_minor)
                    handmajor.set_finger_state()
                    handminor.set_finger_state()
                    gest_name = handminor.get_gesture()
                    if gest_name == Gest.PINCH_MINOR:
                        Controller.handle_controls(gest_name, handminor.hand_result)
                    else:
                        gest_name = handmajor.get_gesture()
                        Controller.handle_controls(gest_name, handmajor.hand_result)
                    for hand_landmarks in results.multi_hand_landmarks:
                        mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                else:
                    Controller.prev_hand = None
                    # If no hands detected, make sure to deselect if fist was active
                    if Controller.fist_selected:
                        Controller.handle_fist_deselection()
                        Controller.fistflag = False

                cv2.imshow('Gesture Controller', image)
                if cv2.waitKey(5) & 0xFF == 27:
                    print("Exiting program on ESC key press.")
                    break
        GestureController.cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    gc1 = GestureController()
    gc1.start()