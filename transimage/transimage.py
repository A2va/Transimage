import wx
from transimage.canvas import DisplayCanvas

class Transimage(wx.Frame):
	def __init__(self,parent):
		wx.Frame.__init__(self,parent,id=wx.ID_ANY,title="Transimage",pos=wx.DefaultPosition,size=wx.Size(1000,500),style=wx.DEFAULT_FRAME_STYLE)

		self.SetSizeHints(wx.DefaultSize,wx.DefaultSize)
		self.SetForegroundColour("#ff0000")
		self.SetBackgroundColour("#ff0000")

		mainSizer= wx.BoxSizer(wx.HORIZONTAL)
		toolBarSizer= wx.BoxSizer(wx.HORIZONTAL)

		self.toolBar= wx.ToolBar(self,wx.ID_ANY,wx.DefaultPosition,wx.DefaultSize,wx.TB_VERTICAL)
		self.toolBar.SetForegroundColour("#0000ff")
		self.toolBar.SetBackgroundColour("#0000ff")

		self.tool1=self.toolBar.AddTool(wx.ID_ANY,"Tool",wx.Bitmap("icons/ocr.png"),wx.NullBitmap,wx.ITEM_CHECK,wx.EmptyString,wx.EmptyString,None)

		self.toolBar.Realize()

		toolBarSizer.Add(self.toolBar,0,wx.EXPAND,5)

		mainSizer.Add(toolBarSizer,0,wx.EXPAND,5)

		imageSizer= wx.BoxSizer(wx.HORIZONTAL)

		#self.imagePanel=wx.Panel(self,wx.ID_ANY,wx.DefaultPosition,wx.DefaultSize,wx.TAB_TRAVERSAL)
		self.imageCanvas=DisplayCanvas(self,id=wx.ID_ANY,size=wx.DefaultSize,ProjectionFun=None,BackgroundColor='#00ff00')
		self.imageCanvas.SetForegroundColour("#00ff00")
		self.imageCanvas.SetBackgroundColour("#00ff00")

		imageSizer.Add(self.imageCanvas,3,wx.EXPAND)
		mainSizer.Add(imageSizer,3,wx.EXPAND,1)

		editSizer=wx.BoxSizer(wx.VERTICAL)
		self.textCrtl=wx.TextCtrl(self,wx.ID_ANY,wx.EmptyString,wx.DefaultPosition,wx.DefaultSize,0)
		editSizer.Add(self.textCrtl,0,wx.ALIGN_CENTER|wx.ALL,5)

		mainSizer.Add(editSizer,1,0,5)

		self.SetSizer(mainSizer)
		self.Layout()

		self.Centre(wx.BOTH)
