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
        self.chosen_num = ""
        self.button_list = self.buttons.findChildren(QtWidgets.QPushButton)
        self.song_labels = self.findChildren(QtWidgets.QLabel, QtCore.QRegularExpression("^song"))
        self.timers = []
        self.page_load()
        # Connect buttons
        for button in self.button_list:
            button.clicked.connect(partial(self.button_click, button))
        self.playing = False
    
    def page_load(self):
        self.text_reset()
        song_titles = [song.title for song in self.pages[self.active_page].tracks]
        for i,title in enumerate(song_titles):
            label = self.findChild(QtWidgets.QLabel, name=f"song{i}")
            label.setText(title + " ")
            label.adjustSize()
            scrollbar = label.parentWidget().parentWidget().parentWidget().horizontalScrollBar()
            scrollbar.hide()
            if len(title) > 11:
                scrollbar.setMaximum(label.width()-label.parentWidget().parentWidget().parentWidget().width())
                self.stop_text_scroll(scrollbar)
        

    def text_reset(self):
        for label in self.song_labels:
            label.setText("")

    def start_text_scroll(self, scrollbar, maximum):
        scrollbar.setValue(scrollbar.value() + 20)
        if scrollbar.value() < maximum:
            timer = QtCore.QTimer()
            timer.setInterval(500)
            timer.setSingleShot(True)
            timer.timeout.connect(partial(self.start_text_scroll, scrollbar, max))
            timer.start()
            self.timers.append(timer)
        else:
            timer = QtCore.QTimer()
            timer.setInterval(3000)
            timer.setSingleShot(True)
            timer.timeout.connect(partial(self.stop_text_scroll, scrollbar))
            timer.start()
            self.timers.append(timer)
        

    def stop_text_scroll(self, scrollbar):
        scrollbar.setValue(0)
        timer = QtCore.QTimer()
        timer.setInterval(3000)
        timer.setSingleShot(True)
        timer.timeout.connect(partial(self.start_text_scroll, scrollbar, scrollbar.maximum()))
        self.timers.append(timer)
        timer.start()
        

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
                if chosen_track > len(self.pages[self.active_page].tracks) or chosen_track < 0:
                    self.button_reset()
                elif chosen_track==0:
                    if self.playing:
                        request("PUT", "https://api.spotify.com/v1/me/player/pause")
                        self.playing = False
                    else:
                        request("PUT", "https://api.spotify.com/v1/me/player/play")
                        self.playing = True
                    self.button_reset()
                else:
                    self.pages[self.active_page].tracks[chosen_track-1].play()
                    self.playing = True
                    self.button_reset()
        else:
            self.clear_timers()
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

    def clear_timers(self):
        for timer in self.timers:
            timer.stop()
        self.timers = []

                


app = QtWidgets.QApplication(sys.argv)

window = MainWindow()
window.show()
app.exec()