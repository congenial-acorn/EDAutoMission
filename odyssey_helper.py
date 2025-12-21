# odyssey.py
# Originally by Pon Pon
# Now developed by congenial-acorn
# Low level implementation of main script functionalities for Odyssey

import logging
from time import sleep

from pydirectinput import press
from pyautogui import screenshot
from numpy import array
from numpy import sum as array_sum

from helper_functions import screenHeight, screenWidth, ocr_screen_location, slight_random_time

class OdysseyHelper:
    missions_seen = 0
    back_button_original = None

    @classmethod
    def open_missions_board(cls):
        # Note: Starts from starport screen, but ends on mission category board. 
        # Doesn't break anything when starting from mission category board.
        # If it's not broken don't fix it!
        press('space', presses=2, interval=slight_random_time(0.3))
        sleep(5)  # Delay to account for load time

        # Change filter to transport
        press('d', presses=2, interval=slight_random_time(0.3))
        press('space', interval=slight_random_time(0.3))
        sleep(5)  # Delay to account for load time

    @classmethod
    def at_bottom(cls):
        if cls.back_button_original is None:
            cls.back_button_original = array(screenshot(
                region=(
                    int(screenWidth*235/3840),
                    int(screenHeight*1868/2160),
                    int(screenWidth*666/3840),
                    int(screenHeight*90/2160)
                )
            ))
        back_button_new = array(screenshot(
            region=(
                int(screenWidth*235/3840),
                int(screenHeight*1868/2160),
                int(screenWidth*666/3840),
                int(screenHeight*90/2160)
            )
        ))

        # logging.debug("Original:")
        # logging.debug(cls.back_button_original)
        # logging.debug("New:")
        # logging.debug(back_button_new)

        # Calculate the Mean Squared Error between the two images (i.e. the
        # average error between all the pixels). This looks complicated, but it
        # is just taking the square of the difference divided by the total
        # number of pixels in the arrays.
        # See https://pyimagesearch.com/2014/09/15/python-compare-two-images/
        # for a more in-depth explanation
        mse = array_sum((cls.back_button_original.astype("float") - back_button_new.astype("float")) ** 2)/float(cls.back_button_original.shape[0] * back_button_new.shape[1])
        logging.debug("mse = {}".format(mse))
        return mse > 1 #The color of the button changed, return True for at bottom of list.

    @classmethod
    def ocr_mission(cls):
        # Odyssey will not scroll the mission board until the first 6 missions have
        # been iterated over. Therefore, we need to specifically look at the
        # coordinates of the first 6 missions before just looking at the coordinates
        # of the bottom most mission

        # Reference screen size (used to determine relative coords)
        myScreenWidth = 3840
        myScreenHeight = 2160
        # Vertical start coordinate of each of the missions (on the reference screen)
        reference_verts = (888, 1040, 1184, 1336, 1481, 1627, 1683)

        # Actual screen size values
        horiz_start = int(screenWidth*235/myScreenWidth)
        selection_width = int(screenWidth*1563/myScreenWidth)
        selection_height = int(screenHeight*127/myScreenHeight)
        mission_coords = [
            (horiz_start, int(screenHeight*vert/myScreenHeight), selection_width, selection_height) for vert in reference_verts
        ]
        if cls.missions_seen < 6:
            return ocr_screen_location(mission_coords[cls.missions_seen])
        else:
            return ocr_screen_location(mission_coords[6])


    @classmethod
    def check_wing_mission(cls) -> bool:
        from PIL import Image

        myScreenWidth = 3840
        myScreenHeight = 2160

        # Vertical start coordinate of each of wing mission icon locations.
        reference_verts = (980, 1132, 1276, 1428, 1573, 1719, 1775)

        # Actual screen size values
        horiz_start = int(screenWidth*235/myScreenWidth)
        selection_width = int(screenWidth*45/myScreenWidth)
        selection_height = int(screenHeight*40/myScreenHeight)

        if cls.missions_seen < 6:
            mission_coord = (horiz_start, int(screenHeight*reference_verts[cls.missions_seen]/myScreenHeight), selection_width, selection_height)
        else:
            mission_coord = (horiz_start, int(screenHeight*reference_verts[6]/myScreenHeight), selection_width, selection_height)

        # Capture screenshot of the wing icon location
        captured_image = array(screenshot(region=mission_coord))
    
        # Load the reference wing icon and resize to match captured dimensions
        wing_icon = Image.open('wingicon.png').convert('RGB')
        wing_icon_resized = wing_icon.resize((captured_image.shape[1], captured_image.shape[0]))
        wing_icon_array = array(wing_icon_resized)

        # Calculate the Mean Squared Error between the two images
        mse = array_sum((wing_icon_array.astype("float") - captured_image.astype("float")) ** 2) / float(wing_icon_array.shape[0] * wing_icon_array.shape[1])

        logging.debug("Wing mission MSE = {}".format(mse))

        # Return True if images match (low MSE), False otherwise
    
        return mse < 5000
    
    @classmethod
    def accept_mission(cls):
        press('space', presses=2, interval=slight_random_time(0.3))

    @classmethod
    def next_mission(cls):
        cls.missions_seen += 1
        press('s', interval=slight_random_time(0.2))

    @classmethod
    def return_to_starport(cls):
        cls.missions_seen = 0
        cls.back_button_original = None  # Reset this to force a new screenshot for every board refresh
        press('backspace', presses=2, interval=slight_random_time(0.5))

    @classmethod
    def check_missions_accepted(cls):
        
        # Press 1 to open the missions summary and OCR the mission count.
        # Scales coordinates relative to a 3840x2160 reference.
        
        myScreenWidth = 3840
        myScreenHeight = 2160

        press('1', presses=1, interval=slight_random_time(0.3))
        sleep(1)  # Allow UI to update

        x = int(screenWidth * 499 / myScreenWidth)
        y = int(screenHeight * 630 / myScreenHeight)
        width = int(screenWidth * (562 - 499) / myScreenWidth)
        height = int(screenHeight * (658 - 630) / myScreenHeight)

        mission_text = ocr_screen_location((x, y, width, height))
        logging.debug("OCR mission count text: %s", mission_text)

        digits = "".join(ch for ch in mission_text if ch.isdigit())
        if not digits:
            logging.debug("No digits found in mission count OCR text")
            return 0

        try:
            return int(digits)
        except ValueError:
            logging.debug("Failed to parse mission count from digits: %s", digits)
            return 0

# Run as script for debug only
if __name__ == "__main__":
    import helper_functions
    sleep(5)
    helper_functions.module_setup()
    OdysseyHelper.check_missions_accepted()
