import wx
from transimage.transimage import Transimage
import multiprocessing
if __name__ =='__main__':
    multiprocessing.freeze_support()
    app = wx.App()
    transimage = Transimage(None)
    transimage.Show()
    app.MainLoop()
    