# Copyright (C) 2020  A2va

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from typing import List, Optional
from image_translator.type import Paragraph

import json
import os
import threading
import logging
import time

import cv2
import numpy as np
import pickle
import pathos.multiprocessing as p_multiprocessing
import wx
import wx.lib.newevent
from image_translator.image_translator import ImageTranslator

from easyocr.config import detection_models

from transimage.canvas import DisplayCanvas
from transimage.config import (BACKGROUND_COLOR, CANVAS_COLOR, SETTINGS_FILE,
                               TEXT_COLOR, LABEL_SIZE)
from transimage.lang import TO_LANG_CODE, TO_LANG_NAME
from transimage.settings import SettingsDialog, download

import pyppeteer.chromium_downloader as chromium

logFormatter = logging.Formatter(
    "[%(asctime)s] "
    "[%(levelname)-5.5s]: "
    "%(message)s")
log = logging.getLogger('transimage')
fileHandler = logging.FileHandler('latest.log')
fileHandler.setFormatter(logFormatter)
log.addHandler(fileHandler)

log.setLevel(logging.WARNING)

EvtImageProcess, EVT_IMAGE_PROCESS = wx.lib.newevent.NewEvent()


class ImageProcessError(Exception):
    pass


def create_settings_file():
    setting_dict = {
        'language_pack': TO_LANG_NAME.copy(),
        'default_src_lang': 'eng',
        'default_dest_lang': 'fra',
        'default_ocr': 'tesseract',
        'default_translator': 'bing',
        'gpu': False
    }

    for lang in setting_dict['language_pack']:
        setting_dict['language_pack'][lang] = False

    setting_file = open(SETTINGS_FILE, 'w')
    json.dump(setting_dict, setting_file)
    setting_file.close()


class ImageFile():
    def __init__(self):
        self.path: Optional[str] = None
        self.translator: Optional[str] = None
        self.ocr: Optional[str] = None
        self.src_lang: Optional[str] = None
        self.dest_lang: Optional[str] = None
        self.img: Optional[np.ndarray] = None
        self.name: Optional[str] = None
        self.text_list: Optional[List[Paragraph]] = None


class ImageProcess(threading.Thread):
    def __init__(self, notify_window: wx.Frame, img_file: ImageFile,gpu: bool, mode_process=True):
        super(ImageProcess, self).__init__()
        self.notify_window: wx.Frame = notify_window
        self.mode_process: bool = mode_process
        self.img: np.ndarray = img_file.img
        self.ocr: str = img_file.ocr
        self.translator: str = img_file.translator
        self.src_lang: str = img_file.src_lang
        self.dest_lang = img_file.dest_lang
        self.gpu: bool = gpu
        self.image_translator = ImageTranslator(self.img, self.ocr,
                                                self.translator,
                                                self.src_lang, self.dest_lang, self.gpu)
        self.process: p_multiprocessing.ProcessingPool = p_multiprocessing.ProcessingPool()
        self.stop: bool = False

    def run(self):
        """Run the ImageTranslator object"""
        try:
            self.stop = False
            # If mode_process true only process
            if self.mode_process:
                results = self.process.amap(ImageProcess.worker_process,
                                            [self.image_translator])
            else:  # Else translate
                results = self.process.amap(ImageProcess.worker_translate,
                                            [self.image_translator])
            # Wait the results to be ready or
            # stop by the user
            while not results.ready() and self.stop:
                time.sleep(2)

            # Skip this if user stopped
            if not self.stop:
                self.image_translator: ImageTranslator = results.get()
                # self.process.close()
                # Post the event to run callback function
                evt = EvtImageProcess(data=self.image_translator)
                wx.PostEvent(self.notify_window, evt)
        except ImageProcessError:
            log.error(
                f'ImageProcess got an error (mode_process:{self.mode_process})')
            raise ImageProcessError(
                f'ImageProcess got an error (mode_process:{self.mode_process}) look at log file')

    def abort(self):
        """Stop the mutliprocessing and while loop"""
        if self.process is not None:
            self.stop = True
            self.process.terminate()
            self.process.join()
            self.process.restart()
            self.image_translator = None

    @staticmethod
    def worker_process(image_translator):
        """Processing worker"""
        image_translator.processing()
        return image_translator

    @staticmethod
    def worker_translate(image_translator):
        """Translator worker"""
        image_translator.translate()
        return image_translator


class ProgressingDialog(wx.Dialog):
    """A class to show time elapsed"""
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title="Progressing",
                           pos=wx.DefaultPosition, size=wx.Size(200, 120),
                           style=wx.DEFAULT_DIALOG_STYLE)

        self.SetForegroundColour(BACKGROUND_COLOR)
        self.SetBackgroundColour(BACKGROUND_COLOR)
        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        mainSizer = wx.BoxSizer(wx.VERTICAL)

        textSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.fixedText = wx.StaticText(self, wx.ID_ANY, "Time:", wx.DefaultPosition,
                                       wx.DefaultSize, wx.ALIGN_CENTER_HORIZONTAL)
        self.fixedText.SetForegroundColour(TEXT_COLOR)
        self.fixedText.Wrap(-1)

        textSizer.Add(self.fixedText, 1, wx.ALIGN_CENTER, 5)

        self.timeText = wx.StaticText(self, wx.ID_ANY, "0", wx.DefaultPosition,
                                      wx.DefaultSize, wx.ALIGN_CENTER_HORIZONTAL)
        self.timeText.SetForegroundColour(TEXT_COLOR)

        textSizer.Add(self.timeText, 1, wx.ALIGN_CENTER | wx.ALL, 5)

        mainSizer.Add(textSizer, 1, wx.ALIGN_CENTER, 5)

        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.cancelButton = wx.Button(self, wx.ID_CANCEL, "Cancel",
                                      wx.DefaultPosition, wx.DefaultSize, 0)
        self.cancelButton.SetForegroundColour(TEXT_COLOR)
        self.cancelButton.SetBackgroundColour(BACKGROUND_COLOR)

        buttonSizer.Add(self.cancelButton, 1, wx.ALIGN_CENTER | wx.ALL, 5)

        mainSizer.Add(buttonSizer, 1, wx.ALIGN_CENTER, 5)

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.update_label, self.timer)
        self.timer.Start(1000)

        self.SetSizer(mainSizer)
        self.Layout()

        self.Centre(wx.BOTH)

    def update_label(self, event):
        """Update text label"""
        self.timeText.SetLabel(str(int(self.timeText.Label)+1))


class Transimage(wx.Frame):
    def __init__(self, parent):

        log.debug('Init the main frame (Transimage)')

        self.image_translator: Optional[ImageTranslator] = None

        # Create empty image file
        self.img_file = ImageFile()
        self.img_file.dest_lang = ''
        self.img_file.src_lang = ''
        self.img_file.translator = ''
        self.img_file.ocr = ''
        self.img_file.path = ''

        # Init the ui
        self.init_ui(parent)

        # Create settings file if it's needed
        if not os.path.exists(SETTINGS_FILE):
            open(SETTINGS_FILE, 'w+').close()
            create_settings_file()

        # Get settings file
        with open(SETTINGS_FILE, 'r') as settings_file:
            self.settings = json.load(settings_file)
            for lang in self.settings['language_pack']:
                if self.settings['language_pack'][lang]:
                    self.dest_langCombo.Append(TO_LANG_NAME[lang].capitalize())
                    self.src_langCombo.Append(TO_LANG_NAME[lang].capitalize())

            item = self.src_langCombo.FindString(
                TO_LANG_NAME[self.settings['default_src_lang']])
            if item != -1:
                self.src_langCombo.SetSelection(item)

            item = self.dest_langCombo.FindString(
                TO_LANG_NAME[self.settings['default_dest_lang']])
            if item != -1:
                self.dest_langCombo.SetSelection(item)

            item = self.ocrCombo.FindString(self.settings['default_ocr'])
            if item != -1:
                self.ocrCombo.SetSelection(item)

            item = self.translatorCombo.FindString(
                self.settings['default_translator'])
            if item != -1:
                self.translatorCombo.SetSelection(item)

            self.img_file.translator = self.settings['default_translator']
            self.img_file.ocr = self.settings['default_ocr']
            self.img_file.src_lang = self.settings['default_src_lang']
            self.img_file.dest_lang = self.settings['default_dest_lang']

        wx.CallAfter(self.download_components)

    def download_components(self):
        """Download CRAFT text detector model
        and chromium for pyppeteer"""
        filename: str = detection_models['craft']['filename']
        if not os.path.exists(f'easyocr/model/{filename}'):
            progress_dialog = wx.ProgressDialog(
            'Download', 'Detector model', maximum=100, parent=self)
            download(detection_models['craft']['url'], 'easyocr/model/',
                     progress_dialog, True, detection_models['craft']['filename'])
            progress_dialog.Destroy()

        chromium_path: str = f'./chromium/{chromium.REVISION}'
        if not os.path.exists('./chromium'):
            os.makedirs(chromium_path)

            progress_dialog = wx.ProgressDialog(
            'Download', 'Chromium', maximum=100, parent=self)
            download(chromium.get_url(), chromium_path,
                     progress_dialog, True)
            progress_dialog.Destroy()

    def init_ui(self, parent):
        """Init the ui"""
        wx.Frame.__init__(self, parent, id=wx.ID_ANY, title="Transimage",
                          pos=wx.DefaultPosition, size=wx.Size(1200, 500),
                          style=wx.DEFAULT_FRAME_STYLE)
        self.locale = wx.Locale(wx.LANGUAGE_ENGLISH)

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)
        self.SetForegroundColour(BACKGROUND_COLOR)
        self.SetBackgroundColour(BACKGROUND_COLOR)

        mainSizer = wx.BoxSizer(wx.HORIZONTAL)

        # Toolbar
        self.toolBar = wx.ToolBar(self, wx.ID_ANY, wx.DefaultPosition,
                                  wx.DefaultSize, wx.TB_VERTICAL)
        self.SetToolBar(self.toolBar)
        self.toolBar.SetForegroundColour(BACKGROUND_COLOR)
        self.toolBar.SetBackgroundColour(BACKGROUND_COLOR)

        self.logo = self.toolBar.AddTool(wx.ID_ANY, "Logo",
                                         wx.Bitmap("icons/logo.png"),
                                         wx.NullBitmap, wx.ITEM_NORMAL,
                                         wx.EmptyString, wx.EmptyString)
        self.Bind(wx.EVT_TOOL, self.context_menu, self.logo)

        self.open = self.toolBar.AddTool(wx.ID_ANY, "Open Image",
                                         wx.Bitmap("icons/open_file.png"),
                                         wx.NullBitmap, wx.ITEM_NORMAL,
                                         'Open Image', wx.EmptyString)
        self.Bind(wx.EVT_TOOL, self.open_file, self.open)

        self.save = self.toolBar.AddTool(wx.ID_ANY, "Save",
                                         wx.Bitmap("icons/save.png"),
                                         wx.NullBitmap, wx.ITEM_NORMAL,
                                         'Save project (shift click for save as)',
                                         wx.EmptyString)
        self.Bind(wx.EVT_TOOL, self.save_file, self.save)

        self.save_image = self.toolBar.AddTool(wx.ID_ANY, "Save",
                                               wx.Bitmap(
                                                   "icons/save_image.png"),
                                               wx.NullBitmap,
                                               wx.ITEM_NORMAL,
                                               'Save Image',
                                               'Save with png and jpeg format')
        self.Bind(wx.EVT_TOOL, self.save_image_file, self.save_image)

        self.about = self.toolBar.AddTool(wx.ID_ANY, "About",
                                          wx.Bitmap("icons/info.png"),
                                          wx.NullBitmap, wx.ITEM_NORMAL,
                                          'About', wx.EmptyString)
        self.Bind(wx.EVT_TOOL, self.about_menu, self.about)

        self.help = self.toolBar.AddTool(wx.ID_ANY, "Help",
                                         wx.Bitmap("icons/help.png"),
                                         wx.NullBitmap, wx.ITEM_NORMAL,
                                         'Help', wx.EmptyString)
        self.Bind(wx.EVT_TOOL, self.help_menu, self.help)

        self.settings = self.toolBar.AddTool(wx.ID_ANY, "Settings",
                                             wx.Bitmap("icons/settings.png"),
                                             wx.NullBitmap, wx.ITEM_NORMAL,
                                             'Settings', wx.EmptyString)
        self.Bind(wx.EVT_TOOL, self.settings_menu, self.settings)

        self.toolBar.Realize()

        imageSizer = wx.BoxSizer(wx.HORIZONTAL)

        # Image Canvas
        self.imageCanvas = DisplayCanvas(self, id=wx.ID_ANY, size=wx.DefaultSize,
                                         ProjectionFun=None,
                                         BackgroundColor=CANVAS_COLOR)
        self.imageCanvas.SetForegroundColour(CANVAS_COLOR)
        self.imageCanvas.SetBackgroundColour(CANVAS_COLOR)

        imageSizer.Add(self.imageCanvas, 3, wx.EXPAND)
        mainSizer.Add(imageSizer, 3, wx.EXPAND, 1)

        editSizer = wx.BoxSizer(wx.VERTICAL)
        # Source Language
        src_langSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.src_langText = wx.StaticText(self, wx.ID_ANY, "Source Language")
        self.src_langText.SetForegroundColour(TEXT_COLOR)
        self.src_langText.SetFont(wx.Font(LABEL_SIZE,
                                          wx.FONTFAMILY_DEFAULT,
                                          wx.FONTSTYLE_NORMAL,
                                          wx.FONTWEIGHT_NORMAL, 0, ""))

        self.src_langCombo = wx.ComboBox(
            self, wx.ID_ANY, choices=[], style=wx.CB_DROPDOWN | wx.CB_SORT)
        self.src_langCombo.SetBackgroundColour(BACKGROUND_COLOR)
        self.src_langCombo.SetForegroundColour(TEXT_COLOR)  # For text
        self.src_langCombo.SetFont(wx.Font(LABEL_SIZE,
                                           wx.FONTFAMILY_DEFAULT,
                                           wx.FONTSTYLE_NORMAL,
                                           wx.FONTWEIGHT_NORMAL, 0, ""))
        self.src_langCombo.Bind(wx.EVT_COMBOBOX, self.update_src_lang)

        src_langSizer.Add(self.src_langText, 0, wx.ALL | wx.EXPAND, 0)
        src_langSizer.AddSpacer(10)
        src_langSizer.Add(self.src_langCombo, 0, wx.ALL | wx.EXPAND, 0)

        # Destination Language
        dest_langSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.dest_langText = wx.StaticText(
            self, wx.ID_ANY, "Destination Language")
        self.dest_langText.SetForegroundColour(TEXT_COLOR)
        self.dest_langText.SetFont(wx.Font(LABEL_SIZE,
                                           wx.FONTFAMILY_DEFAULT,
                                           wx.FONTSTYLE_NORMAL,
                                           wx.FONTWEIGHT_NORMAL, 0, ""))

        self.dest_langCombo = wx.ComboBox(
            self, wx.ID_ANY, choices=[], style=wx.CB_DROPDOWN | wx.CB_SORT)
        self.dest_langCombo.SetBackgroundColour(BACKGROUND_COLOR)
        self.dest_langCombo.SetForegroundColour(TEXT_COLOR)  # For text
        self.dest_langCombo.SetFont(wx.Font(LABEL_SIZE,
                                            wx.FONTFAMILY_DEFAULT,
                                            wx.FONTSTYLE_NORMAL,
                                            wx.FONTWEIGHT_NORMAL, 0, ""))
        self.dest_langCombo.Bind(wx.EVT_COMBOBOX, self.update_dest_lang)

        dest_langSizer.Add(self.dest_langText, 0, wx.ALL, 0)
        dest_langSizer.AddSpacer(10)
        dest_langSizer.Add(self.dest_langCombo, 0, wx.ALL, 0)

        # Translator
        translatorSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.translatorText = wx.StaticText(self, wx.ID_ANY, "Translator")
        self.translatorText.SetForegroundColour(TEXT_COLOR)
        self.translatorText.SetFont(wx.Font(LABEL_SIZE,
                                            wx.FONTFAMILY_DEFAULT,
                                            wx.FONTSTYLE_NORMAL,
                                            wx.FONTWEIGHT_NORMAL, 0, ""))

        self.translatorCombo = wx.ComboBox(self, wx.ID_ANY,
                                           choices=["Deepl", "Google"],
                                           style=wx.CB_DROPDOWN | wx.CB_SORT)
        self.translatorCombo.SetBackgroundColour(BACKGROUND_COLOR)
        self.translatorCombo.SetForegroundColour(TEXT_COLOR)  # For text
        self.translatorCombo.SetFont(wx.Font(LABEL_SIZE,
                                             wx.FONTFAMILY_DEFAULT,
                                             wx.FONTSTYLE_NORMAL,
                                             wx.FONTWEIGHT_NORMAL, 0, ""))
        self.translatorCombo.Bind(wx.EVT_COMBOBOX, self.update_translator)

        translatorSizer.Add(self.translatorText, 0, wx.ALL | wx.EXPAND, 0)
        translatorSizer.AddSpacer(10)
        translatorSizer.Add(self.translatorCombo, 0, wx.ALL | wx.EXPAND, 0)

        # OCR
        ocrSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.ocrText = wx.StaticText(self, wx.ID_ANY, "OCR")
        self.ocrText.SetForegroundColour(TEXT_COLOR)
        self.ocrText.SetFont(wx.Font(LABEL_SIZE, wx.FONTFAMILY_DEFAULT,
                             wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, ""))

        self.ocrCombo = wx.ComboBox(self, wx.ID_ANY,
                                    choices=["Tesseract", "Easyocr"],
                                    style=wx.CB_DROPDOWN | wx.CB_SORT)
        self.ocrCombo.SetBackgroundColour(BACKGROUND_COLOR)
        self.ocrCombo.SetForegroundColour(TEXT_COLOR)  # For text
        self.ocrCombo.SetFont(wx.Font(LABEL_SIZE,
                                      wx.FONTFAMILY_DEFAULT,
                                      wx.FONTSTYLE_NORMAL,
                                      wx.FONTWEIGHT_NORMAL, 0, ""))
        self.ocrCombo.Bind(wx.EVT_COMBOBOX, self.update_ocr)

        ocrSizer.Add(self.ocrText, 0, wx.ALL | wx.EXPAND, 0)
        ocrSizer.AddSpacer(10)
        ocrSizer.Add(self.ocrCombo, 0, wx.ALL | wx.EXPAND, 0)

        # Button
        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.processButton = wx.Button(
            self, wx.ID_ANY, "Run processing", wx.DefaultPosition, wx.DefaultSize, 0)
        self.processButton.Bind(wx.EVT_BUTTON, self.process_image)
        self.processButton.SetForegroundColour(TEXT_COLOR)
        self.processButton.SetBackgroundColour(BACKGROUND_COLOR)

        buttonSizer.Add(self.processButton, 1, wx.ALL | wx.ALIGN_CENTER, 5)

        editSizer.Add(src_langSizer, 1, wx.ALL, 5)
        editSizer.Add(dest_langSizer, 1, wx.ALL, 5)
        editSizer.Add(translatorSizer, 1, wx.ALL, 5)
        editSizer.Add(ocrSizer, 1, wx.ALL, 5)
        editSizer.Add(buttonSizer, 1, wx.ALL | wx.ALIGN_CENTER, 5)

        mainSizer.Add(editSizer, 1, 0, 5)

        self.Bind(EVT_IMAGE_PROCESS, self.callback_image_process)

        self.SetSizer(mainSizer)
        self.Layout()

        self.Centre(wx.BOTH)

    def context_menu(self, event):
        """Event for display some context menu"""
        event.Skip()

    def open_file(self, event):
        """Open a file (transimg,png or jpg)"""
        event.Skip()
        self.img_file.path = None
        wildcard: str = """Open Image/Project Files (*.jpg;*jpeg;*.png,*.transimg)
        |*.jpeg;*.jpg;*.png;*.transimg|"""\
            "PNG file (*.png)|*.png|"\
            "JPG file (*.jpg;*.jpeg)|*.jpg;*.jpeg|"\
            "Transimg file (*.transimg)|*.transimg"
        with wx.FileDialog(self, "Open File", wildcard=wildcard,
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return

            file_path = fileDialog.GetPath()

            if file_path.endswith('transimg'):
                with open(file_path, 'rb') as file:
                    # Deserialize the file
                    self.img_file = pickle.load(file)

                self.img_file.path = file_path
                # Check deserialization
                if self.img_file.ocr is not None:
                    item = self.ocrCombo.FindString(self.img_file.ocr)
                    self.ocrCombo.SetSelection(item)

                if self.img_file.translator is not None:
                    item = self.translatorCombo.FindString(
                        self.img_file.translator)
                    self.translatorCombo.SetSelection(item)

                if self.img_file.src_lang is not None:
                    item = self.src_langCombo.FindString(
                        TO_LANG_NAME[self.img_file.src_lang])
                    if item != -1:
                        self.src_langCombo.SetSelection(item)
                    else:
                        wx.MessageDialog(None, "The source language in the doesn't installed",
                                         'Error', wx.OK | wx.ICON_EXCLAMATION).ShowModal()

                if self.img_file.dest_lang is not None:
                    item = self.dest_langCombo.FindString(
                        TO_LANG_NAME[self.img_file.dest_lang])
                    if item != -1:
                        self.dest_langCombo.SetSelection(item)
                    else:
                        wx.MessageDialog(None, """The destination language in the
                                          doesn't installed""",
                                         'Error', wx.OK | wx.ICON_EXCLAMATION).ShowModal()

                # Clear canvas and display image and text
                self.imageCanvas.clear()
                self.imageCanvas.set_image(self.img_file.img)
                self.imageCanvas.add_text_from_list(self.img_file.text_list)

                # Create image_translator object
                self.image_translator = ImageTranslator(self.img_file.img,
                                                        self.img_file.ocr,
                                                        self.img_file.translator,
                                                        self.img_file.src_lang,
                                                        self.img_file.dest_lang)
                # Set the img of image translator
                self.image_translator.img_process = self.img_file.img
                self.image_translator.img_out = self.img_file.img
                self.image_translator.text = self.img_file.text_list

            else:
                # Read the img from file
                self.img_file.img = cv2.imread(file_path)
                self.img_file.path = file_path

                # Clear canvas and set img
                self.imageCanvas.clear()
                self.imageCanvas.set_image(self.img_file.img)

    def save_file(self, event):
        """ Save the file"""
        self.img_file.text_list = self.imageCanvas.text[0]

        if self.image_translator is not None:
            self.img_file.img = self.image_translator.img_process

        shift = wx.GetKeyState(wx.WXK_SHIFT)
        if not shift:  # Normal save
            if self.img_file.path is None:  # Save
                self.save_file_dialog()
            else:  # Write to the opened file
                with open(self.img_file.path, 'wb') as file:
                    pickle.dump(self.img_file, file)
        else:  # Save as
            self.save_as_file_dialog()

    def save_as_file_dialog(self):
        """ Save as file"""
        wildcard: str = "Transimg File (*.transimg)|*.transimg"
        with wx.FileDialog(self, "Save Transimg File", wildcard=wildcard,
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            self.img_file.name = fileDialog.GetFilename()
            self.img_file.path = fileDialog.GetPath()
            with open(fileDialog.GetPath(), 'wb') as file:
                pickle.dump(self.img_file, file)

    def save_image_file(self, event):
        """Save an image file"""
        event.Skip()
        # Translate the image
        log.debug('Start the translation of image')
        # Set text from canvas to translator
        self.image_translator.text = self.imageCanvas.text[0]

        # Process the translate
        self.processImage = ImageProcess(self, self.img_file, self.settings['gpu'])
        self.processImage.image_translator = self.image_translator
        self.process_image.image_translator.gpu = self.settings['gpu']
        self.processImage.mode_process = False
        self.processImage.start()

        # Progressing dialog
        self.progressDialog = ProgressingDialog(self)
        if self.progressDialog.ShowModal() == wx.ID_CANCEL:
            self.processImage.abort()

    def about_menu(self, event):
        event.Skip()
        print('about_menu')

    def help_menu(self, event):
        event.Skip()
        print('help_menu')

    def settings_menu(self, event):
        """ Open settings menu"""
        event.Skip()
        dlg = SettingsDialog(self)
        if dlg.ShowModal() == wx.ID_OK:
            # Clear the combo box
            # Save current language selection before clear
            src_lang: str = self.src_langCombo.GetStringSelection()
            dest_lang: str =  self.dest_langCombo.GetStringSelection() 
            self.src_langCombo.Clear()
            self.dest_langCombo.Clear()
            # Append the existing language to combo box
            for lang in dlg.settings['language_pack']:
                if dlg.settings['language_pack'][lang]:
                    self.dest_langCombo.Append(TO_LANG_NAME[lang].capitalize())
                    self.src_langCombo.Append(TO_LANG_NAME[lang].capitalize())
            # Write the settings file
            with open(SETTINGS_FILE, 'w') as settings_file:
                json.dump(dlg.settings, settings_file)

            item = self.src_langCombo.FindString(src_lang)
            if item != -1:
                self.src_langCombo.SetSelection(item)

            item = self.dest_langCombo.FindString(dest_lang)
            if item != -1:
                self.dest_langCombo.SetSelection(item)


    def update_translator(self, event):
        """Update the translator into img file"""
        string: str = event.String.lower()
        self.img_file.translator = string

    def update_ocr(self, event):
        """Update the ocr into img file"""
        string: str = event.String.lower()
        self.img_file.ocr = string

    def update_src_lang(self, event):
        """Update the source language into img file"""
        string: str = event.String.lower()
        self.img_file.src_lang = TO_LANG_CODE[string]

    def update_dest_lang(self, event):
        """Update the destimation language into img file"""
        string: str = event.String.lower()
        self.img_file.dest_lang = TO_LANG_CODE[string]

    def callback_image_process(self, event):
        """Callback after image processing or translating"""
        # Close the dialog
        self.progressDialog.Close()
        # Get the image_translator
        self.image_translator = event.data[0]

        # If it's a processing or translating
        if self.processImage.mode_process:
            log.debug('End of the processing')
            self.imageCanvas.clear()
            self.imageCanvas.set_image(self.image_translator.img_process)
            self.imageCanvas.add_text_from_list(self.image_translator.text)
        else:  # Saving image
            log.debug('Saving the image')
            wildcard: str = "JPG Files (*.jpg)|*.jpg|PNG files (*.png)|*.png"
            with wx.FileDialog(self, "Save Image File", wildcard=wildcard,
                               style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
                               defaultFile=self.img_file.name) as fileDialog:

                if fileDialog.ShowModal() == wx.ID_CANCEL:
                    return
                cv2.imwrite(fileDialog.GetPath(),
                            self.image_translator.img_out)

    def process_image(self, event):
        """Method to prepare the processing of image"""
        log.debug('Start the processing of image')

        # Check some errors
        if self.img_file.src_lang == self.img_file.dest_lang:
            wx.MessageDialog(None, 'The source and destination lang cannot be the same',
                             'Error', wx.OK | wx.ICON_EXCLAMATION).ShowModal()
        elif (self.img_file.src_lang == '' or self.img_file.dest_lang == ''
              or self.img_file.translator == '' or self.img_file.ocr == ''):
            wx.MessageDialog(None, 'One on the combox are empty',
                             'Error', wx.OK | wx.ICON_EXCLAMATION).ShowModal()
        elif self.img_file.path == '':
            wx.MessageDialog(None, 'Any image or file are open',
                             'Error', wx.OK | wx.ICON_EXCLAMATION).ShowModal()
        else:
            self.processImage = ImageProcess(self, self.img_file, self.settings['gpu'])
            self.processImage.start()

            self.progressDialog = ProgressingDialog(self)
            if self.progressDialog.ShowModal() == wx.ID_CANCEL:
                self.processImage.abort()
