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

import json
import os
from urllib.request import urlretrieve
from zipfile import ZipFile

import easyocr.config as easyocr_lang
import image_translator.utils.lang as image_translator_lang
import wx
from wx.core import ALIGN_CENTER
import wx.lib.agw.flatnotebook as agw_flatnotebook

from transimage.config import (BACKGROUND_COLOR, LABEL_SIZE, SETTINGS_FILE,
                               TEXT_COLOR)
from transimage.lang import  TO_LANG_CODE, TO_LANG_NAME

TESSDATA='https://github.com/tesseract-ocr/tessdata/raw/master'
TESSDATA_BEST='https://github.com/tesseract-ocr/tessdata_best/raw/master'

class SettingsDialog(wx.Dialog):
    def __init__(self,parent):
        wx.Dialog.__init__ (self,parent,id=wx.ID_ANY,title="Settings",pos=wx.DefaultPosition,size=wx.Size(400,300),style=wx.DEFAULT_DIALOG_STYLE)

        self.SetSizeHints(wx.DefaultSize,wx.DefaultSize)
        self.SetForegroundColour(BACKGROUND_COLOR)
        self.SetBackgroundColour(BACKGROUND_COLOR)
        self.SetMinSize(wx.Size(400,300))

        mainSizer = wx.BoxSizer(wx.VERTICAL)

        self.notebook = agw_flatnotebook.FlatNotebook(self, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize,style=0, 
                        agwStyle=agw_flatnotebook.FNB_NO_NAV_BUTTONS|agw_flatnotebook.FNB_NO_X_BUTTON
                        |agw_flatnotebook.FNB_NODRAG |agw_flatnotebook.FNB_FANCY_TABS|agw_flatnotebook.FNB_TABS_BORDER_SIMPLE, name="FlatNotebook")
        self.notebook.SetActiveTabTextColour(TEXT_COLOR)
        self.notebook.SetNonActiveTabTextColour(TEXT_COLOR)
        self.notebook.SetTabAreaColour(BACKGROUND_COLOR)
        self.notebook.SetActiveTabColour(BACKGROUND_COLOR)
        self.notebook.SetGradientColours(BACKGROUND_COLOR,BACKGROUND_COLOR,BACKGROUND_COLOR)
        mainSizer.Add(self.notebook, 1, wx.EXPAND, 0)

        # Page 1: General 

        page1Sizer = wx.BoxSizer(wx.VERTICAL)
        self.page_1 = wx.Panel(self.notebook, wx.ID_ANY)
        self.page_1.SetForegroundColour(BACKGROUND_COLOR)
        self.page_1.SetBackgroundColour(BACKGROUND_COLOR)
        self.notebook.AddPage(self.page_1, "General")

        self.page_1Text = wx.StaticText(self.page_1, wx.ID_ANY, "Nothing to see in this page")
        self.page_1Text.SetForegroundColour(TEXT_COLOR)
        self.page_1Text.SetFont(wx.Font(20, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, ""))
        page1Sizer.Add(self.page_1Text,1,wx.ALL|wx.ALIGN_CENTER,5)

        self.page_1.SetSizer(page1Sizer)

        # Page 2: Language Pack

        page2Sizer = wx.BoxSizer(wx.VERTICAL)
        self.page_2 = wx.Panel(self.notebook, wx.ID_ANY)
        self.page_2.SetForegroundColour(BACKGROUND_COLOR)
        self.page_2.SetBackgroundColour(BACKGROUND_COLOR)
        self.notebook.AddPage(self.page_2, "Language Pack")

        self.lang_CheckList =wx.CheckListBox(self.page_2, wx.ID_ANY,style=wx.LB_SORT)
        self.lang_CheckList.SetBackgroundColour(BACKGROUND_COLOR)
        self.lang_CheckList.SetForegroundColour(BACKGROUND_COLOR)

        page2Sizer.Add(self.lang_CheckList,1,wx.ALL|wx.EXPAND,5)

        self.applyButton = wx.Button(self.page_2,wx.ID_ANY,"Apply",wx.DefaultPosition,wx.DefaultSize,0)
        self.applyButton.SetForegroundColour(TEXT_COLOR)
        self.applyButton.SetBackgroundColour(BACKGROUND_COLOR)
        self.applyButton.Bind(wx.EVT_BUTTON,self.apply)

        page2Sizer.Add(self.applyButton,0,wx.ALIGN_RIGHT|wx.ALL,5)

        self.page_2.SetSizer(page2Sizer)

        # Confirmation Button

        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.okButton = wx.Button(self,wx.ID_OK,"OK",wx.DefaultPosition,wx.DefaultSize,0)
        self.okButton.SetForegroundColour(TEXT_COLOR)
        self.okButton.SetBackgroundColour(BACKGROUND_COLOR)
        buttonSizer.Add(self.okButton,1,wx.ALIGN_CENTER|wx.ALL,5)

        self.cancelButton = wx.Button(self,wx.ID_CANCEL,"Cancel",wx.DefaultPosition,wx.DefaultSize,0)
        self.cancelButton.SetForegroundColour(TEXT_COLOR)
        self.cancelButton.SetBackgroundColour(BACKGROUND_COLOR)
        buttonSizer.Add(self.cancelButton,1,wx.ALIGN_CENTER|wx.ALL,5)

        mainSizer.Add(buttonSizer, 0, wx.ALIGN_RIGHT | wx.ALL, 5)
        self.SetSizer(mainSizer)

        self.Layout()

        self.Centre(wx.BOTH)

        for lang in TO_LANG_NAME:
            self.lang_CheckList.Append(TO_LANG_NAME[lang].capitalize())

        with open(SETTINGS_FILE,'r') as settings_file:
            self.settings=json.load(settings_file)
            for item in range(self.lang_CheckList.GetCount()):
                string =self.lang_CheckList.GetString(item).lower()
                checked=self.settings['language_pack'][TO_LANG_CODE[string]]
                self.lang_CheckList.Check(item,checked)
    
                self.lang_CheckList.SetItemBackgroundColour(item,BACKGROUND_COLOR)
                self.lang_CheckList.SetItemForegroundColour(item,TEXT_COLOR)


    def apply(self,event):
        #Format the CheckListBox to a dict
        checked_lang={}
        for item in range(self.lang_CheckList.GetCount()):
            string =self.lang_CheckList.GetString(item).lower()
            checked=self.lang_CheckList.IsChecked(item)
            checked_lang[TO_LANG_CODE[string]]=checked

        differences = self.settings['language_pack'].items() -  checked_lang.items()
        for diff in differences:
            checked=checked_lang[diff[0]]
            if checked:
                download_lang(diff[0],self)

        #Save the new settings into json file        
        self.settings['language_pack']=checked_lang
        with open(SETTINGS_FILE,'w') as settings_file:
            json.dump(self.settings,settings_file)

def download_lang(lang,parent):
  
    tesseract_url=f'{TESSDATA_BEST}/{lang}.traineddata'

    lang_code_tesseract=image_translator_lang.OCR_LANG[lang][0]
    if lang_code_tesseract != 'invalid':
        if not os.path.exists(f'tesseract-ocr/tessdata/{lang_code_tesseract}.traineddata'):
            progress_dialog=wx.ProgressDialog('Language pack',f'{TO_LANG_NAME[lang].capitalize()}: Tesseract Model',maximum=100,parent=parent)
            download(tesseract_url,'tesseract-ocr/tessdata',progress_dialog)
            progress_dialog.Destroy()


    lang_code_easyocr=image_translator_lang.OCR_LANG[lang][1]
    if lang_code_easyocr != 'invalid':

        if not os.path.exists('./easyocr'):
            os.makedirs('easyocr/model')

        file=''
        if lang_code_easyocr in easyocr_lang.latin_lang_list:
            file='latin.pth'
        elif lang_code_easyocr in easyocr_lang.arabic_lang_list:
            file='arabic.pth'
        elif lang_code_easyocr in easyocr_lang.bengali_lang_list:
            file='bengali.pth'
        elif lang_code_easyocr in easyocr_lang.cyrillic_lang_list:
            file='cyrillic.pth'
        elif lang_code_easyocr in easyocr_lang.devanagari_lang_list:
            file='devanagari.pth'
        elif lang_code_easyocr == 'th':
            file='thai.pth'
        elif lang_code_easyocr == 'ch_sim':
            file='chinese_sim.pth'
        elif lang_code_easyocr == 'ch_tra':
            file='chinese.pth'
        elif lang_code_easyocr == 'ja':
            file='japanese.pth'
        elif lang_code_easyocr == 'ko':
            file='korean.pth'
        elif lang_code_easyocr == 'ta':
            file='tamil.path'
        elif lang_code_easyocr == 'te':
            file='telegu.pth'
        elif lang_code_easyocr == 'kn':
            file='kannada.pth'

        if file != '' and not os.path.exists(f'easyocr/model/{file}'):
            url= easyocr_lang.model_url[file][0]
            progress_dialog=wx.ProgressDialog('Language pack',f'{TO_LANG_NAME[lang].capitalize()}: EasyOCR model',maximum=100,parent=parent)
            download(url,'easyocr/model',progress_dialog,file)
            progress_dialog.Destroy()

def download(url, path,progress_dialog,filename=None):

    if filename is not None:
        file = os.path.join(path, 'temp.zip')
        urlretrieve(url, file,reporthook=progress_bar(progress_dialog))
        with ZipFile(file, 'r') as zipObj:
            zipObj.extract(filename, path)
        os.remove(file)
    else:
        file = os.path.join(path,url.split('/')[-1])
        urlretrieve(url, file,reporthook=progress_bar(progress_dialog))


def progress_bar(progress_dialog):
    def progress_hook(count, block_size, total_size):
        progress_size = int(count * block_size)
        
        percent = min(int(count*block_size*100/total_size),100)
        progress_dialog.Update(percent)

    return progress_hook
