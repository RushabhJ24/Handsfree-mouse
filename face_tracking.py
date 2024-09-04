from PyQt5.QtCore import QThread, pyqtSignal
import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import time

class FaceTracker(QThread):
    finished = pyqtSignal()

    def __init__(self, sensitivity=3, blink_threshold=0.2, blink_duration=0.3, 
                 mouth_open_threshold=30, mouth_open_duration=0.5, 
                 tilt_threshold=10, scroll_speed=20):
        super().__init__()
        self.sensitivity = sensitivity
        self.previous_positions = None
        self.blink_threshold = blink_threshold
        self.blink_duration = blink_duration
        self.left_eye_closed = False
        self.right_eye_closed = False
        self.left_blink_start = 0
        self.right_blink_start = 0
        self.mouth_open_threshold = mouth_open_threshold
        self.mouth_open = False
        self.mouth_open_start = 0
        self.mouth_open_duration = mouth_open_duration
        self.tilt_threshold = tilt_threshold
        self.scroll_speed = scroll_speed
        self.neutral_angle = None
        self.calibration_frames = 30
        self.scroll_mode_active = False  # Add a flag for scroll mode

    def detect_blink(self, eye_landmarks, image):
        height, width = image.shape[:2]
        
        eye_points = [
            (int(eye_landmarks[p].x * width), int(eye_landmarks[p].y * height))
            for p in range(len(eye_landmarks))
        ]
        
        ear = self.eye_aspect_ratio(eye_points)
        
        return ear < self.blink_threshold

    def eye_aspect_ratio(self, eye):
        A = self.distance(eye[1], eye[5])
        B = self.distance(eye[2], eye[4])
        C = self.distance(eye[0], eye[3])
        ear = (A + B) / (2.0 * C)
        return ear

    def distance(self, p1, p2):
        return ((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)**0.5

    def detect_mouth_open(self, mouth_landmarks, image):
        height, width = image.shape[:2]
        
        if len(mouth_landmarks) < 2:
            return False
        
        top_lip = int(mouth_landmarks[0].y * height)
        bottom_lip = int(mouth_landmarks[1].y * height)
        
        mouth_opening = bottom_lip - top_lip
        return mouth_opening > self.mouth_open_threshold

    def detect_head_tilt(self, face_landmarks, image):
        height, width = image.shape[:2]
        
        nose_tip = (face_landmarks.landmark[4].x * width, face_landmarks.landmark[4].y * height)
        left_eye = (face_landmarks.landmark[159].x * width, face_landmarks.landmark[159].y * height)
        right_eye = (face_landmarks.landmark[386].x * width, face_landmarks.landmark[386].y * height)
        
        eye_center = ((left_eye[0] + right_eye[0]) / 2, (left_eye[1] + right_eye[1]) / 2)
        
        delta_y = nose_tip[1] - eye_center[1]
        delta_x = nose_tip[0] - eye_center[0]
        angle = np.degrees(np.arctan2(delta_y, delta_x)) - 90
        
        return angle

    def run(self):
        cap = cv2.VideoCapture(0)
        mp_face_mesh = mp.solutions.face_mesh
        face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True, min_detection_confidence=0.5, min_tracking_confidence=0.5)

        stable_landmarks_indices = [1, 4, 5, 6, 10, 152, 101, 330, 362, 385, 387, 263, 373, 380, 33, 160, 158, 133, 153, 144, 13, 14]
        left_eye_indices = [362, 385, 387, 263, 373, 380]
        right_eye_indices = [33, 160, 158, 133, 153, 144]
        mouth_indices = [13, 14]

        pyautogui.FAILSAFE = False
        calibration_count = 0

        while True:
            success, image = cap.read()
            if not success:
                continue

            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(image_rgb)

            if results.multi_face_landmarks:
                for face_landmarks in results.multi_face_landmarks:
                    current_positions = []

                    for idx in stable_landmarks_indices:
                        landmark = face_landmarks.landmark[idx]
                        x = int(landmark.x * image.shape[1])
                        y = int(landmark.y * image.shape[0])
                        current_positions.append((x, y))
                        cv2.circle(image, (x, y), 2, (0, 255, 0), -1)

                    left_eye_landmarks = [face_landmarks.landmark[i] for i in left_eye_indices]
                    right_eye_landmarks = [face_landmarks.landmark[i] for i in right_eye_indices]
                    mouth_landmarks = [face_landmarks.landmark[i] for i in mouth_indices]

                    left_blink = self.detect_blink(left_eye_landmarks, image)
                    right_blink = self.detect_blink(right_eye_landmarks, image)
                    mouth_open = self.detect_mouth_open(mouth_landmarks, image)

                    current_time = time.time()

                    # Handle left eye blink
                    if left_blink and not self.left_eye_closed:
                        self.left_eye_closed = True
                        self.left_blink_start = current_time
                    elif not left_blink and self.left_eye_closed:
                        if current_time - self.left_blink_start > self.blink_duration:
                            pyautogui.click(button='left')
                            print("Left Click")
                        self.left_eye_closed = False

                    # Handle right eye blink
                    if right_blink and not self.right_eye_closed:
                        self.right_eye_closed = True
                        self.right_blink_start = current_time
                    elif not right_blink and self.right_eye_closed:
                        if current_time - self.right_blink_start > self.blink_duration:
                            pyautogui.click(button='right')
                            print("Right Click")
                        self.right_eye_closed = False

                    # Handle mouth open (double-click)
                    if mouth_open and not self.mouth_open:
                        self.mouth_open = True
                        self.mouth_open_start = current_time
                    elif not mouth_open and self.mouth_open:
                        if current_time - self.mouth_open_start > self.mouth_open_duration:
                            pyautogui.doubleClick()
                            print("Double Click")
                        self.mouth_open = False

                    # Head tilt detection and scrolling
                    if self.scroll_mode_active:
                        tilt_angle = self.detect_head_tilt(face_landmarks, image)
                        
                        if self.neutral_angle is None:
                            if calibration_count < self.calibration_frames:
                                if self.neutral_angle is None:
                                    self.neutral_angle = 0
                                self.neutral_angle += tilt_angle
                                calibration_count += 1
                            else:
                                self.neutral_angle /= self.calibration_frames
                                print(f"Calibration complete. Neutral angle: {self.neutral_angle}")
                        else:
                            relative_tilt = tilt_angle - self.neutral_angle
                            if abs(relative_tilt) > self.tilt_threshold:
                                scroll_amount = int((relative_tilt - self.tilt_threshold) * self.scroll_speed / 10)
                                pyautogui.scroll(scroll_amount)
                                print(f"Scrolling: {scroll_amount}")

                    if self.previous_positions is not None:
                        move_x = 0
                        move_y = 0
                        for i, (prev_pos, curr_pos) in enumerate(zip(self.previous_positions, current_positions)):
                            move_x += curr_pos[0] - prev_pos[0]
                            move_y += curr_pos[1] - prev_pos[1]
                        
                        move_x /= len(stable_landmarks_indices)
                        move_y /= len(stable_landmarks_indices)

                        try:
                            movement = (-(move_x * (self.sensitivity)**2)**1/2, (move_y * (self.sensitivity)**2)**1/2)
                        except:
                            movement = (0, 0)
                        pyautogui.moveRel(movement[0], movement[1])

                    self.previous_positions = current_positions

            cv2.imshow('Face Tracker', cv2.flip(image, 1))
            if cv2.waitKey(5) & 0xFF == 27:  # Press 'ESC' to exit
                break

        cap.release()
        cv2.destroyAllWindows()
        self.finished.emit()