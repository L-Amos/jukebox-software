"""Prototype for jukebox interface.

Displays a rough interface in a picture of the jukebox frontage. Includes clickable buttons and scrolling
song names.
"""
from math import ceil
from functools import partial
from collections.abc import Callable
import sys
import pigpio
from PySide6 import QtWidgets, QtCore
sys.path.append("../")  # Allows for below imports
from interface_prototype.app_ui import Ui_MainWindow
from src.jukebox import Page
from src.utils import request, PLAYLIST_ID, SONGS_PER_PAGE

BUTTONS = {
    2: 1,
    3: 2,
    4: 3,
    17: 4,
    27: 5,
    22: "forward",
    14: 6,
    15: 7,
    18: 8,
    23: 9,
    24: 0,
    25: "backward"
}

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    """Main GUI window.
    """
    def __init__(self):
        super().__init__()
        self.setupUi(self)  # Creates ui based on app_ui.py
        self.chosen_num = ""
        self.button_list = self.buttons.findChildren(QtWidgets.QPushButton)
        self.song_labels = self.findChildren(QtWidgets.QLabel, QtCore.QRegularExpression("^song"))
        self.timers = []
        self.playing = False
        # Create Pages
        num_songs = request("GET", f"https://api.spotify.com/v1/playlists/{PLAYLIST_ID}")["tracks"]["total"]
        num_pages = ceil(num_songs/SONGS_PER_PAGE)
        self.pages = [Page(PLAYLIST_ID, i) for i in range(num_pages)]
        self.active_page = 0
        self.pages[self.active_page].refresh()
        self.page_load()
        self.chosen_num = ""
        # Connect buttons to button_click function
        for button in self.button_list:
            button.clicked.connect(partial(self.button_click, button))
            button.hide()

    def page_load(self):
        """Loads and displays the currently-selected page.
        """
        self.text_reset()
        song_titles = [song.title for song in self.pages[self.active_page].tracks]
        for i,title in enumerate(song_titles):
            # Change the text of each label to the appropriate song title
            label = self.findChild(QtWidgets.QLabel, name=f"song{i}")
            label.setText(title + " ")
            label.adjustSize()  # Needed for the scrollbar to work properly
            # Set up the label's scrollbar
            scrollbar = label.parentWidget().parentWidget().parentWidget().horizontalScrollBar()
            scrollbar.hide()
            if len(title) > 11:
                scrollbar.setMaximum(label.width()-label.parentWidget().parentWidget().parentWidget().width())  # Calculate maximum value (as for some reason it doesn't report it properly)
                self.stop_text_scroll(scrollbar)

    def text_reset(self):
        """Clears all song titles from the screen.
        """
        for label in self.song_labels:
            label.setText("")

    def create_oneshot_timer(self, time : int, bind : Callable):
        """Creates a oneshot timer, links it to a callable and adds it to the list of timers.

        :param time: how long the timer should last
        :type time: int
        :param bind: function to call when the timer is done
        :type bind: Callable
        """
        timer = QtCore.QTimer()
        timer.setInterval(time)
        timer.setSingleShot(True)
        timer.timeout.connect(bind)
        timer.start()
        self.timers.append(timer)

    def start_text_scroll(self, scrollbar : QtWidgets.QScrollBar):
        """Starts scrolling the songnames of the labels.

        :param scrollbar: scrollbar attached to the label
        :type scrollbar: QtWidgets.QScrollBar
        """
        scrollbar.setValue(scrollbar.value() + 20)
        if scrollbar.value() < scrollbar.maximum():
            self.create_oneshot_timer(500, partial(self.start_text_scroll, scrollbar))
        else:
            self.create_oneshot_timer(3000, partial(self.stop_text_scroll, scrollbar))

    def stop_text_scroll(self, scrollbar : QtWidgets.QScrollBar):
        """Resets label scrolling before beginning scroll again after 3 seconds.

        :param scrollbar: scrollbar attached to the label
        :type scrollbar: QtWidgets.QScrollBar
        """
        scrollbar.setValue(0)
        self.create_oneshot_timer(3000, partial(self.start_text_scroll, scrollbar))

    def button_reset(self):
        """Resets the state of the buttons.
        """
        for button in self.button_list:
            button.setStyleSheet("background-color: qradialgradient(spread:pad, cx:0.5, cy:0.5, radius:0.5, fx:0.5, fy:0.5, stop:0 rgba(255, 235, 235, 206), stop:0.35 rgba(255, 188, 188, 80), stop:0.4 rgba(255, 162, 162, 80), stop:0.425 rgba(255, 132, 132, 156), stop:0.44 rgba(252, 128, 128, 80), stop:1 rgba(255, 255, 255, 0));\n"
"border-radius: 15px;")
        self.chosen_num = ""

    # Clicked Buttons
    def button_click(self, button : QtWidgets.QPushButton):
        """Handles button push event on main interface.

        :param button: button that has been pushed
        :type button: QtWidgets.QPushButton
        """
        # Paint the pressed button red
        button.setStyleSheet("background-color: rgb(255,0,0);\nborder-radius: 15px;")
        button.repaint()
        # Case where numbered button is pressed
        if button.text():
            self.chosen_num += button.text()
            if len(self.chosen_num)==2:
                chosen_track = int(self.chosen_num)
                # Reset buttons without doing anything if invalid number inputted
                if chosen_track > len(self.pages[self.active_page].tracks) or chosen_track < 0:
                    self.button_reset()
                # Pause/play if 00 entered
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
        # Case where page forward/backward button is pressed
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
        """Stops and destroys all currently-active timers.
        """
        for timer in self.timers:
            timer.stop()
        self.timers = []
    
    def gpio_press(self, button, _,_2):
        pressed = BUTTONS[button]
        pressed_button = next(button for button in self.button_list if str(pressed) in button.objectName())
        pressed_button.click()

app = QtWidgets.QApplication(sys.argv)

window = MainWindow()
# GPIO
pi = pigpio.pi()
# Connect buttons to functions
for button in BUTTONS:
    pi.set_glitch_filter(button, 1000)  # Deals with switch bounce
    pi.callback(button, func=window.gpio_press)

window.show()
app.exec()
