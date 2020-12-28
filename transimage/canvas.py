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

import logging

import cv2
import numpy as np
import wx
from wx.lib.floatcanvas import FloatCanvas
from wx.lib.floatcanvas.FCObjects import ScaledTextBox

from transimage.config import BACKGROUND_COLOR, TEXT_COLOR

log = logging.getLogger('transimage')

wx.Font.AddPrivateFont('font/Cantarell.ttf')

EvtCanvasContextMenu, EVT_CANVAS_CONTEXT_MENU = wx.lib.newevent.NewEvent()

class EditDialog (wx.Dialog):

    def __init__(self,parent,font):
        wx.Dialog.__init__ (self,parent,id=wx.ID_ANY,title="Edit",pos=wx.DefaultPosition,size=wx.Size(400,200),style=wx.DEFAULT_DIALOG_STYLE)

        self.SetSizeHints(wx.DefaultSize,wx.DefaultSize)
        self.SetForegroundColour(BACKGROUND_COLOR)
        self.SetBackgroundColour(BACKGROUND_COLOR)
        self.SetMinSize(wx.Size(400,200))


        mainSizer = wx.BoxSizer(wx.VERTICAL)

        sizeSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.sizeText = wx.StaticText(self,wx.ID_ANY, "Size",wx.DefaultPosition,wx.DefaultSize,wx.ALIGN_LEFT)
        self.sizeText.SetForegroundColour(TEXT_COLOR)
        self.sizeText.Wrap(-1)

        sizeSizer.Add(self.sizeText,0,wx.ALL,5)

        self.sizeSpinCtrl = wx.SpinCtrl(self,wx.ID_ANY,wx.EmptyString,wx.DefaultPosition,wx.DefaultSize,0)
        self.sizeSpinCtrl.SetForegroundColour(TEXT_COLOR)
        self.sizeSpinCtrl.SetBackgroundColour(BACKGROUND_COLOR)
        self.sizeSpinCtrl.SetMax(100000)
        self.sizeSpinCtrl.SetMin(1)
        self.sizeSpinCtrl.Bind(wx.EVT_SPINCTRL,self.set_size)
        sizeSizer.Add(self.sizeSpinCtrl,0,wx.ALL,5)

        sizeSizer.Add((0,0),1,wx.EXPAND,5)

        self.widthText = wx.StaticText(self,wx.ID_ANY,"Width",wx.DefaultPosition,wx.DefaultSize,0)
        self.widthText.SetForegroundColour(TEXT_COLOR)
        self.widthText.Wrap(-1)

        sizeSizer.Add(self.widthText,0,wx.ALL,5)

        self.widthSpinCtrl =wx.SpinCtrl(self,wx.ID_ANY,wx.EmptyString,wx.DefaultPosition,wx.DefaultSize,0)
        self.widthSpinCtrl.SetForegroundColour(TEXT_COLOR)
        self.widthSpinCtrl.SetBackgroundColour(BACKGROUND_COLOR)
        self.widthSpinCtrl.SetMax(100000)
        self.widthSpinCtrl.SetMin(1)
    
        sizeSizer.Add(self.widthSpinCtrl,0,wx.ALL,5)

        mainSizer.Add(sizeSizer,1,wx.EXPAND,5)

        textSizer = wx.BoxSizer(wx.VERTICAL)

        self.textText = wx.StaticText(self,wx.ID_ANY,"Text",wx.DefaultPosition,wx.DefaultSize,0)
        self.textText.SetForegroundColour(TEXT_COLOR)

        self.textText.Wrap(-1)

        textSizer.Add(self.textText,0,wx.ALL,5)

        #Change for ExpandoTextCtrl in wx.lib.expando
        self.textTextCtrl = wx.TextCtrl(self,wx.ID_ANY,wx.EmptyString,wx.DefaultPosition,wx.DefaultSize,wx.TE_MULTILINE)
        self.textTextCtrl.SetForegroundColour(TEXT_COLOR)
        self.textTextCtrl.SetBackgroundColour(BACKGROUND_COLOR)
        self.textTextCtrl.SetFont(font)

        textSizer.Add(self.textTextCtrl,1,wx.ALL|wx.EXPAND,5)

        mainSizer.Add(textSizer,2,wx.EXPAND,5)

        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.okButton = wx.Button(self,wx.ID_OK,"OK",wx.DefaultPosition,wx.DefaultSize,0)
        self.okButton.SetForegroundColour(TEXT_COLOR)
        self.okButton.SetBackgroundColour(BACKGROUND_COLOR)
        buttonSizer.Add(self.okButton,1,wx.ALIGN_CENTER|wx.ALL,5)

        self.cancelButton = wx.Button(self,wx.ID_CANCEL,"Cancel",wx.DefaultPosition,wx.DefaultSize,0)
        self.cancelButton.SetForegroundColour(TEXT_COLOR)
        self.cancelButton.SetBackgroundColour(BACKGROUND_COLOR)
        buttonSizer.Add(self.cancelButton,1,wx.ALIGN_CENTER|wx.ALL,5)

        mainSizer.Add(buttonSizer,1,wx.EXPAND,5)

        self.SetSizer(mainSizer)
        self.Layout()
        self.Fit()

        self.Centre(wx.BOTH)

    def set_size(self,event):
        # self.font=wx.Font(self.sizeSpinCtrl.GetValue(), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "Cantarell")
        # self.textTextCtrl.SetFont(self.font)
        # self.Fit()
        event.Skip()

class ContextMenu(wx.Menu):

    def __init__(self, parent,pos,type=0,text=None):
        super(ContextMenu, self).__init__()

        self.parent = parent
        self.font=wx.Font(30, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "Cantarell")
        self.pos=pos
        self.text=text

        add_text = wx.MenuItem(self, wx.NewIdRef(), 'Add Text')
        self.Append(add_text)
        self.Bind(wx.EVT_MENU, self.add_text, add_text)

        if type>=1:
            edit_text = wx.MenuItem(self, wx.NewIdRef(), 'Edit Text')
            self.Append(edit_text)
            self.Bind(wx.EVT_MENU, self.edit_text, edit_text)
        if type >=2:
            delete_text = wx.MenuItem(self, wx.NewIdRef(), 'Delete Text')
            self.Append(delete_text)
            self.Bind(wx.EVT_MENU, self.delete_text, delete_text)
        
    def add_text(self, event):
       dlg = EditDialog(self.parent,self.font)
       dlg.SetTitle('Add')
       dlg.sizeSpinCtrl.SetValue(30)
       dlg.widthSpinCtrl.SetValue(50)

       if dlg.ShowModal()==wx.ID_OK:
            evt = EvtCanvasContextMenu(data={
                'event_type':'add_text',
                'event_data':{
                    'width':dlg.widthSpinCtrl.GetValue(),
                    'size':dlg.sizeSpinCtrl.GetValue(),
                    'string':dlg.textTextCtrl.GetValue(),
                    'pos':(0,0)
                }
            })
            wx.PostEvent(self.parent, evt)
    def edit_text(self,event):
        evt = EvtCanvasContextMenu(data={
                'event_type':'edit_text',
                'event_data':self.text
            })
        wx.PostEvent(self.parent, evt)
    def delete_text(self,event):
        evt = EvtCanvasContextMenu(data={
                'event_type':'delete_text',
                'event_data':self.text
            })
        wx.PostEvent(self.parent, evt)

class DisplayCanvas(FloatCanvas.FloatCanvas):

    def __init__(self, *args, **kwargs):
        FloatCanvas.FloatCanvas.__init__(self, *args, **kwargs)
        self.text=[]

        #Canvas Event
        self.Bind(wx.EVT_MOUSEWHEEL,self.zoom)
        self.Bind(FloatCanvas.EVT_LEFT_UP, self.stop_move)
        self.Bind(FloatCanvas.EVT_MOTION, self.moving)
        self.Bind(FloatCanvas.EVT_RIGHT_DOWN,self.context_menu)
        self.Bind(EVT_CANVAS_CONTEXT_MENU, self.callback_context_menu)


        self.Show()
        self.ZoomToBB()
        self.delta = 1.2
        self.MoveObject = None
        self.Moving = False

    def context_menu(self,event):
        if isinstance(event,wx.PyCommandEvent):
            pos=event.GetPosition()
            self.PopupMenu(ContextMenu(self,pos), pos)
        elif isinstance(event,ScaledTextBox):
            pos=wx.GetMousePosition() - self.GetScreenPosition() 
            self.PopupMenu(ContextMenu(self,pos,2,event), pos)

    def clear(self):
        self.ClearAll()
        self.text.clear()
        self.Draw(True)

    def delete_text(self,text,Force=True):
        self.RemoveObject(text)
        self.Draw(Force)

    def delete_all_text(self):
        for text in self.text:
            self.delete_text(text,False)
        self.Draw(True) 

    def callback_context_menu(self,event):
        if event.data['event_type']=='add_text':
            data=event.data['event_data']
            self.add_text(data['string'],'',data['pos'],data['width'],data['size'])
        elif event.data['event_type']=='edit_text':
            data=event.data['event_data']
            font=data.Font
            font.SetPointSize(data.Size)
            dlg = EditDialog(self,font)

            dlg.textTextCtrl.SetValue(data.String)
            dlg.widthSpinCtrl.SetValue(data.Width)
            dlg.sizeSpinCtrl.SetValue(data.Size)
            if dlg.ShowModal()==wx.ID_OK:
                data.SetText(dlg.textTextCtrl.GetValue())
                data.Size=dlg.sizeSpinCtrl.GetValue()
                data.Width=dlg.widthSpinCtrl.GetValue()
                self.Draw(True)
        elif event.data['event_type']=='delete_text':
            data=event.data['event_data']
            self.delete_text(data)

    def add_text(self,string,translated_string,pos,width,size):
        text=self.AddScaledTextBox(
                String=string,
                Point=pos,
                Size=size,
                Color = "Black",
                BackgroundColor = "White",
                LineStyle = "Transparent",
                Width = width,
                Position = 'tl',
                LineSpacing = 1,
                Alignment = "left",
                Font=wx.Font(size, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "Cantarell"))
        text.Bind(FloatCanvas.EVT_FC_LEFT_DOWN, self.start_move)
        text.Bind(FloatCanvas.EVT_FC_LEFT_DCLICK,self.edit_text)
        text.Bind(FloatCanvas.EVT_FC_RIGHT_DOWN,self.context_menu)

        self.text.append( {
                'original_text':string,
                'original_translated':translated_string,
                'text_object':text
            })
        self.Draw(True)

    def update_image(self,image):
        #For PIL Image
        # self.img=wx.EmptyImage(image.size[0],image.size[1])
        # self.img.setData(image.convert("RGB").tostring())
        # self.img.setAlphaData(image.convert("RGBA").tostring()[3::4])

        # self.bmp = wx.BitmapFromImage(self.img)

        # self.AddScaledBitmap(self.img,(10,10),image.size[1],'cc')
        height, width = image.shape[:2]
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        self.bmp = wx.Bitmap.FromBuffer(width, height, image)
        self.AddScaledBitmap(self.bmp,(0,0),height,'tl')

        self.Draw(True)
        self.ZoomToBB()

    def edit_text(self,event):
        string=event.String
        font=event.Font
        font.SetPointSize(event.Size)
        dlg = EditDialog(self,font)

        dlg.textTextCtrl.SetValue(string)
        dlg.widthSpinCtrl.SetValue(event.Width)
        dlg.sizeSpinCtrl.SetValue(event.Size)
        if dlg.ShowModal()==wx.ID_OK:
            event.SetText(dlg.textTextCtrl.GetValue())
            event.Size=dlg.sizeSpinCtrl.GetValue()
            event.Width=dlg.widthSpinCtrl.GetValue()
            self.Draw(True)

    def zoom(self, wheel):
        #http://wxpython-users.1045709.n5.nabble.com/Hold-shift-ctrl-mouse-click-td2363641.html
        ctrl=wheel.ControlDown()
        shift=wheel.ShiftDown()
        if ctrl:
            if wheel.WheelRotation==-120: #Scroll down
                self.Zoom(1/self.delta)
            elif wheel.WheelRotation==120: #Scroll up
                self.Zoom(self.delta)
            self.Draw(True)
        elif shift:
            Rot = wheel.GetWheelRotation()
            Rot = Rot / abs(Rot) * 0.1
            if wheel.ControlDown(): # move up-down
                self.MoveImage( (0, Rot), "Panel" )
            else: # move up-down
                self.MoveImage( (Rot, 0), "Panel" )
        else:
            Rot = wheel.GetWheelRotation()
            Rot = Rot / abs(Rot) * 0.1
            if wheel.ControlDown(): # move left-right
                self.MoveImage( (Rot, 0), "Panel" )
            else: # move up-down
                self.MoveImage( (0, Rot), "Panel" )

    def start_move(self, object):
        if not self.Moving:
            self.Moving = True
            self.StartPoint = object.HitCoordsPixel
            BB=object.BoundingBox
            OutlinePoints = np.array( ( (BB[0,0], BB[0,1]),
                                    (BB[0,0], BB[1,1]),
                                    (BB[1,0], BB[1,1]),
                                    (BB[1,0], BB[0,1]),
                                 )
                               )
            self.StartObject = self.WorldToPixel(OutlinePoints)
            self.MoveObject = None
            self.MovingObject = object

    def moving(self, event):
        """
        Updates the status bar with the world coordinates
        and moves the object it is clicked on
        """
        if self.Moving:
            dxy = event.GetPosition() - self.StartPoint
            # Draw the Moving Object:
            dc = wx.ClientDC(self)
            dc.SetPen(wx.Pen('WHITE', 2, wx.SHORT_DASH))
            dc.SetBrush(wx.TRANSPARENT_BRUSH)
            dc.SetLogicalFunction(wx.XOR)
            if self.MoveObject is not None:
                dc.DrawPolygon(self.MoveObject)
            self.MoveObject = self.StartObject + dxy
            dc.DrawPolygon(self.MoveObject)

    def stop_move(self, event):
        if self.Moving:
            self.Moving = False
            if self.MoveObject is not None:
                dxy = event.GetPosition() - self.StartPoint
                dxy = self.ScalePixelToWorld(dxy)
                self.MovingObject.Move(dxy)
                self.MoveTri = None
            self.Draw(True)
