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

import wx
import wx.lib.agw.flatnotebook as agw_flatnotebook
from transimage.lang import LANG,LANG_DICT
from transimage.config import BACKGROUND_COLOR,TEXT_COLOR

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

        # self.lang_CheckList.SetItemBackgroundColour(0, BACKGROUND_COLOR)
        # self.lang_CheckList.SetItemForegroundColour(0,TEXT_COLOR)

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

        for lang in LANG:
            self.lang_CheckList.Append(lang.capitalize())
           
        for i in range(self.lang_CheckList.GetCount()):
            self.lang_CheckList.SetItemBackgroundColour(i,BACKGROUND_COLOR)
            self.lang_CheckList.SetItemForegroundColour(i,TEXT_COLOR)


    def apply(self,event):
        #Format the CheckListBox to a dict
        checked_lang={}
        for item in range(self.lang_CheckList.GetCount()):
            string =self.lang_CheckList.GetString(item)
            string = string[0].lower() + string[1:]
            checked=self.lang_CheckList.IsChecked(item)
            checked_lang[LANG[string]]=checked