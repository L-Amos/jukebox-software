import sys
sys.path.append("../")
from PySide6 import QtWidgets, QtCore

from app.app_ui import Ui_MainWindow
from functools import partial

from math import ceil

from src.jukebox import PLAYLIST_ID, SONGS_PER_PAGE, Page
from src.utils import request

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        # Get Page
        num_songs = request("GET", f"https://api.spotify.com/v1/playlists/{PLAYLIST_ID}")["tracks"]["total"]
        num_pages = ceil(num_songs/SONGS_PER_PAGE)
        self.pages = [Page(PLAYLIST_ID, i) for i in range(num_pages)]
        self.active_page = 0
        self.pages[self.active_page].refresh()
        self.pages[self.active_page].display()
        self.chosen_num = ""
        self.button_list = self.buttons.findChildren(QtWidgets.QPushButton)
        self.song_labels = self.findChildren(QtWidgets.QLabel, QtCore.QRegularExpression("^song"))
        self.page_load()
        # Connect buttons
        for button in self.button_list:
            button.clicked.connect(partial(self.button_click, button))
    
    def page_load(self):
        self.text_reset()
        song_titles = [song.title for song in self.pages[self.active_page].tracks]
        for i,title in enumerate(song_titles):
            label = self.findChild(QtWidgets.QLabel, name=f"song{i}")
            label.setText(f"{i+1:02}: {title}")

    def text_reset(self):
        for label in self.song_labels:
            label.setText("")

    def button_reset(self):
        for button in self.button_list:
            button.setStyleSheet(u"background-color: qradialgradient(spread:pad, cx:0.5, cy:0.5, radius:0.5, fx:0.5, fy:0.5, stop:0 rgba(255, 235, 235, 206), stop:0.35 rgba(255, 188, 188, 80), stop:0.4 rgba(255, 162, 162, 80), stop:0.425 rgba(255, 132, 132, 156), stop:0.44 rgba(252, 128, 128, 80), stop:1 rgba(255, 255, 255, 0));\n"
"border-radius: 15px;")
        self.chosen_num = ""

    # Clicked Buttons
    def button_click(self, button):
        button.setStyleSheet("background-color: rgb(255,0,0);\n""border-radius: 15px;")
        button.repaint()
        if button.text():
            self.chosen_num += button.text()
            if len(self.chosen_num)==2:
                chosen_track = int(self.chosen_num)
                if chosen_track > len(self.pages[self.active_page].tracks) or chosen_track < 1:
                    self.button_reset()
                else:
                    self.pages[self.active_page].tracks[chosen_track-1].play()
                    self.button_reset()
        else:
            if "forward" in button.objectName():
                self.active_page += 1
                if self.active_page >= len(self.pages):
                    self.active_page = 0       
            else:
                self.active_page -= 1
                if self.active_page < 0:
                    self.active_page = len(self.pages)-1
            self.pages[self.active_page].refresh()
            self.page_load()
            self.button_reset()

                


app = QtWidgets.QApplication(sys.argv)

window = MainWindow()
window.show()
app.exec()