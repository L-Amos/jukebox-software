"""Prototype for jukebox interface.

Displays a rough interface in a picture of the jukebox frontage. Includes clickable buttons and scrolling
song names.
"""
from math import ceil
from requests.exceptions import ReadTimeout
import subprocess
from functools import partial
from collections.abc import Callable
import sys
import pigpio
from PySide6 import QtWidgets, QtCore
sys.path.append("../")  # Allows for below imports
from app.app_ui import Ui_MainWindow
from src.jukebox import Page
from src.utils import request, PLAYLIST_ID, SONGS_PER_PAGE

BUTTONS = {
    19: 1,
    13: 2,
    22: 3,
    23: 4,
    12: 5,
    6: "backward",
    26: 6,
    7: 7,
    5: 8,
    11: 9,
    8: 0,
    25: "forward"
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
        self.timers = QtCore.QObject()
        self.playing = False
        self.off = False
        self.create_pages()
        self.active_page = 0
        self.pages[self.active_page].refresh()
        self.page_load()
        self.chosen_num = ""
        # Connect buttons to button_click function
        for button in self.button_list:
            button.clicked.connect(partial(self.button_click, button))

    def create_pages(self):
        """Create pages of songs.
        """
        try:    
            num_songs = request("GET", f"https://api.spotify.com/v1/playlists/{PLAYLIST_ID}")["tracks"]["total"]
        except ReadTimeout:
            create_pages()
        num_pages = ceil(num_songs/SONGS_PER_PAGE)
        self.pages = [Page(PLAYLIST_ID, i) for i in range(num_pages)]
    
    def page_load(self):
        """Loads and displays the currently-selected page.
        """
        self.text_reset()
        self.chosen_num = ""
        song_titles = [song.title for song in self.pages[self.active_page].tracks]
        for i,title in enumerate(song_titles):
            # Change the text of each label to the appropriate song title
            label = self.findChild(QtWidgets.QLabel, name=f"song{i}")
            label.setText(title + " ")
            label.adjustSize()  # Needed for the scrollbar to work properly
            # Set up the label's scrollbar
            scrollbar = label.parentWidget().parentWidget().parentWidget().horizontalScrollBar()
            scrollbar.hide()
            scrollbar_width = label.width()-label.parentWidget().parentWidget().parentWidget().width()
            if scrollbar_width > 0:
                scrollbar.setMaximum(scrollbar_width)  # Set maximum value (for some reason it doesn't automatically set it properly)
                self.stop_text_scroll(scrollbar)

    def text_reset(self):
        """Clears all song titles from the screen.
        """
        for label in self.song_labels:
            label.setText("")

    def create_oneshot_timer(self, time : int):
        """Creates a oneshot timer, links it to a callable and adds it to the list of timers.

        :param time: how long the timer should last
        :type time: int
        :param bind: function to call when the timer is done
        :type bind: Callable
        """
        timer = QtCore.QTimer(self.timers)
        timer.setInterval(time)
        timer.setSingleShot(True)
        return timer

    def start_text_scroll(self, scrollbar : QtWidgets.QScrollBar, old_timer : QtCore.QTimer = None):
        """Starts scrolling the songnames of the labels.

        :param scrollbar: scrollbar attached to the label
        :type scrollbar: QtWidgets.QScrollBar
        """
        if old_timer:
            old_timer.setParent(None)
            old_timer.deleteLater()
        scrollbar.setValue(scrollbar.value() + 20)
        if scrollbar.value() < scrollbar.maximum():
            timer = self.create_oneshot_timer(500)
            timer.timeout.connect(partial(self.start_text_scroll, scrollbar, timer))
        else:
            timer = self.create_oneshot_timer(3000)
            timer.timeout.connect(partial(self.stop_text_scroll, scrollbar, timer))
        timer.start()

    def stop_text_scroll(self, scrollbar : QtWidgets.QScrollBar, old_timer : QtCore.QTimer = None):
        """Resets label scrolling before beginning scroll again after 3 seconds.

        :param scrollbar: scrollbar attached to the label
        :type scrollbar: QtWidgets.QScrollBar
        """
        if old_timer:
            old_timer.setParent(None)
            old_timer.deleteLater()
        scrollbar.setValue(0)
        timer = self.create_oneshot_timer(3000)
        timer.timeout.connect(partial(self.start_text_scroll, scrollbar, timer))
        timer.start()

    # Clicked Buttons
    def button_click(self, button : QtWidgets.QPushButton):
        """Handles button push event on main interface.

        :param button: button that has been pushed
        :type button: QtWidgets.QPushButton
        """
        if self.off:
            subprocess.call(['sh', '../../screen_on.sh'])
            self.off = False
            return
        # Case where numbered button is pressed
        if button.text():
            self.chosen_num += button.text()
            if len(self.chosen_num)==2:
                chosen_track = int(self.chosen_num)
                # Reset buttons without doing anything if invalid number inputted
                if chosen_track==69:
                    self.close()
                elif chosen_track==99:
                    subprocess.call(['sh', '../../screen_off.sh'])
                    self.off = True
                # Pause/play if 00 entered
                elif chosen_track==0:
                    if self.playing:
                        request("PUT", "https://api.spotify.com/v1/me/player/pause")
                        self.playing = False
                    else:
                        request("PUT", "https://api.spotify.com/v1/me/player/play")
                        self.playing = True
                elif chosen_track >= len(self.pages[self.active_page].tracks):
                    pass
                else:
                    self.pages[self.active_page].tracks[chosen_track-1].play()
                    self.playing = True
                self.chosen_num = ""
        # Case where page forward/backward button is pressed
        else:
            self.clear_timers()
            if "forward" in button.objectName():
                self.active_page += 1
                if self.active_page == len(self.pages):
                    self.create_pages()
                if self.active_page >= len(self.pages):
                    self.active_page = 0   
            else:
                self.active_page -= 1
                if self.active_page < 0:
                    self.create_pages()
                    self.active_page = len(self.pages)-1
                    self.page_load()
                    return
            self.pages[self.active_page].refresh()
            self.page_load()
    
    def clear_timers(self):
        """Stops and destroys all currently-active timers.
        """
        self.timers.deleteLater()
        self.timers = QtCore.QObject()
    
    def gpio_press(self, button, _,_2):
        """Handles pressing of GPIO buttons.
        """
        pressed = BUTTONS[button]
        pressed_button = next(button for button in self.button_list if str(pressed) in button.objectName())
        pressed_button.click()


# Set up GPIO
pi = pigpio.pi()
for button in BUTTONS:
    pi.set_mode(button, pigpio.INPUT)
    pi.set_pull_up_down(button, pigpio.PUD_UP)
    pi.set_glitch_filter(button, 1000)  # Deals with switch bounce

app = QtWidgets.QApplication(sys.argv)

window = MainWindow()
# Connect buttons to functions
for button in BUTTONS:
    pi.callback(button, func=window.gpio_press)

window.show()
app.exec()
