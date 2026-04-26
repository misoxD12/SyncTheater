import sys
import threading
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QTextEdit
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
        self.setGeometry(100, 100, 1000, 600) # Made window wider to fit the console

        # --- The File Setup ---
        # We save the exact filename here so the whole app can check it later
        self.my_filename = "test.mp4" 
        self.video_path = os.path.join(os.getcwd(), self.my_filename)

        # --- UI Setup (Horizontal Split) ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main Layout is now Horizontal (Left: TV, Right: Console)
        main_layout = QHBoxLayout(central_widget) 

        # --- Left Side: The TV and Remote ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        self.video_widget = QVideoWidget()
        self.pause_btn = QPushButton("⏸️ Send PAUSE")
        self.play_btn = QPushButton("▶️ Send PLAY")
        
        left_layout.addWidget(self.video_widget)
        left_layout.addWidget(self.pause_btn)
        left_layout.addWidget(self.play_btn)

        # --- Right Side: The System Console ---
        self.console = QTextEdit()
        self.console.setReadOnly(True) # So users can't type in it accidentally
        self.console.setFixedWidth(300) # Lock the width so it doesn't squish the video
        self.console.setStyleSheet("background-color: #1e1e1e; color: #00ff00; font-family: Consolas;") # Cool hacker styling
        
        # Add both sides to the main window
        main_layout.addWidget(left_panel)
        main_layout.addWidget(self.console)

        # --- The VCR Engine ---
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput() 
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.video_widget)
        self.player.setSource(QUrl.fromLocalFile(self.video_path))

        # Initialize the console with system info
        self.log_to_console(f"SYSTEM: Booting SyncTheater...")
        self.log_to_console(f"SYSTEM: Loaded local file '{self.my_filename}'")

        # --- Networking Setup ---
        self.tunnel = None 
        self.signals = WorkerSignals()
        self.signals.new_message.connect(self.execute_sync_command) 
        self.pause_btn.clicked.connect(self.send_pause)
        self.play_btn.clicked.connect(self.send_play)

        threading.Thread(target=self.background_listener, daemon=True).start()

    # --- Custom Logging Tool ---
    def log_to_console(self, text):
        self.console.append(text) # Prints a new line to our visual text box

    # --- The Actions ---
    def send_pause(self):
        if self.tunnel:
            self.tunnel.send("PAUSE")
            self.player.pause() 
            self.log_to_console("You: Paused the video.")

    def send_play(self):
        if self.tunnel:
            self.tunnel.send("PLAY")
            self.player.play() 
            self.log_to_console("You: Played the video.")

    def execute_sync_command(self, command):
        # 1. Handle Play/Pause
        if command == "PAUSE":
            self.player.pause()
            self.log_to_console("Network: Video Paused.")
        elif command == "PLAY":
            self.player.play()
            self.log_to_console("Network: Video Playing.")
            
        # 2. Handle File Verification Handshake
        elif command.startswith("FILE:"):
            # Split "FILE:test.mp4" into two pieces and grab the filename
            their_file = command.split(":")[1] 
            
            if their_file == self.my_filename:
                self.log_to_console(f"✅ Network: A user joined with correct file ({their_file})")
            else:
                self.log_to_console(f"⚠️ WARNING: User joined with wrong file! They have '{their_file}' instead of '{self.my_filename}'!")

    # --- The Background Worker ---
    def background_listener(self):
        # MAKE SURE TO PUT YOUR NGROK LINK HERE
        with connect("wss://jaywalker-salvation-financial.ngrok-free.dev") as websocket:
            self.tunnel = websocket
            
            # The exact moment we connect, broadcast our file name to the room!
            self.tunnel.send(f"FILE:{self.my_filename}")
            
            while True:
                incoming_msg = websocket.recv() 
                self.signals.new_message.emit(incoming_msg) 

app = QApplication(sys.argv)
window = SyncTheaterApp()
window.show()
sys.exit(app.exec())