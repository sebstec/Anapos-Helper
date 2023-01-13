"""
Screen Resolution should be 4K (3840x2160) otherwise adjustments in the code are neccessary
"""

from pywinauto.application import Application
import pyautogui
from pynput import keyboard
from pynput import mouse
from pynput.mouse import Controller, Button
from PIL import Image
from PIL import ImageStat
from PIL import ImageGrab
from PIL import ImageStat
from PIL import ImageChops
from PIL import ImageTk
from PIL import ImageEnhance
from PIL import ImageFilter
from PIL import ImageDraw
import time
import tkinter as tk
from tkinter import StringVar, filedialog, BooleanVar
from tkinter import messagebox as mb
import numpy as np
import ctypes
import json
import threading
from functools import partial

try:  # Windows 8.1 and later
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception as e:
    pass


def get_curr_screen_geometry():
    """
    Workaround to get the size of the current screen in a multi-screen setup.

    Returns:
        geometry (str): The standard Tk geometry string.
            [width]x[height]+[left]+[top]
    """
    root = tk.Tk()
    root.update_idletasks()
    root.attributes('-fullscreen', True)
    root.state('iconic')
    #geometry = root.winfo_geometry()
    geometry_x = root.winfo_width()
    geometry_y = root.winfo_height()
    #geometry_sx = root.winfo_screenwidth()
    #geometry_sy = root.winfo_screenheight()
    root.destroy()
    return geometry_x, geometry_y


"""Settings"""
brute_x_max = 0.10  #0.25
brute_y_max = 0.10  #0.25
brute_angle_max = 0.03  #0.03
brute_height_max = 0.10  #0.15
brute_deviation_increment = 0.01  #0.01
#3s each Increment

level_threshold_top = 120
level_threshold_bottom = 60
increase_height_diff_threshold_button = "Button2"
decrease_height_diff_threshold_button = "Button3"
height_diff_threshold_static = "Static0"
x_direction_shift_input = "XWindowsForms10.Window.8.app.0.134c08f_r12_ad11"
y_direction_shift_input = "YWindowsForms10.Window.8.app.0.134c08f_r12_ad11"
app_title_regex = ".*Vergleichsbild.*"
neig_title_regex = "Neig.ausr. festl."
app_class_name = "WindowsForms10.Window.8.app.0.134c08f_r12_ad1"
height_diff_show_button = "Höhendifferenz-Anz."
height_diff_dialog_title = "Höhenanzeige einstellen"
height_diff_settings_button = "Einstellungen...Button1"
height_diff_settings_scheme_colorpalette = "WindowsForms10.Window.8.app.0.134c08f_r12_ad119"
height_diff_settings_scheme_colorpalette_gray = (
    "WindowsForms10.Window.8.app.0.134c08f_r12_ad125")
height_diff_settings_ok_button = "OKButton"
manual_adjust_dialog_button = "Man. Anpassen..."
manual_adjust_dialog_title = "Manuell anpassen"
detail_pos_shift_dialog_dropdown = "Detaillierte Positionsausr.WindowsForms10.Window.8.app.0.134c08f_r12_ad1"
niveau_title_regex = "NivExtrakt"
niveau_button = "Niveau"
tolerance_setting_edit = "Toleranz einstellenEdit"
tolerance_setting = "0,1"
set_niveau_coordinates = (3030, 85)
set_niveau_expand_button = "StreckungButton"
set_niveau_ok_button = "OKButton"
zoom_combobox = "ZoomComboBox"
manual_adjust_image_view = "AnsichtWindowsForms10.Window.8.app.0.134c08f_r12_ad19"
neig_image_view = "AnsichtWindowsForms10.Window.8.app.0.134c08f_r12_ad13"
neig_settings_button = "Einstellungen...Button4"
neig_area_delete_button = "Button10"
neig_area_recover_button = "Button8"
angle_shift_input = "DrehenEdit"
height_shift_input = "HöheEdit"
neig_abort_button = "AbbrechenButton"
screenwidth, screenheight = get_curr_screen_geometry()
window_size = {"width": 422, "height": 600}
window_pos = {
    "posx": screenwidth - window_size["width"] - 20,
    "posy": (screenheight - window_size["height"]) - 400
}
window_geometry = "{0}x{1}+{2}+{3}".format(window_size["width"],
                                           window_size["height"],
                                           window_pos["posx"],
                                           window_pos["posy"])
"""global variables"""
chooseImage_flag = True
"""Functions"""


def adjustDifferenceView(current_level, app, ground_image, mask_image):
    can_continue = False
    while not (can_continue):
        current_level_temp = current_level
        if current_level > level_threshold_top:
            app[app_title_regex][increase_height_diff_threshold_button].click()
            can_continue = False
        elif current_level < level_threshold_bottom:
            app[app_title_regex][decrease_height_diff_threshold_button].click()
            can_continue = False
        else:
            can_continue = True
        while (current_level == current_level_temp and not can_continue):
            time.sleep(0.01)
            current_level = getCurrentLevel(ground_image, mask_image)
    return current_level


def getCurrentLevel(ground_image,
                    mask_image,
                    show_image=False,
                    x=None,
                    y=None,
                    height=None,
                    angle=None,
                    fov=None):
    ss = grabAndCropSS()
    final_image = makeFinalImage(ss, ground_image, mask_image)
    current_stats = ImageStat.Stat(final_image).mean
    current_level = (abs(current_stats[1] - 254) +
                     abs(current_stats[0] - 254) + abs(current_stats[2] - 255))
    if show_image:
        d = ImageDraw.Draw(final_image)
        d.multiline_text(
            (10,
             10),
            "level:\n{0}\nfov:\n{1}\nx:\n{2}\ny:\n{3}\nheight:\n{4}\nangle:\n{5}"
            .format(current_level,
                    fov,
                    x,
                    y,
                    height,
                    angle),
            fill=(0,
                  0,
                  0))
        final_image.show()
    return current_level


def testInOneDirection(app,
                       ground_image,
                       mask_image,
                       deviation_increment,
                       max_num_increments,
                       best_mean,
                       direction,
                       sign):
    current_level = getCurrentLevel(ground_image, mask_image)

    if (direction == "x"):
        app[manual_adjust_dialog_title][
            x_direction_shift_input].double_click_input()
    elif (direction == "y"):
        app[manual_adjust_dialog_title][
            y_direction_shift_input].double_click_input()
    elif (direction == "angle"):
        app[manual_adjust_dialog_title][angle_shift_input].double_click_input()
    elif (direction == "height"):
        app[manual_adjust_dialog_title][height_shift_input].double_click_input(
        )

    pyautogui.hotkey('ctrl', 'a')
    #time.sleep(0.1)  #TODO: improve
    pyautogui.hotkey('ctrl', 'c')
    root = tk.Tk()
    root.withdraw()
    current_deviation_string = root.clipboard_get()
    current_deviation = float(current_deviation_string.replace(",", "."))
    while (current_level <= best_mean and max_num_increments >= 0):
        current_level = adjustDifferenceView(current_level,
                                             app,
                                             ground_image,
                                             mask_image)
        best_mean = current_level
        max_num_increments -= 1

        if (sign == "up"):
            current_deviation = current_deviation + deviation_increment
        elif (sign == "down"):
            current_deviation = current_deviation - deviation_increment

        current_deviation = round(current_deviation, 2)
        current_deviation_string = str(current_deviation).replace(".", ",")

        if (direction == "x"):
            app[manual_adjust_dialog_title][
                x_direction_shift_input].double_click_input()
        elif (direction == "y"):
            app[manual_adjust_dialog_title][
                y_direction_shift_input].double_click_input()
        elif (direction == "angle"):
            app[manual_adjust_dialog_title][
                angle_shift_input].double_click_input()
        elif (direction == "height"):
            app[manual_adjust_dialog_title][
                height_shift_input].double_click_input()

        pyautogui.hotkey('ctrl', 'a')
       #time.sleep(0.1)  #TODO: improve
        pyautogui.write(current_deviation_string)
        pyautogui.press('enter')
        while (current_level == best_mean):
            time.sleep(0.01)
            current_level = getCurrentLevel(ground_image, mask_image)
    if (sign == "up"):
        current_deviation = current_deviation - deviation_increment
    elif (sign == "down"):
        current_deviation = current_deviation + deviation_increment

    current_deviation = round(current_deviation, 2)
    current_deviation_string = str(current_deviation).replace(".", ",")

    if (direction == "x"):
        app[manual_adjust_dialog_title][
            x_direction_shift_input].double_click_input()
    elif (direction == "y"):
        app[manual_adjust_dialog_title][
            y_direction_shift_input].double_click_input()
    elif (direction == "angle"):
        app[manual_adjust_dialog_title][angle_shift_input].double_click_input()
    elif (direction == "height"):
        app[manual_adjust_dialog_title][height_shift_input].double_click_input(
        )

    pyautogui.hotkey('ctrl', 'a')
    #time.sleep(0.1)  #TODO: improve
    pyautogui.write(current_deviation_string)
    pyautogui.press('enter')
    while (current_level != best_mean):
        time.sleep(0.01)
        current_level = getCurrentLevel(ground_image, mask_image)
    root.destroy()
    return current_level


def find_indices(list_to_check, item_to_find):
    return [
        idx for idx,
        value in enumerate(list_to_check) if value == item_to_find
    ]


def testInOneDirectionBrute(app,
                            ground_image,
                            mask_image,
                            brute_deviation_increment,
                            direction,
                            sign,
                            result,
                            x,
                            y,
                            angle,
                            height):
    current_level = getCurrentLevel(ground_image, mask_image)

    if (direction == "x"):
        current_deviation = x
    elif (direction == "y"):
        current_deviation = y
    elif (direction == "angle"):
        current_deviation = angle
    elif (direction == "height"):
        current_deviation = height

    current_level_temp = current_level
    if (sign == "up"):
        current_deviation = current_deviation + brute_deviation_increment
    elif (sign == "down"):
        current_deviation = current_deviation - brute_deviation_increment
    current_deviation = round(current_deviation, 2)
    current_deviation_string = str(current_deviation).replace(".", ",")
    if (direction == "x"):
        app[manual_adjust_dialog_title][
            x_direction_shift_input].double_click_input()
        x = current_deviation
    elif (direction == "y"):
        app[manual_adjust_dialog_title][
            y_direction_shift_input].double_click_input()
        y = current_deviation
    elif (direction == "angle"):
        app[manual_adjust_dialog_title][angle_shift_input].double_click_input()
        angle = current_deviation
    elif (direction == "height"):
        app[manual_adjust_dialog_title][height_shift_input].double_click_input(
        )
        height = current_deviation
    pyautogui.hotkey('ctrl', 'a')
    #time.sleep(0.1)  #TODO: improve
    pyautogui.write(current_deviation_string)
    pyautogui.press('enter')
    while (current_level == current_level_temp):
        time.sleep(0.01)
        current_level = getCurrentLevel(ground_image, mask_image)
    if len(result["best_levels"]) >= result["best_levels_length"]:
        best_levels_worst = max(result["best_levels"])
        if current_level < best_levels_worst:
            result["best_levels"].remove(best_levels_worst)
            result["best_levels"].append(current_level)
            result["best_levels[{0}]_pos".format(
                current_level
            )] = "x: {0:+.2f} y:{1:+.2f} angle:{2:+.2f} height:{3:+.2f}".format(
                x,
                y,
                angle,
                height)
    else:
        result["best_levels"].append(current_level)
        result["best_levels[{0}]_pos".format(
            current_level
        )] = "x: {0:+.2f} y:{1:+.2f} angle:{2:+.2f} height:{3:+.2f}".format(
            x,
            y,
            angle,
            height)

    return result


def getStartPos(app, result, ground_image, mask_image):
    root = tk.Tk()
    root.withdraw()

    app[manual_adjust_dialog_title][
        x_direction_shift_input].double_click_input()
    pyautogui.hotkey('ctrl', 'a')
    #time.sleep(0.1)  #TODO: improve
    pyautogui.hotkey('ctrl', 'c')
    current_deviation_string = root.clipboard_get()
    current_deviation = float(current_deviation_string.replace(",", "."))
    result["x_start"] = current_deviation

    app[manual_adjust_dialog_title][
        y_direction_shift_input].double_click_input()
    pyautogui.hotkey('ctrl', 'a')
    #time.sleep(0.1)  #TODO: improve
    pyautogui.hotkey('ctrl', 'c')
    current_deviation_string = root.clipboard_get()
    current_deviation = float(current_deviation_string.replace(",", "."))
    result["y_start"] = current_deviation

    app[manual_adjust_dialog_title][angle_shift_input].double_click_input()
    pyautogui.hotkey('ctrl', 'a')
    #time.sleep(0.1)  #TODO: improve
    pyautogui.hotkey('ctrl', 'c')
    current_deviation_string = root.clipboard_get()
    current_deviation = float(current_deviation_string.replace(",", "."))
    result["angle_start"] = current_deviation

    app[manual_adjust_dialog_title][height_shift_input].double_click_input()
    pyautogui.hotkey('ctrl', 'a')
    #time.sleep(0.1)  #TODO: improve
    pyautogui.hotkey('ctrl', 'c')
    current_deviation_string = root.clipboard_get()
    current_deviation = float(current_deviation_string.replace(",", "."))
    result["height_start"] = current_deviation

    result["starting_level"] = getCurrentLevel(ground_image, mask_image)

    root.destroy()
    return result


def moveToStartPos(app,
                   result,
                   ground_image,
                   mask_image,
                   x=True,
                   y=True,
                   angle=True,
                   height=True):
    if x:
        app[manual_adjust_dialog_title][
            x_direction_shift_input].double_click_input()
        current_deviation = result["x_start"]
        current_deviation = round(current_deviation, 2)
        current_deviation_string = str(current_deviation).replace(".", ",")
        pyautogui.hotkey('ctrl', 'a')
        #time.sleep(0.1)  #TODO: improve
        pyautogui.write(current_deviation_string)
        pyautogui.press('enter')

    if y:
        app[manual_adjust_dialog_title][
            y_direction_shift_input].double_click_input()
        current_deviation = result["y_start"]
        current_deviation = round(current_deviation, 2)
        current_deviation_string = str(current_deviation).replace(".", ",")
        pyautogui.hotkey('ctrl', 'a')
        #time.sleep(0.1)  #TODO: improve
        pyautogui.write(current_deviation_string)
        pyautogui.press('enter')

    if angle:
        app[manual_adjust_dialog_title][angle_shift_input].double_click_input()
        current_deviation = result["angle_start"]
        current_deviation = round(current_deviation, 2)
        current_deviation_string = str(current_deviation).replace(".", ",")
        pyautogui.hotkey('ctrl', 'a')
        #time.sleep(0.1)  #TODO: improve
        pyautogui.write(current_deviation_string)
        pyautogui.press('enter')

    if height:
        app[manual_adjust_dialog_title][height_shift_input].double_click_input(
        )
        current_deviation = result["height_start"]
        current_deviation = round(current_deviation, 2)
        current_deviation_string = str(current_deviation).replace(".", ",")
        pyautogui.hotkey('ctrl', 'a')
        #time.sleep(0.1)  #TODO: improve
        pyautogui.write(current_deviation_string)
        pyautogui.press('enter')

    return


def testIncrement(app,
                  ground_image,
                  mask_image,
                  max_num_increments,
                  best_mean,
                  increment):
    best_mean = testInOneDirection(app,
                                   ground_image,
                                   mask_image,
                                   increment,
                                   max_num_increments,
                                   best_mean,
                                   direction="x",
                                   sign="up")
    best_mean = testInOneDirection(app,
                                   ground_image,
                                   mask_image,
                                   increment,
                                   max_num_increments,
                                   best_mean,
                                   direction="x",
                                   sign="down")
    best_mean = testInOneDirection(app,
                                   ground_image,
                                   mask_image,
                                   increment,
                                   max_num_increments,
                                   best_mean,
                                   direction="y",
                                   sign="up")
    best_mean = testInOneDirection(app,
                                   ground_image,
                                   mask_image,
                                   increment,
                                   max_num_increments,
                                   best_mean,
                                   direction="y",
                                   sign="down")

    return best_mean


def testAngle(app,
              ground_image,
              mask_image,
              max_num_increments,
              best_mean,
              increment):
    best_mean = testInOneDirection(app,
                                   ground_image,
                                   mask_image,
                                   increment,
                                   max_num_increments,
                                   best_mean,
                                   direction="angle",
                                   sign="up")
    best_mean = testInOneDirection(app,
                                   ground_image,
                                   mask_image,
                                   increment,
                                   max_num_increments,
                                   best_mean,
                                   direction="angle",
                                   sign="down")
    return best_mean


def testHeight(app,
               ground_image,
               mask_image,
               max_num_increments,
               best_mean,
               increment):
    best_mean = testInOneDirection(app,
                                   ground_image,
                                   mask_image,
                                   increment,
                                   max_num_increments,
                                   best_mean,
                                   direction="height",
                                   sign="up")
    best_mean = testInOneDirection(app,
                                   ground_image,
                                   mask_image,
                                   increment,
                                   max_num_increments,
                                   best_mean,
                                   direction="height",
                                   sign="down")
    return best_mean


def testNextOptimum(app, ground_image, mask_image):
    max_num_increments = 1000
    best_mean = 765
    best_mean_tmp_iter = 0

    best_mean = testHeight(app,
                           ground_image,
                           mask_image,
                           max_num_increments,
                           best_mean,
                           1)

    best_mean = testIncrement(app,
                              ground_image,
                              mask_image,
                              max_num_increments,
                              best_mean,
                              1)
    #TODO: testIncrement mit Inkrement 0.1 evtl auch hier, vor der Schleife
    while (best_mean != best_mean_tmp_iter):
        best_mean_tmp_iter = best_mean
        best_mean = testIncrement(app,
                                  ground_image,
                                  mask_image,
                                  max_num_increments,
                                  best_mean,
                                  0.1)
        best_mean = testIncrement(app,
                                  ground_image,
                                  mask_image,
                                  max_num_increments,
                                  best_mean,
                                  0.01)
        best_mean_tmp = 0
        while (best_mean != best_mean_tmp):
            best_mean_tmp = best_mean
            best_mean = testIncrement(app,
                                      ground_image,
                                      mask_image,
                                      max_num_increments,
                                      best_mean,
                                      0.01)
        best_mean = testAngle(app,
                              ground_image,
                              mask_image,
                              max_num_increments,
                              best_mean,
                              0.01)
        best_mean = testHeight(app,
                               ground_image,
                               mask_image,
                               max_num_increments,
                               best_mean,
                               0.1)
        best_mean = testHeight(app,
                               ground_image,
                               mask_image,
                               max_num_increments,
                               best_mean,
                               0.01)
    return best_mean


def setUpAppConnection(title_regex):
    """connect and focus"""
    app = Application().connect(title_re=title_regex,
                                class_name=app_class_name)
    app[app_title_regex].set_focus()
    return app


def setUpHeightDiff(app, gray=False):
    app[app_title_regex].set_focus()
    if not app[app_title_regex][height_diff_settings_button].is_enabled():
        app[app_title_regex][height_diff_show_button].click()
        while not app[app_title_regex][height_diff_settings_button].is_enabled(
        ):
            time.sleep(0.01)
    app[app_title_regex][height_diff_settings_button].click_input()
    if gray:
        app[height_diff_dialog_title][
            height_diff_settings_scheme_colorpalette_gray].click()
    else:
        app[height_diff_dialog_title][
            height_diff_settings_scheme_colorpalette].click()
    app[height_diff_dialog_title][height_diff_settings_ok_button].click()
    app[height_diff_dialog_title].wait_not("visible")
    return


def setUpManAdjust(app):
    app[app_title_regex][detail_pos_shift_dialog_dropdown].click_input()
    already_shown = False
    for s in app.windows():
        if ("Manuell anpassen" in str(s)):
            already_shown = True
            break
    if not already_shown:
        app[app_title_regex][manual_adjust_dialog_button].click()
        app[manual_adjust_dialog_title].wait("visible enabled active")
    return


def removeLines():
    pyautogui.moveTo(1584, 500)
    pyautogui.dragTo(2850, 500, button="left")
    pyautogui.moveTo(1584, 973)
    pyautogui.dragTo(2519, 1876, button="left")
    return


def setUpAppConnection(title_regex):
    """connect and focus"""
    app = Application().connect(title_re=title_regex,
                                class_name=app_class_name)
    app[app_title_regex].set_focus()
    return app


def captureImageViewandFloodfillDarkAreas(app, floodfill=True):
    app[neig_title_regex].set_focus()
    ss = app[neig_title_regex][neig_image_view].capture_as_image()
    ss_width = ss.size[0]
    ss_height = ss.size[1]
    crop_x = ss_width // 100
    crop_y = ss_height // 100
    crop_width = ss_width - crop_x
    crop_height = ss_height - crop_y
    ss = ss.crop((crop_x, crop_y, crop_width, crop_height))
    if (floodfill):
        ImageDraw.floodfill(ss, (0, 0), (0, 0, 0), thresh=80)
    return ss


def findStartEndPixels(image):
    ss_width = image.size[0]
    nparrayimg = np.array(image.getdata())
    begin_pixels = []
    end_pixels = []
    pixel_begin = 0
    rowpostemppixel_x = ss_width
    rowpostemppixel_y = 0
    pixel_end = nparrayimg[(nparrayimg.size // 3) - 1]
    i = 0
    for p in nparrayimg:
        if (p[0] != 0 or p[1] != 0 or p[2] != 0):
            if pixel_begin == 0:
                pixel_begin = i
            pixel = i % ss_width
            if pixel <= rowpostemppixel_x:
                if (len(begin_pixels) > 0):
                    begin_pixels.pop(0)
                begin_pixels.append(pixel)
                rowpostemppixel_x = pixel
        if p[0] != 0 or p[1] != 0 or p[2] != 0:
            pixel_end = i
            pixel = i % ss_width
            if pixel >= rowpostemppixel_y:
                if (len(end_pixels) > 0):
                    end_pixels.pop(0)
                end_pixels.append(pixel)
                rowpostemppixel_y = pixel

        i = i + 1
    pixel_begin_x = np.bincount(np.array(begin_pixels)).argmax()
    pixel_end_x = np.bincount(np.array(end_pixels)).argmax()

    print("pixel_begin_num: ", pixel_begin)
    print("pixel_end_num: ", pixel_end)

    pixel_begin_row_firstpixelnum = 0

    for y in range(0, (nparrayimg.size // 3), ss_width):
        if y > (pixel_begin - ss_width):
            pixel_begin_row_firstpixelnum = y
            break

    pixel_begin_y = pixel_begin_row_firstpixelnum // ss_width
    print("pixelbegin", pixel_begin_x, pixel_begin_y)

    pixel_end_row_firstpixelnum = 0

    for y in range(0, (nparrayimg.size // 3), ss_width):
        if y > (pixel_end - ss_width):
            pixel_end_row_firstpixelnum = y
            break

    pixel_end_y = pixel_end_row_firstpixelnum // ss_width
    print("pixelend", pixel_end_x, pixel_end_y)
    return (pixel_begin_x, pixel_begin_y, pixel_end_x, pixel_end_y)


def createOverlayImage(flooded_image, start_end_pixels):
    pixel_begin_x = start_end_pixels[0]
    pixel_begin_y = start_end_pixels[1]
    pixel_end_x = start_end_pixels[2]
    pixel_end_y = start_end_pixels[3]
    crop = (pixel_begin_x, pixel_begin_y, pixel_end_x, pixel_end_y)
    temp_image = flooded_image.crop(crop)
    return temp_image


def makeTkinterOverlayWindow(overlay_image, filepaths, mask_image):
    coords = (0, 0)
    if filepaths[0] and len(filepaths[0]) > 1:
        with open(filepaths[0]) as file:  #TODO: error handling try catch
            coords_json = json.load(file)
            print("coordsstring: ", coords_json)
            print("coordsjson[x]", coords_json["x"])
            print("coordsjson[y]", coords_json["y"])
        file.close()
        if coords_json:
            coords = (coords_json["x"], coords_json["y"])
            print("coords ", coords)
    overlay_window = tk.Tk()

    def chooseImage():
        global chooseImage_flag, chooseImage_image  #TODO: find better solution
        chooseImage_flag = not chooseImage_flag
        if chooseImage_flag:
            chooseImage_image = ImageTk.PhotoImage(mask_image)
        else:
            chooseImage_image = ImageTk.PhotoImage(overlay_image)
        return chooseImage_image

    def on_move(x, y):
        overlay_window.geometry("+{}+{}".format(
            x - overlay_window.winfo_width() // 2,
            y - overlay_window.winfo_height() // 2))

    def on_click(x, y, button, pressed, want_to_save=False):
        global overlay_window_size, overlay_window_pos
        overlay_window_pos = (x - overlay_window.winfo_width() // 2,
                              y - overlay_window.winfo_height() // 2)
        print("overlay_window Pos at {0}".format(overlay_window_pos))
        overlay_window_size = (overlay_window.winfo_width(),
                               overlay_window.winfo_height())
        print("overlay_window Size {0}".format(overlay_window_size))
        if filepaths[1] and len(filepaths[1]) > 1:
            pos = {"x": x, "y": y}
            with open(filepaths[1], "w") as file:
                json.dump(pos, file)
        if not pressed:
            # Stop listener
            overlay_window.destroy()
            return False

    def on_release(key):
        mouse = Controller()
        if key == keyboard.Key.up:
            mouse.move(0, -1)
        if key == keyboard.Key.down:
            mouse.move(0, 1)
        if key == keyboard.Key.left:
            mouse.move(-1, 0)
        if key == keyboard.Key.right:
            mouse.move(1, 0)
        if key == keyboard.Key.end:
            mouse.click(Button.left, 1)
        if key == keyboard.Key.home:
            if coords != (0, 0):
                mouse.position = (coords[0], coords[1])
        if key == keyboard.Key.page_up:
            window_alpha = overlay_window.attributes("-alpha")
            window_alpha = window_alpha + 0.05
            overlay_window.attributes("-alpha", window_alpha)
        if key == keyboard.Key.page_down:
            window_alpha = overlay_window.attributes("-alpha")
            window_alpha = window_alpha - 0.05
            overlay_window.attributes("-alpha", window_alpha)
        if key == keyboard.Key.ctrl_r:
            image = chooseImage()
            canvas.itemconfig(image_container, image=image)

    keyboard_listener = keyboard.Listener(on_release=on_release)
    keyboard_listener.start()
    mouse_listener = mouse.Listener(on_move=on_move, on_click=on_click)
    mouse_listener.start()

    setUpAppConnection(app_title_regex)
    width = overlay_image.size[0]
    height = overlay_image.size[1]
    overlay_window.geometry("%dx%d" % (width, height))
    overlay_window.geometry("+500+200")
    overlay_window.overrideredirect(True)
    overlay_window.attributes("-alpha", 0.5)
    overlay_window.attributes("-topmost", "true")
    canvas = tk.Canvas(overlay_window, width=width, height=height)
    canvas.pack()
    tk_image = ImageTk.PhotoImage(mask_image)
    image_container = canvas.create_image(0, 0, anchor=tk.NW, image=tk_image)
    showOverlayTipsDialog(overlay_window)
    pyautogui.moveTo(1584,
                     500)  #TODO:get screen coords instead of hardcoded values
    overlay_window.mainloop()


def showOverlayTipsDialog(root):
    window = tk.Toplevel(root)
    window.geometry(window_geometry)
    window.attributes("-topmost", "true")

    ipadding = {'ipadx': 10, 'ipady': 10, "padx": 0, "pady": 0}

    tk.Label(
        window,
        text=
        "Keyboard up/down/left/right oder Maus um die\nArtefaktaufnahmen uebereinander zu legen",
        anchor=tk.W,
        bg="white").pack(**ipadding,
                         fill=tk.X)
    tk.Label(
        window,
        text=
        "Keyboard home(pos1) um das Bild auf die\ngeladene Position zu bringen",
        anchor=tk.W,
        bg="white").pack(**ipadding,
                         fill=tk.X)
    tk.Label(
        window,
        text=
        "Keyboard end oder Maus Linksklick sobald\nPosition der Artefaktaufnahmen uebereinstimmt",
        anchor=tk.W,
        bg="white").pack(**ipadding,
                         fill=tk.X)
    tk.Label(
        window,
        text="Keyboard ctrl_r um zwischen\nMaske und Overlay umzuschalten",
        anchor=tk.W,
        bg="white").pack(**ipadding,
                         fill=tk.X)
    tk.Label(window,
             text="Keyboard page-up/page-down um\nTransparenz zu veraendern",
             anchor=tk.W,
             bg="white").pack(**ipadding,
                              fill=tk.X)
    window.mainloop()


def makeMaskfromSS(ss, start_end_pixels, filepaths):
    #TODO: Reihenfolge aendern, so ists ineffektiv / evtl. eine Lösung mit Image.point finden anstatt Konversion zu Array
    nparrayimg = np.array(ss.getdata())
    for r in nparrayimg:
        if r[0] == r[1] == r[2]:
            r[0] = 0
            r[1] = 0
            r[2] = 0
        else:
            r[0] = 255
            r[1] = 255
            r[2] = 255
    pixel_begin_x = start_end_pixels[0]
    pixel_begin_y = start_end_pixels[1]
    pixel_end_x = start_end_pixels[2]
    pixel_end_y = start_end_pixels[3]
    crop = (pixel_begin_x, pixel_begin_y, pixel_end_x, pixel_end_y)
    mask_image = Image.fromarray(
        nparrayimg.astype(np.uint8).reshape(ss.size[1],
                                            ss.size[0],
                                            3))
    mask_image = mask_image.crop(crop)
    mask_image = mask_image.convert("L")
    if filepaths[1] and len(filepaths[1]) > 1:
        mask_image.save(filepaths[1])  #TODO: error handling try catch
    return mask_image


def makeGroundImage(mask_image):
    nparrayimg = np.zeros([mask_image.size[0],
                           mask_image.size[1],
                           3],
                          dtype=np.uint8)
    nparrayimg.fill(254)
    nparrayimg[:, 2] = 255
    ground_image = Image.fromarray(
        nparrayimg.reshape(mask_image.size[1],
                           mask_image.size[0],
                           3))
    return ground_image


def grabAndCropSS():  #overlay_window_pos / overlay_window_size are global vars
    setUpAppConnection(app_title_regex)
    ss = ImageGrab.grab()
    crop = (overlay_window_pos[0],
            overlay_window_pos[1],
            overlay_window_pos[0] + overlay_window_size[0],
            overlay_window_pos[1] + overlay_window_size[1])
    ss = ss.crop(crop)
    return ss


def makeFinalImage(ss, ground_image, mask_image):
    final_image = ground_image.copy()
    final_image.paste(ss, box=None, mask=mask_image)
    return final_image


def setUpHeightDiff(app, gray=False, title=app_title_regex):
    app[title].set_focus()
    if not app[title][height_diff_settings_button].is_enabled():
        app[title][height_diff_show_button].click()
        while not app[title][height_diff_settings_button].is_enabled():
            time.sleep(0.5)
            app[title][height_diff_show_button].click()
    app[title][height_diff_settings_button].click_input()
    if gray:
        app[height_diff_dialog_title][
            height_diff_settings_scheme_colorpalette_gray].click()
    else:
        app[height_diff_dialog_title][
            height_diff_settings_scheme_colorpalette].click()
    app[height_diff_dialog_title][height_diff_settings_ok_button].click()
    app[height_diff_dialog_title].wait_not("visible")
    return


def setDownHeightDiff(app, title=app_title_regex):
    app[title].set_focus()
    if app[title][height_diff_settings_button].is_enabled():
        app[title][height_diff_show_button].click()
        while app[title][height_diff_settings_button].is_enabled():
            time.sleep(0.5)
            app[title][height_diff_show_button].click()
    return


def showMarkAreaDialog():
    window = tk.Tk()
    window.geometry(window_geometry)
    window.attributes("-topmost", "true")
    file_path_load = StringVar()
    file_path_load.set("-")
    file_path_save = StringVar()
    file_path_save.set("-")

    def filedialogopen():
        file_path_load.set(filedialog.askopenfilename())

    def filedialogsave():
        file_path_save.set(
            filedialog.asksaveasfilename(defaultextension="bmp"))

    def end():
        window.destroy()

    ipadding = {'ipadx': 10, 'ipady': 10, "padx": 0, "pady": 0}
    tk.Label(
        window,
        text=
        "JETZT den Bereich der Aufnahme auswaehlen,\nanhand dessen die Positionierung erfolgen soll",
        anchor=tk.W,
        bg="red").pack(**ipadding,
                       fill=tk.X)
    tk.Label(window,
             text="der Zoom-Faktor darf nicht geändert werden!",
             anchor=tk.W,
             bg="red").pack(**ipadding,
                            fill=tk.X)
    tk.Label(window,
             text="Dazu die Keyence Funktionen verwenden",
             anchor=tk.W,
             bg="white").pack(**ipadding,
                              fill=tk.X)
    tk.Label(window,
             text="Alternativ einen bereits festgelegten Bereich laden",
             anchor=tk.W,
             bg="white").pack(**ipadding,
                              fill=tk.X)
    tk.Label(
        window,
        text=
        "(Positionierung VOR dem Klick auf OK durchfuehren\nODER Bild laden, dann auf OK)",
        anchor=tk.W,
        bg="red").pack(**ipadding,
                       fill=tk.X)
    tk.Label(window,
             textvariable=file_path_load).pack(**ipadding,
                                               fill=tk.X,
                                               expand=True)
    tk.Button(window,
              text='Bild mit Festlegung laden',
              command=filedialogopen).pack(**ipadding,
                                           fill=tk.X)
    tk.Button(window,
              text='Bereich nach Festlegung speichern',
              command=filedialogsave).pack(**ipadding,
                                           fill=tk.X)
    tk.Label(window,
             textvariable=file_path_save).pack(**ipadding,
                                               fill=tk.X,
                                               expand=True)
    tk.Button(window, text='OK', command=end).pack(**ipadding, fill=tk.X)
    window.mainloop()
    return (file_path_load.get(), file_path_save.get())


def showOverlayAreaDialog():
    window = tk.Tk()
    window.geometry(window_geometry)
    window.attributes("-topmost", "true")
    file_path_load = StringVar()
    file_path_load.set("-")
    file_path_save = StringVar()
    file_path_save.set("-")

    def filedialogopen():
        file_path_load.set(filedialog.askopenfilename())

    def filedialogsave():
        file_path_save.set(
            filedialog.asksaveasfilename(defaultextension="json"))

    def end():
        window.destroy()

    ipadding = {'ipadx': 10, 'ipady': 10, "padx": 0, "pady": 0}

    tk.Label(window,
             text="Entweder bereits festgelegte Position laden",
             anchor=tk.W,
             bg="white").pack(**ipadding,
                              fill=tk.X)
    tk.Label(
        window,
        text="oder die Position des festgelegten Bereichs\nmanuell festlegen",
        anchor=tk.W,
        bg="white").pack(**ipadding,
                         fill=tk.X)
    tk.Label(
        window,
        text=
        "die festgelegte Position kann gespeichert werden\n(zur späteren Wiederverwendung)",
        anchor=tk.W,
        bg="white").pack(**ipadding,
                         fill=tk.X)
    tk.Label(window,
             text="(Positionierung beginnt NACH dem Klick auf OK)",
             anchor=tk.W,
             bg="red").pack(**ipadding,
                            fill=tk.X)
    tk.Label(window,
             textvariable=file_path_load).pack(**ipadding,
                                               fill=tk.X,
                                               expand=True)
    tk.Button(window,
              text='Position zur Festlegung mit Pos1 laden',
              command=filedialogopen).pack(**ipadding,
                                           fill=tk.X)
    tk.Button(window,
              text='Position nach Festlegung speichern',
              command=filedialogsave).pack(**ipadding,
                                           fill=tk.X)
    tk.Label(window,
             textvariable=file_path_save).pack(**ipadding,
                                               fill=tk.X,
                                               expand=True)
    tk.Button(window, text='OK', command=end).pack(**ipadding, fill=tk.X)
    window.mainloop()
    return (file_path_load.get(), file_path_save.get())


def setUpZoom(app, title, image_view):
    texts = app[title][zoom_combobox].item_texts()
    texts.reverse()
    for sel in texts:
        app[title][zoom_combobox].select(sel)
        if controlZoomvalue(app, title, image_view):
            selection = sel
        else:
            break
    app[title][zoom_combobox].select(selection)
    return selection


def checkColor(pixel_color):
    if pixel_color[0] != pixel_color[1] or pixel_color[1] != pixel_color[
            2] or pixel_color[0] > 80 or pixel_color[1] > 80 or pixel_color[
                2] > 80:
        return False
    else:
        return True


def controlZoomvalue(app, title, image_view):
    app = setUpAppConnection(title)
    control_image = app[title][image_view].capture_as_image()
    control_pixel = (int(control_image.size[0] * 0.5),
                     int(control_image.size[1] * 0.005))
    control_pixel_color = control_image.getpixel(control_pixel)
    if not checkColor(control_pixel_color):
        return False
    for i in range(0, 500, 100):
        padd = (control_pixel[0] + i, control_pixel[1])
        psub = (control_pixel[0] - i, control_pixel[1])
        padd_pixel_color = control_image.getpixel(padd)
        psub_pixel_color = control_image.getpixel(psub)
        print(control_pixel_color, padd_pixel_color, psub_pixel_color)
        if padd_pixel_color != control_pixel_color or psub_pixel_color != control_pixel_color:
            return False

    return True


def showStartingWindow():
    window = tk.Tk()
    window.geometry(window_geometry)
    window.attributes("-topmost", "true")

    def end():
        window.destroy()

    ipadding = {'ipadx': 10, 'ipady': 10, "padx": 0, "pady": 0}
    tk.Label(
        window,
        text=
        "Vor Beginn muss das Keyence Analyseprogramm\ngeöffnet werden, dort:",
        anchor=tk.W,
        bg="white").pack(**ipadding,
                         fill=tk.X)
    tk.Label(window,
             text="-> Analyse öffnen",
             anchor=tk.W,
             bg="white").pack(**ipadding,
                              fill=tk.X)
    tk.Label(window,
             text="-> Messvergleich starten",
             anchor=tk.W,
             bg="white").pack(**ipadding,
                              fill=tk.X)
    tk.Label(
        window,
        text=
        "-> [falls Referenzbild bereits gewählt: Klick auf\n\"Position ausrichten\" - Button]",
        anchor=tk.W,
        bg="white").pack(**ipadding,
                         fill=tk.X)
    tk.Label(
        window,
        text="das \"Vergleichsbild auswählen\" - Fenster\nmuss geöffnet sein!",
        anchor=tk.W,
        bg="red").pack(**ipadding,
                       fill=tk.X,
                       expand=True)
    tk.Label(window,
             text="-> Referenzdaten auswählen",
             anchor=tk.W,
             bg="white").pack(**ipadding,
                              fill=tk.X)
    tk.Label(window,
             text="-> dann Programm starten durch Klick auf \"OK\"",
             anchor=tk.W,
             bg="white").pack(**ipadding,
                              fill=tk.X)
    tk.Label(
        window,
        text=
        "während des gesamten Ablaufs gilt:\nkeine Maus-/Tastatureingabe ohne Aufforderung!",
        anchor=tk.W,
        bg="red").pack(**ipadding,
                       fill=tk.X,
                       expand=True)
    tk.Button(window, text='OK', command=end).pack(**ipadding, fill=tk.X)
    window.mainloop()
    return


class DelayWindowThread(threading.Thread):
    # override the constructor
    def __init__(self, app, window):
        # execute the base constructor
        threading.Thread.__init__(self)
        self.app = app
        self.window = window

    # custom run function
    def run(self):
        self.ss_overlay = captureImageViewandFloodfillDarkAreas(self.app)
        self.start_end_pixels = findStartEndPixels(self.ss_overlay)
        self.window.quit()
        self.window.update()

    # custom get function
    def get(self):
        return self.ss_overlay, self.start_end_pixels


def showDelayWindow(app):
    window = tk.Tk()
    window.geometry(window_geometry)
    window.attributes("-topmost", "true")
    ipadding = {'ipadx': 10, 'ipady': 10, "padx": 0, "pady": 0}
    tk.Label(window,
             text="Berechne...",
             anchor=tk.W,
             bg="red").pack(**ipadding,
                            fill=tk.X)
    thread = DelayWindowThread(app, window)
    thread.start()
    window.mainloop()
    thread.join()
    ss_overlay, start_end_pixels = thread.get()
    window.destroy()
    return ss_overlay, start_end_pixels


def showWhichTestDialog(app):
    window = tk.Tk()
    window.geometry(window_geometry)
    window.attributes("-topmost", "true")

    file_path_save = StringVar()
    file_path_save.set("-")

    def filedialogsave():
        file_path_save.set(
            filedialog.asksaveasfilename(defaultextension="json"))

    r = [0]

    def returnOne(r):
        r[0] = 1
        window.destroy()

    def returnTwo(r):
        filedialogsave()
        r[0] = 2
        r.append(file_path_save.get())
        window.destroy()

    def returnThree(r):
        filedialogsave()
        r[0] = 3
        r.append(file_path_save.get())
        window.destroy()

    def returnFour(r):
        r[0] = 4
        window.destroy()

    def returnZero():
        window.destroy()
        exit()

    ipadding = {'ipadx': 10, 'ipady': 10, "padx": 0, "pady": 0}
    tk.Button(window,
              text='nach naechstgelegenem Minimum suchen',
              command=partial(returnOne,
                              r)).pack(**ipadding,
                                       fill=tk.X)
    tk.Button(
        window,
        text=
        'nach absolutem Minimum in der Naehe suchen\n(Grenzwerte sind im Skript definiert)\n(dauert ca. 2 Tage)',
        command=partial(returnTwo,
                        r)).pack(**ipadding,
                                 fill=tk.X)
    tk.Button(window,
              text='beides',
              command=partial(returnThree,
                              r)).pack(**ipadding,
                                       fill=tk.X)
    tk.Button(window,
              text='nur current level',
              command=partial(returnFour,
                              r)).pack(**ipadding,
                                       fill=tk.X)
    tk.Button(window,
              text='Ende',
              command=returnZero).pack(**ipadding,
                                       fill=tk.X)

    window.update()
    window.mainloop()
    app[app_title_regex].set_focus()
    return r


def setUpAreaToCompare(app, zoom_value):
    app[app_title_regex][neig_settings_button].click()
    app[neig_title_regex][zoom_combobox].select(zoom_value)
    app[neig_title_regex][height_diff_show_button].click()
    app[neig_title_regex][height_diff_show_button].click()
    app[neig_title_regex][neig_area_delete_button].click()
    ss_overlay, start_end_pixels = showDelayWindow(app)
    app[neig_title_regex][neig_area_recover_button].click()
    filepaths_image = showMarkAreaDialog()
    if filepaths_image[0] and len(filepaths_image[0]) > 1:
        mask_image = Image.open(
            filepaths_image[0])  #TODO: error handling try catch
    else:
        setUpHeightDiff(app, gray=True, title=neig_title_regex)
        ss_mask = captureImageViewandFloodfillDarkAreas(app, floodfill=False)
        mask_image = makeMaskfromSS(ss_mask,
                                    start_end_pixels,
                                    filepaths=filepaths_image)
    overlay_image = createOverlayImage(ss_overlay, start_end_pixels)
    app[neig_title_regex][neig_abort_button].click_input()
    setDownHeightDiff(app, title=app_title_regex)
    filepaths_position = showOverlayAreaDialog()
    makeTkinterOverlayWindow(
        overlay_image,
        filepaths_position,
        mask_image
    )  #TODO: maybe rework global vars overlay_window_pos/overlay_window_size
    ground_image = makeGroundImage(mask_image)
    return (ground_image, mask_image)


def bruteXY(app,
            ground_image,
            mask_image,
            brute_deviation_increment,
            result,
            x,
            y,
            angle,
            height,
            intvar,
            window):
    #0+
    x_max_temp = brute_x_max + x
    while x < x_max_temp:
        result = testInOneDirectionBrute(app,
                                         ground_image,
                                         mask_image,
                                         brute_deviation_increment,
                                         "x",
                                         "up",
                                         result,
                                         x,
                                         y,
                                         angle,
                                         height)
        x = x + brute_deviation_increment
        i = intvar.get()
        intvar.set(i - 1)
        window.update()
    moveToStartPos(app,
                   result,
                   ground_image,
                   mask_image,
                   x=True,
                   y=False,
                   angle=False,
                   height=False)
    x = result["x_start"]

    #0-
    x_max_temp = x - brute_x_max
    while x > x_max_temp:
        result = testInOneDirectionBrute(app,
                                         ground_image,
                                         mask_image,
                                         brute_deviation_increment,
                                         "x",
                                         "down",
                                         result,
                                         x,
                                         y,
                                         angle,
                                         height)
        x = x - brute_deviation_increment
        i = intvar.get()
        intvar.set(i - 1)
        window.update()
    moveToStartPos(app,
                   result,
                   ground_image,
                   mask_image,
                   x=True,
                   y=False,
                   angle=False,
                   height=False)
    x = result["x_start"]

    #++
    x_max_temp = brute_x_max + x
    y_max_temp = brute_y_max + y
    while y < y_max_temp:
        result = testInOneDirectionBrute(app,
                                         ground_image,
                                         mask_image,
                                         brute_deviation_increment,
                                         "y",
                                         "up",
                                         result,
                                         x,
                                         y,
                                         angle,
                                         height)
        y = y + brute_deviation_increment
        i = intvar.get()
        intvar.set(i - 1)
        window.update()
        while x < x_max_temp:
            result = testInOneDirectionBrute(app,
                                             ground_image,
                                             mask_image,
                                             brute_deviation_increment,
                                             "x",
                                             "up",
                                             result,
                                             x,
                                             y,
                                             angle,
                                             height)
            x = x + brute_deviation_increment
        moveToStartPos(app,
                       result,
                       ground_image,
                       mask_image,
                       x=True,
                       y=False,
                       angle=False,
                       height=False)
        x = result["x_start"]
        i = intvar.get()
        intvar.set(i - 1)
        window.update()

    moveToStartPos(app,
                   result,
                   ground_image,
                   mask_image,
                   x=False,
                   y=True,
                   angle=False,
                   height=False)
    x = result["x_start"]
    y = result["y_start"]

    #+-
    y_max_temp = brute_y_max + y
    x_max_temp = x - brute_x_max
    while y < y_max_temp:
        result = testInOneDirectionBrute(app,
                                         ground_image,
                                         mask_image,
                                         brute_deviation_increment,
                                         "y",
                                         "up",
                                         result,
                                         x,
                                         y,
                                         angle,
                                         height)
        y = y + brute_deviation_increment
        while x > x_max_temp:
            result = testInOneDirectionBrute(app,
                                             ground_image,
                                             mask_image,
                                             brute_deviation_increment,
                                             "x",
                                             "down",
                                             result,
                                             x,
                                             y,
                                             angle,
                                             height)
            x = x - brute_deviation_increment
            i = intvar.get()
            intvar.set(i - 1)
            window.update()
        moveToStartPos(app,
                       result,
                       ground_image,
                       mask_image,
                       x=True,
                       y=False,
                       angle=False,
                       height=False)
        x = result["x_start"]

    moveToStartPos(app,
                   result,
                   ground_image,
                   mask_image,
                   x=False,
                   y=True,
                   angle=False,
                   height=False)
    x = result["x_start"]
    y = result["y_start"]

    #-+
    y_max_temp = y - brute_y_max
    x_max_temp = brute_x_max + x
    while y > y_max_temp:
        result = testInOneDirectionBrute(app,
                                         ground_image,
                                         mask_image,
                                         brute_deviation_increment,
                                         "y",
                                         "down",
                                         result,
                                         x,
                                         y,
                                         angle,
                                         height)
        y = y - brute_deviation_increment
        i = intvar.get()
        intvar.set(i - 1)
        window.update()
        while x < x_max_temp:
            result = testInOneDirectionBrute(app,
                                             ground_image,
                                             mask_image,
                                             brute_deviation_increment,
                                             "x",
                                             "up",
                                             result,
                                             x,
                                             y,
                                             angle,
                                             height)
            x = x + brute_deviation_increment
            i = intvar.get()
            intvar.set(i - 1)
            window.update()
        moveToStartPos(app,
                       result,
                       ground_image,
                       mask_image,
                       x=True,
                       y=False,
                       angle=False,
                       height=False)
        x = result["x_start"]

    moveToStartPos(app,
                   result,
                   ground_image,
                   mask_image,
                   x=False,
                   y=True,
                   angle=False,
                   height=False)
    x = result["x_start"]
    y = result["y_start"]

    #--
    y_max_temp = y - brute_y_max
    x_max_temp = x - brute_x_max
    while y > y_max_temp:
        result = testInOneDirectionBrute(app,
                                         ground_image,
                                         mask_image,
                                         brute_deviation_increment,
                                         "y",
                                         "down",
                                         result,
                                         x,
                                         y,
                                         angle,
                                         height)
        y = y - brute_deviation_increment
        while x > x_max_temp:
            result = testInOneDirectionBrute(app,
                                             ground_image,
                                             mask_image,
                                             brute_deviation_increment,
                                             "x",
                                             "down",
                                             result,
                                             x,
                                             y,
                                             angle,
                                             height)
            x = x - brute_deviation_increment
            i = intvar.get()
            intvar.set(i - 1)
            window.update()
        moveToStartPos(app,
                       result,
                       ground_image,
                       mask_image,
                       x=True,
                       y=False,
                       angle=False,
                       height=False)
        x = result["x_start"]

    moveToStartPos(app,
                   result,
                   ground_image,
                   mask_image,
                   x=False,
                   y=True,
                   angle=False,
                   height=False)

    return result


def bruteAngleAndXY(app,
                    ground_image,
                    mask_image,
                    brute_deviation_increment,
                    result,
                    x,
                    y,
                    angle,
                    height,
                    intvar,
                    window):
    #0
    result = bruteXY(app,
                     ground_image,
                     mask_image,
                     brute_deviation_increment,
                     result,
                     x,
                     y,
                     angle,
                     height,
                     intvar,
                     window)

    #+
    angle_max_temp = brute_angle_max + angle
    while angle < angle_max_temp:
        result = testInOneDirectionBrute(app,
                                         ground_image,
                                         mask_image,
                                         brute_deviation_increment,
                                         "angle",
                                         "up",
                                         result,
                                         x,
                                         y,
                                         angle,
                                         height)
        angle = angle + brute_deviation_increment
        i = intvar.get()
        intvar.set(i - 1)
        window.update()
        result = bruteXY(app,
                         ground_image,
                         mask_image,
                         brute_deviation_increment,
                         result,
                         x,
                         y,
                         angle,
                         height,
                         intvar,
                         window)
    angle = result["angle_start"]
    moveToStartPos(app,
                   result,
                   ground_image,
                   mask_image,
                   x=False,
                   y=False,
                   angle=True,
                   height=False)

    #-
    angle_max_temp = angle - brute_angle_max
    while angle > angle_max_temp:
        result = testInOneDirectionBrute(app,
                                         ground_image,
                                         mask_image,
                                         brute_deviation_increment,
                                         "angle",
                                         "down",
                                         result,
                                         x,
                                         y,
                                         angle,
                                         height)
        angle = angle - brute_deviation_increment
        i = intvar.get()
        intvar.set(i - 1)
        window.update()
        result = bruteXY(app,
                         ground_image,
                         mask_image,
                         brute_deviation_increment,
                         result,
                         x,
                         y,
                         angle,
                         height,
                         intvar,
                         window)
    angle = result["angle_start"]
    moveToStartPos(app,
                   result,
                   ground_image,
                   mask_image,
                   x=False,
                   y=False,
                   angle=True,
                   height=False)

    return result


def bruteHeightAngleAndXY(app,
                          ground_image,
                          mask_image,
                          brute_deviation_increment,
                          result,
                          x,
                          y,
                          angle,
                          height,
                          intvar,
                          window):

    #0
    result = bruteAngleAndXY(app,
                             ground_image,
                             mask_image,
                             brute_deviation_increment,
                             result,
                             x,
                             y,
                             angle,
                             height,
                             intvar,
                             window)

    #+
    height_max_temp = brute_height_max + height
    while height < height_max_temp:
        result = testInOneDirectionBrute(app,
                                         ground_image,
                                         mask_image,
                                         brute_deviation_increment,
                                         "height",
                                         "up",
                                         result,
                                         x,
                                         y,
                                         angle,
                                         height)
        height = height + brute_deviation_increment
        i = intvar.get()
        intvar.set(i - 1)
        window.update()
        result = bruteAngleAndXY(app,
                                 ground_image,
                                 mask_image,
                                 brute_deviation_increment,
                                 result,
                                 x,
                                 y,
                                 angle,
                                 height,
                                 intvar,
                                 window)
    height = result["height_start"]
    moveToStartPos(app,
                   result,
                   ground_image,
                   mask_image,
                   x=False,
                   y=False,
                   angle=False,
                   height=True)

    #-
    height_max_temp = height - brute_height_max
    while height > height_max_temp:
        result = testInOneDirectionBrute(app,
                                         ground_image,
                                         mask_image,
                                         brute_deviation_increment,
                                         "height",
                                         "down",
                                         result,
                                         x,
                                         y,
                                         angle,
                                         height)
        height = height - brute_deviation_increment
        i = intvar.get()
        intvar.set(i - 1)
        window.update()
        result = bruteAngleAndXY(app,
                                 ground_image,
                                 mask_image,
                                 brute_deviation_increment,
                                 result,
                                 x,
                                 y,
                                 angle,
                                 height,
                                 intvar,
                                 window)
    height = result["height_start"]
    moveToStartPos(app,
                   result,
                   ground_image,
                   mask_image,
                   x=False,
                   y=False,
                   angle=False,
                   height=True)

    return result


def bruteEverything(app,
                    ground_image,
                    mask_image,
                    brute_deviation_increment,
                    brute_x_max,
                    brute_y_max,
                    brute_angle_max,
                    brute_height_max,
                    file,
                    intvar,
                    window):

    total = (brute_x_max * (1 / brute_deviation_increment) * 2 +
             1) * (brute_y_max * (1 / brute_deviation_increment) * 2 +
                   1) * (brute_angle_max *
                         (1 / brute_deviation_increment) * 2 +
                         1) * (brute_height_max *
                               (1 / brute_deviation_increment) * 2 + 1)

    print("Brute_Everything_total_pos: ",
          total,
          "Time (days): ",
          total * 3 / 60 / 60 / 24)
    print("Brute_Everything_file: ", file)

    intvar.set(total)

    result = {}
    result["best_levels"] = []
    result["best_levels_length"] = 1000
    result = getStartPos(app, result, ground_image, mask_image)
    result["x_deviation"] = brute_x_max
    result["y_deviation"] = brute_y_max
    result["angle_deviation"] = brute_angle_max
    result["height_deviation"] = brute_height_max
    x = result["x_start"]
    y = result["y_start"]
    angle = result["angle_start"]
    height = result["height_start"]

    print("start,max:",
          x,
          brute_x_max,
          y,
          brute_y_max,
          angle,
          brute_angle_max,
          height,
          brute_height_max)

    result = bruteHeightAngleAndXY(app,
                                   ground_image,
                                   mask_image,
                                   brute_deviation_increment,
                                   result,
                                   x,
                                   y,
                                   angle,
                                   height,
                                   intvar,
                                   window)

    result["best_level_found"] = min(result["best_levels"])
    result["best_level_found_indices"] = find_indices(
        result["best_levels"],
        result["best_level_found"])

    json.dump(result, file)
    window.quit()
    window.update()
    return result


def showBruteDialog(app,
                    ground_image,
                    mask_image,
                    brute_deviation_increment,
                    brute_x_max,
                    brute_y_max,
                    brute_angle_max,
                    brute_height_max,
                    file):

    window = tk.Tk()
    window.geometry(window_geometry)
    window.attributes("-topmost", "true")

    intvar = tk.IntVar(window, 999)

    def returnZero():
        window.quit()
        window.update()

    ipadding = {'ipadx': 10, 'ipady': 10, "padx": 0, "pady": 0}

    tk.Label(window,
             text="verbleibende Positionen:",
             anchor=tk.W,
             bg="white").pack(**ipadding,
                              fill=tk.X)

    tk.Label(window,
             textvariable=intvar,
             anchor=tk.W,
             bg="red").pack(**ipadding,
                            fill=tk.X)

    tk.Button(window,
              text='Abbruch',
              command=returnZero).pack(**ipadding,
                                       fill=tk.X)

    window.after(200,
                 bruteEverything,
                 app,
                 ground_image,
                 mask_image,
                 brute_deviation_increment,
                 brute_x_max,
                 brute_y_max,
                 brute_angle_max,
                 brute_height_max,
                 file,
                 intvar,
                 window)

    window.mainloop()
    return


def getCurrentCoordsAndFov(app):
    root = tk.Tk()
    root.withdraw()

    fov = app[app_title_regex][height_diff_threshold_static].window_text()[1::]

    app[manual_adjust_dialog_title][
        x_direction_shift_input].double_click_input()
    pyautogui.hotkey('ctrl', 'a')
    #time.sleep(0.1)  #TODO: improve
    pyautogui.hotkey('ctrl', 'c')
    x = root.clipboard_get()

    app[manual_adjust_dialog_title][
        y_direction_shift_input].double_click_input()
    pyautogui.hotkey('ctrl', 'a')
    #time.sleep(0.1)  #TODO: improve
    pyautogui.hotkey('ctrl', 'c')
    y = root.clipboard_get()

    app[manual_adjust_dialog_title][height_shift_input].double_click_input()
    pyautogui.hotkey('ctrl', 'a')
    #time.sleep(0.1)  #TODO: improve
    pyautogui.hotkey('ctrl', 'c')
    height = root.clipboard_get()

    app[manual_adjust_dialog_title][angle_shift_input].double_click_input()
    pyautogui.hotkey('ctrl', 'a')
    #time.sleep(0.1)  #TODO: improve
    pyautogui.hotkey('ctrl', 'c')
    angle = root.clipboard_get()

    root.destroy()

    return x, y, height, angle, fov


showStartingWindow()
app = setUpAppConnection(app_title_regex)
removeLines()
zoom_value = setUpZoom(app, app_title_regex, manual_adjust_image_view)
setUpManAdjust(app)
images = setUpAreaToCompare(app, zoom_value)
ground_image = images[0].copy()
mask_image = images[1].copy()
setUpHeightDiff(app)
setUpManAdjust(app)

while (True):
    test = showWhichTestDialog(app)
    if test[0] == 1:
        testNextOptimum(app, ground_image, mask_image)
        x, y, height, angle, fov = getCurrentCoordsAndFov(app)
        getCurrentLevel(ground_image,
                        mask_image,
                        show_image=True,
                        x=x,
                        y=y,
                        height=height,
                        angle=angle,
                        fov=fov)
    elif test[0] == 2:
        with open(test[1], "w") as file:
            showBruteDialog(app,
                            ground_image,
                            mask_image,
                            brute_deviation_increment,
                            brute_x_max,
                            brute_y_max,
                            brute_angle_max,
                            brute_height_max,
                            file)
    elif test[0] == 3:
        testNextOptimum(app, ground_image, mask_image)
        x, y, height, angle, fov = getCurrentCoordsAndFov(app)
        getCurrentLevel(ground_image,
                        mask_image,
                        show_image=True,
                        x=x,
                        y=y,
                        height=height,
                        angle=angle,
                        fov=fov)
        with open(test[1], "w") as file:
            showBruteDialog(app,
                            ground_image,
                            mask_image,
                            brute_deviation_increment,
                            brute_x_max,
                            brute_y_max,
                            brute_angle_max,
                            brute_height_max,
                            file)
    elif test[0] == 4:
        x, y, height, angle, fov = getCurrentCoordsAndFov(app)
        getCurrentLevel(ground_image,
                        mask_image,
                        show_image=True,
                        x=x,
                        y=y,
                        height=height,
                        angle=angle,
                        fov=fov)
"""
weekendtest parameter (4k Screen):

overlay_window_pos = (683, 290)
overlay_window_size = (1797, 1366)
ground_image = Image.open("ground.bmp")
mask_image = Image.open("aa1.bmp")
"""