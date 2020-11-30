import wx
import wx.lib.newevent
import urllib
import numpy as np
import cv2
import threading
import time
import pathos.multiprocessing as p_multiprocessing
from transimage.canvas import DisplayCanvas
from transimage.translator.image_translator import ImageTranslator

EvtImageProcess, EVT_IMAGE_PROCESS = wx.lib.newevent.NewEvent()

class ImageProcess(threading.Thread):
    def __init__(self,notify_window,img, ocr, translator, src_lang, dest_lang,mode_process=True):
        super(ImageProcess, self).__init__()
        self.notify_window = notify_window
        self.mode_process=mode_process
        self.img=img
        self.ocr=ocr
        self.translator=translator
        self.src_lang=src_lang
        self.dest_lang=dest_lang
        self.image_translator=ImageTranslator(self.img,self.ocr,self.translator,self.src_lang, self.dest_lang)
    def run(self):
        self.stop=False
        self.process=p_multiprocessing.ProcessingPool()
        if self.mode_process ==True:
            results = self.process.amap(ImageProcess.worker_process,[self.image_translator])
        else:
            results = self.process.amap(ImageProcess.worker_translate,[self.image_translator])
        while not results.ready() and self.stop==True:
                time.sleep(2)
        if self.stop==False:
            self.image_translator=results.get()
            self.process.close()
            evt = EvtImageProcess(data=self.image_translator)
            wx.PostEvent(self.notify_window, evt)

    def abort(self):
        if self.process !=None:
            self.stop=True
            self.process.terminate()
            self.image_translator=None

    @staticmethod
    def worker_process(image_translator):
        image_translator.processing()
        return image_translator

    @staticmethod
    def worker_translate(image_translator):
        image_translator.translate()
        return image_translator

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

        self.logo=self.toolBar.AddTool(wx.ID_ANY,"Logo",wx.Bitmap("icons/logo.png"),wx.NullBitmap,wx.ITEM_NORMAL ,wx.EmptyString,wx.EmptyString,None)
        self.Bind(wx.EVT_TOOL,self.context_menu,self.logo)

        self.open=self.toolBar.AddTool(wx.ID_ANY,"Open File",wx.Bitmap("icons/open_file.png"),wx.NullBitmap,wx.ITEM_NORMAL ,wx.EmptyString,wx.EmptyString,None)
        self.Bind(wx.EVT_TOOL,self.open_menu,self.open)

        self.save=self.toolBar.AddTool(wx.ID_ANY,"SAve",wx.Bitmap("icons/save.png"),wx.NullBitmap,wx.ITEM_NORMAL ,wx.EmptyString,wx.EmptyString,None)
        self.Bind(wx.EVT_TOOL,self.save_menu,self.save)

        self.about=self.toolBar.AddTool(wx.ID_ANY,"About",wx.Bitmap("icons/info.png"),wx.NullBitmap,wx.ITEM_NORMAL ,wx.EmptyString,wx.EmptyString,None)
        self.Bind(wx.EVT_TOOL,self.about_menu,self.about)

        self.help=self.toolBar.AddTool(wx.ID_ANY,"Help",wx.Bitmap("icons/help.png"),wx.NullBitmap,wx.ITEM_NORMAL ,wx.EmptyString,wx.EmptyString,None)
        self.Bind(wx.EVT_TOOL,self.help_menu,self.help)


        self.toolBar.Realize()

        toolBarSizer.Add(self.toolBar,0,wx.EXPAND,5)

        mainSizer.Add(toolBarSizer,0,wx.EXPAND,5)

        imageSizer= wx.BoxSizer(wx.HORIZONTAL)

        self.imageCanvas=DisplayCanvas(self,id=wx.ID_ANY,size=wx.DefaultSize,ProjectionFun=None,BackgroundColor='#00ff00')
        self.imageCanvas.SetForegroundColour("#00ff00")
        self.imageCanvas.SetBackgroundColour("#00ff00")

        imageSizer.Add(self.imageCanvas,3,wx.EXPAND)
        mainSizer.Add(imageSizer,3,wx.EXPAND,1)

        editSizer=wx.BoxSizer(wx.VERTICAL)
        self.textCrtl=wx.TextCtrl(self,wx.ID_ANY,wx.EmptyString,wx.DefaultPosition,wx.DefaultSize,0)
        editSizer.Add(self.textCrtl,0,wx.ALIGN_CENTER|wx.ALL,5)

        mainSizer.Add(editSizer,1,0,5)

        self.Bind(EVT_IMAGE_PROCESS, self.callback_image_process)

        self.SetSizer(mainSizer)
        self.Layout()

        self.Centre(wx.BOTH)

    def help_menu(self,event):
        event.Skip()
        print('help_menu')

    def about_menu(self,event):
        event.Skip()
        print('about_menu')

    def context_menu(self,event):
        event.Skip()
        print('context_menu')

    def save_menu(self,event):
        event.Skip()
        print('save_menu')

    def open_menu(self,event):
        print('open_menu')
        # self.processImage=ImageProcess(self,'https://i.stack.imgur.com/vrkIj.png', 'tesseract', 'google', 'eng', 'fra')
        # self.processImage.start()

    def translate(self,event):
        self.translator.text.clear()
        for text in self.imageCanvas.text:
            text_object=text['text_object']
            text_object.CalcBoundingBox()
            pos=text_object.XY
            x=pos[0]
            y=pos[1]
            w=text_object.BoxWidth
            h=text_object.BoxHeight


            string=text['original_text']
            if text_object.String != string:
                string=self.translator.run_translator(text_object.String)
            else:
                string=text['original_translated']
            self.translator.text.append(
                {
                'x': x,
                'y': y,
                'w': w,
                'h': h,
                'paragraph_w': None,
                'paragraph_h': None,
                'string':text_object.String,
                'translated_string': string,
                'image': None,
                'max_width': w,
                'font_size': text_object.Size
                })
        self.processImage.image_translator=self.translator
        self.processImage.mode_process=False
        self.processImage.start()

    def callback_image_process(self,event):
        self.translator=event.data[0]
        if self.processImage.mode_process==True:
            self.imageCanvas.update_image(self.translator.img_out)
            for text in self.translator.text:
                self.imageCanvas.add_text(text['string'],text['translated_string'],(text['x'],text['y']),text['max_width'],text['font_zize'])
        else:
            pass
            
