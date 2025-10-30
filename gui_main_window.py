from PyQt5.QtWidgets import (QWidget, QPushButton, QVBoxLayout, QSlider, QLabel, 
                             QLineEdit, QHBoxLayout, QGroupBox, QFormLayout, QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt
from face_tracking import FaceTracker
from speech import SpeechToText
from config_manager import ConfigManager
import pyautogui
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QUrl

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.initUI()
        self.speech_to_text_active = False

    def initUI(self):
        self.setWindowTitle('Face Tracking GUI with Speech-to-Text')
        self.setGeometry(100, 100, 500, 350)
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                font-family: Arial, sans-serif;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px;
                font-size: 16px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3e8e41;
            }
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 8px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #B1B1B1, stop:1 #c4c4c4);
                margin: 2px 0;
            }
            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #b4b4b4, stop:1 #8f8f8f);
                border: 1px solid #5c5c5c;
                width: 18px;
                margin: -2px 0;
                border-radius: 3px;
            }
        """)

        main_layout = QVBoxLayout()

        # Control buttons
        button_layout = QHBoxLayout()
        self.startButton = QPushButton('Start Tracking', self)
        self.startButton.clicked.connect(self.startTracking)
        self.speakButton = QPushButton('Speak', self)
        self.speakButton.clicked.connect(self.startSpeechToText)
        self.scrollButton = QPushButton('Toggle Scroll Mode', self)
        self.scrollButton.clicked.connect(self.toggleScrollMode)
        button_layout.addWidget(self.startButton)
        button_layout.addWidget(self.speakButton)
        button_layout.addWidget(self.scrollButton)
        main_layout.addLayout(button_layout)

         # Add YouTube Button
        self.youtubeButton = QPushButton('Watch Demo Video', self)
        self.youtubeButton.clicked.connect(self.openYouTubeVideo)
        main_layout.addWidget(self.youtubeButton)

        # Sensitivity slider
        sensitivity_group = QGroupBox("Sensitivity Control")
        sensitivity_layout = QVBoxLayout()
        self.sensitivitySlider = QSlider(Qt.Horizontal, self)
        self.sensitivitySlider.setMinimum(1)
        self.sensitivitySlider.setMaximum(10)
        self.sensitivitySlider.setValue(int(self.config_manager.get_value('TRACKING', 'sensitivity', '3')))
        self.sensitivitySlider.setTickPosition(QSlider.TicksBelow)
        self.sensitivitySlider.setTickInterval(1)
        self.sensitivitySlider.valueChanged.connect(self.updateSensitivity)
        self.sensitivityLabel = QLabel(f'Sensitivity: {self.sensitivitySlider.value()}', self)
        sensitivity_layout.addWidget(self.sensitivityLabel)
        sensitivity_layout.addWidget(self.sensitivitySlider)
        sensitivity_group.setLayout(sensitivity_layout)
        main_layout.addWidget(sensitivity_group)

        # Parameters input
        params_group = QGroupBox("Tracking Parameters")
        params_layout = QFormLayout()
        self.blinkThresholdInput = QLineEdit(self)
        self.blinkThresholdInput.setText(self.config_manager.get_value('TRACKING', 'blink_threshold', '0.2'))
        self.blinkDurationInput = QLineEdit(self)
        self.blinkDurationInput.setText(self.config_manager.get_value('TRACKING', 'blink_duration', '0.3'))
        self.mouthOpenThresholdInput = QLineEdit(self)
        self.mouthOpenThresholdInput.setText(self.config_manager.get_value('TRACKING', 'mouth_open_threshold', '30'))
        self.mouthOpenDurationInput = QLineEdit(self)
        self.mouthOpenDurationInput.setText(self.config_manager.get_value('TRACKING', 'mouth_open_duration', '0.5'))
        self.tiltThresholdInput = QLineEdit(self)
        self.tiltThresholdInput.setText(self.config_manager.get_value('TRACKING', 'tilt_threshold', '10'))
        self.scrollSpeedInput = QLineEdit(self)
        self.scrollSpeedInput.setText(self.config_manager.get_value('TRACKING', 'scroll_speed', '20'))
        params_layout.addRow("Blink Threshold:", self.blinkThresholdInput)
        params_layout.addRow("Blink Duration:", self.blinkDurationInput)
        params_layout.addRow("Mouth Open Threshold:", self.mouthOpenThresholdInput)
        params_layout.addRow("Mouth Open Duration:", self.mouthOpenDurationInput)
        params_layout.addRow("Tilt Threshold:", self.tiltThresholdInput)
        params_layout.addRow("Scroll Speed:", self.scrollSpeedInput)
        params_group.setLayout(params_layout)
        main_layout.addWidget(params_group)

        # Connect the value changed signals to update the config
        self.blinkThresholdInput.textChanged.connect(lambda: self.updateConfig('blink_threshold', self.blinkThresholdInput.text()))
        self.blinkDurationInput.textChanged.connect(lambda: self.updateConfig('blink_duration', self.blinkDurationInput.text()))
        self.mouthOpenThresholdInput.textChanged.connect(lambda: self.updateConfig('mouth_open_threshold', self.mouthOpenThresholdInput.text()))
        self.mouthOpenDurationInput.textChanged.connect(lambda: self.updateConfig('mouth_open_duration', self.mouthOpenDurationInput.text()))
        self.tiltThresholdInput.textChanged.connect(lambda: self.updateConfig('tilt_threshold', self.tiltThresholdInput.text()))
        self.scrollSpeedInput.textChanged.connect(lambda: self.updateConfig('scroll_speed', self.scrollSpeedInput.text()))

        # Add some spacing
        main_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.setLayout(main_layout)

        self.face_tracker = FaceTracker(sensitivity=self.sensitivitySlider.value())
        self.face_tracker.finished.connect(self.onTrackingFinished)

        self.speech_to_text = SpeechToText()
        self.speech_to_text.textReady.connect(self.onSpeechRecognized)
        self.speech_to_text.errorOccurred.connect(self.onSpeechError)

    def startTracking(self):
        self.startButton.setEnabled(False)
        self.face_tracker.sensitivity = self.sensitivitySlider.value()
        self.face_tracker.blink_threshold = float(self.blinkThresholdInput.text())
        self.face_tracker.blink_duration = float(self.blinkDurationInput.text())
        self.face_tracker.mouth_open_threshold = int(self.mouthOpenThresholdInput.text())
        self.face_tracker.mouth_open_duration = float(self.mouthOpenDurationInput.text())
        self.face_tracker.tilt_threshold = float(self.tiltThresholdInput.text())
        self.face_tracker.scroll_speed = float(self.scrollSpeedInput.text())
        self.face_tracker.start()

    def onTrackingFinished(self):
        self.startButton.setEnabled(True)

    def openYouTubeVideo(self):
        QDesktopServices.openUrl(QUrl("https://www.youtube.com/watch?v=Em6n8RKEHAk"))

    def updateSensitivity(self, value):
        self.sensitivityLabel.setText(f'Sensitivity: {value}')
        self.face_tracker.sensitivity = value
        self.config_manager.set_value('TRACKING', 'sensitivity', str(value))

    def updateConfig(self, key, value):
        self.config_manager.set_value('TRACKING', key, value)

    def startSpeechToText(self):
        if not self.speech_to_text_active:
            self.speech_to_text_active = True
            self.speakButton.setText("Stop Listening")
            self.speech_to_text.listening = True
            self.speech_to_text.start()
        else:
            self.speech_to_text_active = False
            self.speakButton.setText("Speak")
            self.speech_to_text.stopListening()

    def onSpeechRecognized(self, text):
        pyautogui.typewrite(text)

    def onSpeechError(self, error_message):
        print(f"Speech Recognition Error: {error_message}")
        self.speakButton.setEnabled(True)

    def toggleScrollMode(self):
        self.face_tracker.scroll_mode_active = not self.face_tracker.scroll_mode_active
        status = "enabled" if self.face_tracker.scroll_mode_active else "disabled"
        self.scrollButton.setText(f"Scroll Mode: {status}")