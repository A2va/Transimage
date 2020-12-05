import wx
import cv2
import numpy as np
from wx.lib.floatcanvas import FloatCanvas

class EditDialog ( wx.Dialog ):

    def __init__( self, parent ):
        wx.Dialog.__init__ (self,parent,id=wx.ID_ANY,title="Edit",pos=wx.DefaultPosition,size=wx.Size(400,200),style=wx.DEFAULT_DIALOG_STYLE)

        self.SetSizeHints(wx.DefaultSize,wx.DefaultSize)

        mainSizer = wx.BoxSizer(wx.VERTICAL)

        sizeSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.sizeText = wx.StaticText(self,wx.ID_ANY, "Size",wx.DefaultPosition,wx.DefaultSize,wx.ALIGN_LEFT)
        self.sizeText.Wrap(-1)

        sizeSizer.Add(self.sizeText,0,wx.ALL,5)

        self.sizeSpinCtrl = wx.SpinCtrl(self,wx.ID_ANY,wx.EmptyString,wx.DefaultPosition,wx.DefaultSize,0)
        sizeSizer.Add(self.sizeSpinCtrl,0,wx.ALL,5)

        sizeSizer.Add((0,0),1,wx.EXPAND,5)

        self.widthText = wx.StaticText(self,wx.ID_ANY,"Width",wx.DefaultPosition,wx.DefaultSize,0)
        self.widthText.Wrap(-1)

        sizeSizer.Add(self.widthText,0,wx.ALL,5)

        self.widthSpinCtrl =wx.SpinCtrl(self,wx.ID_ANY,wx.EmptyString,wx.DefaultPosition,wx.DefaultSize,0)
        sizeSizer.Add(self.widthSpinCtrl,0,wx.ALL,5)

        mainSizer.Add(sizeSizer,1,wx.EXPAND,5)

        textSizer = wx.BoxSizer(wx.VERTICAL)

        self.textText = wx.StaticText(self,wx.ID_ANY,"Text",wx.DefaultPosition,wx.DefaultSize,0)
        self.textText.Wrap(-1)
        textSizer.Add(self.textText,0,wx.ALL,5)

        self.textTextCtrl = wx.TextCtrl(self,wx.ID_ANY,wx.EmptyString,wx.DefaultPosition,wx.DefaultSize,wx.TE_MULTILINE)
        textSizer.Add(self.textTextCtrl,1,wx.ALL|wx.EXPAND,5)

        mainSizer.Add(textSizer,2,wx.EXPAND,5)

        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.okButton = wx.Button(self,wx.ID_OK,"OK",wx.DefaultPosition,wx.DefaultSize,0)
        buttonSizer.Add(self.okButton,1,wx.ALIGN_CENTER|wx.ALL,5)

        self.cancelButton = wx.Button(self,wx.ID_CANCEL,"Cancel",wx.DefaultPosition,wx.DefaultSize,0)
        buttonSizer.Add(self.cancelButton,1,wx.ALIGN_CENTER|wx.ALL,5)

        mainSizer.Add(buttonSizer,1,wx.EXPAND,5)

        self.SetSizer(mainSizer)
        self.Layout()

        self.Centre(wx.BOTH)

    def __del__( self ):
        pass

class DisplayCanvas(FloatCanvas.FloatCanvas):

    def __init__(self, *args, **kwargs):
        FloatCanvas.FloatCanvas.__init__(self, *args, **kwargs)
        self.text=[]



        #Canvas Event
        self.Bind(wx.EVT_MOUSEWHEEL,self.zoom)
        self.Bind(FloatCanvas.EVT_LEFT_UP, self.stop_move)
        self.Bind(FloatCanvas.EVT_MOTION, self.moving)

        wx.Font.AddPrivateFont('font/Cantarell.ttf')

        self.Show()
        self.ZoomToBB()
        self.delta = 1.2
        self.MoveObject = None
        self.Moving = False

    def delete_all(self):
        self.ClearAll()
        self.text.clear()
        self.Draw(True)

    def delete_text(self,text):
        self.RemoveObject(text)
        self.Draw(True)

    def add_text(self,string,translated_string,pos,width,size):
        text=self.AddScaledTextBox(
                String=string,
                Point=pos,
                Size=size,
                Color = "Black",
                BackgroundColor = None,
                LineStyle = "Transparent",
                Width = width,
                Position = 'tl',
                LineSpacing = 1,
                Alignment = "left",
                Font=wx.Font(size, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "Cantarell"))
        text.Bind(FloatCanvas.EVT_FC_LEFT_DOWN, self.start_move)
        text.Bind(FloatCanvas.EVT_FC_LEFT_DCLICK,self.edit)

        self.AddObject(text)

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

    def edit(self,event):
        string=event.String
        dlg = EditDialog(self)
        dlg.textTextCtrl.SetValue(string)
        dlg.widthTextCtrl.SetValue(str(event.Width))
        dlg.sizeTextCtrl.SetValue(str(event.Size))
        if dlg.ShowModal()==wx.ID_OK:
            event.SetText(dlg.textTextCtrl.GetValue())
            event.Size=dlg.sizeSpinCtrl.GetValue()
            event.Width=int(dlg.widthSpinCtrl.GetValue())
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
