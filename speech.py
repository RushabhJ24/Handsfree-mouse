from PyQt5.QtCore import QThread, pyqtSignal
import speech_recognition as sr

class SpeechToText(QThread):
    textReady = pyqtSignal(str)
    errorOccurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.listening = True

    def run(self):
        r = sr.Recognizer()
        with sr.Microphone() as source:
            r.pause_threshold = 0.8
            while self.listening:
                try:
                    print("Listening for speech...")
                    audio = r.listen(source, timeout=None, phrase_time_limit=10)
                    try:
                        text = r.recognize_google(audio)
                        self.textReady.emit(text)
                    except sr.UnknownValueError:
                        print("No speech detected, continuing...")
                    except sr.RequestError as e:
                        self.errorOccurred.emit(f"Could not request results from Google Speech Recognition service; {e}")
                except Exception as e:
                    self.errorOccurred.emit(f"An error occurred: {str(e)}")

    def stopListening(self):
        self.listening = False