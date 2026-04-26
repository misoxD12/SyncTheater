import sys
import threading
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PyQt6.QtCore import pyqtSignal, QObject, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from websockets.sync.client import connect

class WorkerSignals(QObject):
    new_message = pyqtSignal(str)

class SyncTheaterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SyncTheater - Watch Party")
        self.setGeometry(100, 100, 800, 600) # Made the window bigger for the video!

        # --- UI Setup ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 1. The Video Screen (The TV)
        self.video_widget = QVideoWidget()
        layout.addWidget(self.video_widget)

        # 2. The Buttons (The Remote Control)
        self.pause_btn = QPushButton("⏸️ Send PAUSE")
        self.play_btn = QPushButton("▶️ Send PLAY")
        layout.addWidget(self.pause_btn)
        layout.addWidget(self.play_btn)

        # 3. The VCR Engine (Invisible video player)
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput() # Need this so we can hear it
        self.player.setAudioOutput(self.audio_output)
        
        # 4. Plug the VCR into the TV
        self.player.setVideoOutput(self.video_widget)

        # 5. Insert the Movie (CHANGE THIS IF YOUR FILE IS NAMED DIFFERENTLY)
        video_path = os.path.join(os.getcwd(), "test.mp4")
        self.player.setSource(QUrl.fromLocalFile(video_path))

        # --- Networking Setup ---
        self.tunnel = None 
        self.signals = WorkerSignals()
        
        # When the walkie-talkie beeps, run the video command!
        self.signals.new_message.connect(self.execute_sync_command) 

        self.pause_btn.clicked.connect(self.send_pause)
        self.play_btn.clicked.connect(self.send_play)

        threading.Thread(target=self.background_listener, daemon=True).start()

    # --- The Actions ---
    def send_pause(self):
        if self.tunnel:
            self.tunnel.send("PAUSE")
            self.player.pause() # Pause our own video immediately

    def send_play(self):
        if self.tunnel:
            self.tunnel.send("PLAY")
            self.player.play() # Play our own video immediately

    def execute_sync_command(self, command):
        # The background worker told us what the server said. Let's do it!
        if command == "PAUSE":
            self.player.pause()
        elif command == "PLAY":
            self.player.play()

    # --- The Background Worker ---
    def background_listener(self):
        with connect("wss://jaywalker-salvation-financial.ngrok-free.dev") as websocket:
            self.tunnel = websocket
            while True:
                incoming_msg = websocket.recv() 
                self.signals.new_message.emit(incoming_msg) 

app = QApplication(sys.argv)
window = SyncTheaterApp()
window.show()
sys.exit(app.exec())