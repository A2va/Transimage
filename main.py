import wx
from transimage.transimage import Transimage

app = wx.App()
transimage = Transimage(None)
transimage.Show()
app.MainLoop()