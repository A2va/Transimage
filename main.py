import wx
from transimage.transimage import Transimage

if __name__ =='__main__':

    app = wx.App()
    transimage = Transimage(None)
    transimage.Show()
    app.MainLoop()
    