import wx
import cv2
import numpy as np
from wx.lib.floatcanvas.FCObjects import ScaledTextBox
from wx.lib.floatcanvas import FloatCanvas



class EditDialog(wx.Dialog):
    def __init__(self, *args, **kwds):
        # begin wxGlade: MyDialog.__init__
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_DIALOG_STYLE
        wx.Dialog.__init__(self, *args, **kwds)
        self.SetTitle("Edit")
        sizer_1 = wx.BoxSizer(wx.VERTICAL)

        static_text_1 = wx.StaticText(self, wx.ID_ANY, "Enter text:")
        sizer_1.Add(static_text_1, 0, wx.ALL, 8)

        self.text_ctrl_1 = wx.TextCtrl(self, wx.ID_ANY, "",style = wx.TE_MULTILINE)
        sizer_1.Add(self.text_ctrl_1, 0, wx.ALL | wx.EXPAND, 8)

        sizer_1.Add((20, 20), 1, wx.EXPAND, 0)

        sizer_2 = wx.StdDialogButtonSizer()
        sizer_1.Add(sizer_2, 0, wx.ALIGN_RIGHT | wx.ALL, 4)

        self.button_OK = wx.Button(self, wx.ID_OK, "")
        self.button_OK.SetDefault()
        sizer_2.AddButton(self.button_OK)

        self.button_CANCEL = wx.Button(self, wx.ID_CANCEL, "")
        sizer_2.AddButton(self.button_CANCEL)

        sizer_2.Realize()

        self.SetSizer(sizer_1)
        sizer_1.Fit(self)

        self.SetAffirmativeId(self.button_OK.GetId())
        self.SetEscapeId(self.button_CANCEL.GetId())

        self.CenterOnParent()
        self.Layout()

class DisplayCanvas(FloatCanvas.FloatCanvas):

    def __init__(self, *args, **kwargs):
        FloatCanvas.FloatCanvas.__init__(self, *args, **kwargs)
        self.text=[]
        # Add the Canvas
      


        #Canvas Event
        self.Bind(wx.EVT_MOUSEWHEEL,self.zoom)
        self.Bind(FloatCanvas.EVT_LEFT_UP, self.stop_move)
        self.Bind(FloatCanvas.EVT_MOTION, self.moving)

        wx.Font.AddPrivateFont('font/Cantarell.ttf')
        # self.Text = self.canvas.AddScaledTextBox(
        #                               String='This is a very very long string for test',
        #                               Point=(10,10),
        #                               Size=10,
        #                               Color = "Black",
        #                               BackgroundColor = None,
        #                               LineStyle = "Transparent",
        #                               Width = 50,
        #                               Position = 'tl',
        #                               LineSpacing = 0.9,
        #                               Alignment = "left",
        #                               Font=Font)

        self.Show()
        self.ZoomToBB()
        self.delta = 1.2
        self.MoveObject = None
        self.Moving = False

    def delete_text(self,text):
        self.RemoveObject(text)
        self.Draw(True)

    def add_text(self,string,pos,width,size):
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

        self.text.append(text)
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
        self.AddScaledBitmap(self.bmp,(10,10),width,'tl')

        self.Draw(True)
        self.ZoomToBB()

    def edit(self,event):
        # string=event.Words
        # string=' '.join(string)
        string=event.String
        dlg = EditDialog(self)
        dlg.text_ctrl_1.SetValue(string)
        if dlg.ShowModal()==wx.ID_OK:
            event.SetText(dlg.text_ctrl_1.GetValue())
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
