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
from transimage.lang import LANG
from transimage.config import BACKGROUND_COLOR,TEXT_COLOR, CANVAS_COLOR


EvtImageProcess, EVT_IMAGE_PROCESS = wx.lib.newevent.NewEvent()

LABEL_SIZE=12

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
        self.process=p_multiprocessing.ProcessingPool()
    def run(self):
        self.stop=False
        if self.mode_process ==True:
            # results = self.process.amap(ImageProcess.worker_process,[self.image_translator])
            self.image_translator.processing()
        else:
            # results = self.process.amap(ImageProcess.worker_translate,[self.image_translator])
            self.image_translator.translate()
        # while not results.ready() and self.stop==True:
        #         time.sleep(2)
        if self.stop==False:
            # self.image_translator=results.get()
            # self.process.close()
            evt = EvtImageProcess(data=self.image_translator)
            wx.PostEvent(self.notify_window, evt)

    def abort(self):
        if self.process !=None:
            self.stop=True
            self.process.terminate()
            self.process.join()
            self.process.restart()
            self.image_translator=None

    @staticmethod
    def worker_process(image_translator):
        image_translator.processing()
        return image_translator

    @staticmethod
    def worker_translate(image_translator):
        image_translator.translate()
        return image_translator

class ProgressingDialog(wx.Dialog):

    def __init__(self,parent):
        wx.Dialog.__init__ (self,parent,id=wx.ID_ANY, title="Progressing", pos=wx.DefaultPosition,size=wx.Size(200,120),style=wx.DEFAULT_DIALOG_STYLE)

        self.SetForegroundColour(BACKGROUND_COLOR)
        self.SetBackgroundColour(BACKGROUND_COLOR)
        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        mainSizer = wx.BoxSizer(wx.VERTICAL)

        textSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.fixedText = wx.StaticText(self,wx.ID_ANY,"Time:",wx.DefaultPosition,wx.DefaultSize, wx.ALIGN_CENTER_HORIZONTAL)
        self.fixedText.SetForegroundColour(TEXT_COLOR)
        self.fixedText.Wrap(-1)

        textSizer.Add(self.fixedText,1,wx.ALIGN_CENTER,5)

        self.timeText = wx.StaticText(self, wx.ID_ANY, "0", wx.DefaultPosition, wx.DefaultSize, wx.ALIGN_CENTER_HORIZONTAL)
        self.timeText.SetForegroundColour(TEXT_COLOR)

        textSizer.Add(self.timeText,1,wx.ALIGN_CENTER|wx.ALL,5)

        mainSizer.Add(textSizer,1,wx.ALIGN_CENTER,5)

        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.cancelButton = wx.Button(self,wx.ID_CANCEL,"Cancel",wx.DefaultPosition,wx.DefaultSize,0)
        self.cancelButton.Disable()
        self.cancelButton.SetForegroundColour(TEXT_COLOR)
        self.cancelButton.SetBackgroundColour(BACKGROUND_COLOR)

        buttonSizer.Add(self.cancelButton,1,wx.ALIGN_CENTER|wx.ALL,5)

        mainSizer.Add( buttonSizer, 1, wx.ALIGN_CENTER, 5 )

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.update_label, self.timer)
        self.timer.Start(1000)

        self.SetSizer(mainSizer)
        self.Layout()

        self.Centre(wx.BOTH)

    def update_label(self,event):
        self.timeText.SetLabel(str(int(self.timeText.Label)+1))

class Transimage(wx.Frame):
    def __init__(self,parent):
        wx.Frame.__init__(self,parent,id=wx.ID_ANY,title="Transimage",pos=wx.DefaultPosition,size=wx.Size(1200,500),style=wx.DEFAULT_FRAME_STYLE)
        self.locale = wx.Locale(wx.LANGUAGE_ENGLISH)

        self.SetSizeHints(wx.DefaultSize,wx.DefaultSize)
        self.SetForegroundColour(BACKGROUND_COLOR)
        self.SetBackgroundColour(BACKGROUND_COLOR)

        mainSizer= wx.BoxSizer(wx.HORIZONTAL)
        self.toolBar= wx.ToolBar(self,wx.ID_ANY,wx.DefaultPosition,wx.DefaultSize,wx.TB_VERTICAL)
        self.SetToolBar(self.toolBar)
        self.toolBar.SetForegroundColour(BACKGROUND_COLOR)
        self.toolBar.SetBackgroundColour(BACKGROUND_COLOR)

        self.logo=self.toolBar.AddTool(wx.ID_ANY,"Logo",wx.Bitmap("icons/logo.png"),wx.NullBitmap,wx.ITEM_NORMAL ,wx.EmptyString,wx.EmptyString,None)
        self.Bind(wx.EVT_TOOL,self.context_menu,self.logo)

        self.open=self.toolBar.AddTool(wx.ID_ANY,"Open File",wx.Bitmap("icons/open_file.png"),wx.NullBitmap,wx.ITEM_NORMAL ,wx.EmptyString,wx.EmptyString,None)
        self.Bind(wx.EVT_TOOL,self.open_menu,self.open)

        self.save=self.toolBar.AddTool(wx.ID_ANY,"Save",wx.Bitmap("icons/save.png"),wx.NullBitmap,wx.ITEM_NORMAL ,wx.EmptyString,wx.EmptyString,None)
        self.Bind(wx.EVT_TOOL,self.save_menu,self.save)

        self.about=self.toolBar.AddTool(wx.ID_ANY,"About",wx.Bitmap("icons/info.png"),wx.NullBitmap,wx.ITEM_NORMAL ,wx.EmptyString,wx.EmptyString,None)
        self.Bind(wx.EVT_TOOL,self.about_menu,self.about)

        self.help=self.toolBar.AddTool(wx.ID_ANY,"Help",wx.Bitmap("icons/help.png"),wx.NullBitmap,wx.ITEM_NORMAL ,wx.EmptyString,wx.EmptyString,None)
        self.Bind(wx.EVT_TOOL,self.help_menu,self.help)

        self.toolBar.Realize()

        imageSizer= wx.BoxSizer(wx.HORIZONTAL)

        self.imageCanvas=DisplayCanvas(self,id=wx.ID_ANY,size=wx.DefaultSize,ProjectionFun=None,BackgroundColor=CANVAS_COLOR)
        self.imageCanvas.SetForegroundColour(CANVAS_COLOR)
        self.imageCanvas.SetBackgroundColour(CANVAS_COLOR)

        imageSizer.Add(self.imageCanvas,3,wx.EXPAND)
        mainSizer.Add(imageSizer,3,wx.EXPAND,1)

        editSizer=wx.BoxSizer(wx.VERTICAL)

        src_langSizer=wx.BoxSizer(wx.HORIZONTAL)

        self.src_langText = wx.StaticText(self, wx.ID_ANY, "Source Language")
        self.src_langText.SetForegroundColour(TEXT_COLOR)
        self.src_langText.SetFont(wx.Font(LABEL_SIZE, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, ""))

        self.src_langCombo = wx.ComboBox(self, wx.ID_ANY, choices=[], style=wx.CB_DROPDOWN | wx.CB_SORT)
        self.src_langCombo.SetBackgroundColour(BACKGROUND_COLOR)
        self.src_langCombo.SetForegroundColour(TEXT_COLOR)  #For text
        self.src_langCombo.SetFont(wx.Font(LABEL_SIZE, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, ""))
        self.src_langCombo.Bind(wx.EVT_COMBOBOX,self.update_src_lang)

        src_langSizer.Add(self.src_langText, 0, wx.ALL | wx.EXPAND, 0)
        src_langSizer.AddSpacer(10)
        src_langSizer.Add(self.src_langCombo, 0, wx.ALL | wx.EXPAND, 0)

        dest_langSizer=wx.BoxSizer(wx.HORIZONTAL)

        self.dest_langText = wx.StaticText(self, wx.ID_ANY, "Destination Language")
        self.dest_langText.SetForegroundColour(TEXT_COLOR)
        self.dest_langText.SetFont(wx.Font(LABEL_SIZE, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, ""))

        self.dest_langCombo = wx.ComboBox(self, wx.ID_ANY, choices=[], style=wx.CB_DROPDOWN | wx.CB_SORT)
        self.dest_langCombo.SetBackgroundColour(BACKGROUND_COLOR)
        self.dest_langCombo.SetForegroundColour(TEXT_COLOR) #For text
        self.dest_langCombo.SetFont(wx.Font(LABEL_SIZE, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, ""))
        self.dest_langCombo.Bind(wx.EVT_COMBOBOX,self.update_dest_lang)

        dest_langSizer.Add(self.dest_langText, 0, wx.ALL, 0)
        dest_langSizer.AddSpacer(10)
        dest_langSizer.Add(self.dest_langCombo, 0, wx.ALL, 0)

        translatorSizer=wx.BoxSizer(wx.HORIZONTAL)

        self.translatorText = wx.StaticText(self, wx.ID_ANY, "Translator")
        self.translatorText.SetForegroundColour(TEXT_COLOR)
        self.translatorText.SetFont(wx.Font(LABEL_SIZE, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, ""))

        self.translatorCombo = wx.ComboBox(self, wx.ID_ANY, choices=["Deepl","Bing"], style=wx.CB_DROPDOWN | wx.CB_SORT)
        self.translatorCombo.SetBackgroundColour(BACKGROUND_COLOR)
        self.translatorCombo.SetForegroundColour(TEXT_COLOR) #For text
        self.translatorCombo.SetFont(wx.Font(LABEL_SIZE, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, ""))
        self.translatorCombo.Bind(wx.EVT_COMBOBOX,self.update_translator)

        translatorSizer.Add(self.translatorText, 0, wx.ALL | wx.EXPAND, 0)
        translatorSizer.AddSpacer(10)
        translatorSizer.Add(self.translatorCombo, 0, wx.ALL | wx.EXPAND, 0)

        ocrSizer=wx.BoxSizer(wx.HORIZONTAL)

        self.ocrText = wx.StaticText(self, wx.ID_ANY, "OCR")
        self.ocrText.SetForegroundColour(TEXT_COLOR)
        self.ocrText.SetFont(wx.Font(LABEL_SIZE, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, ""))

        self.ocrCombo = wx.ComboBox(self, wx.ID_ANY, choices=["Tesseract","EasyOCR"], style=wx.CB_DROPDOWN | wx.CB_SORT)
        self.ocrCombo.SetBackgroundColour(BACKGROUND_COLOR)
        self.ocrCombo.SetForegroundColour(TEXT_COLOR) #For text
        self.ocrCombo.SetFont(wx.Font(LABEL_SIZE, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, ""))
        self.ocrCombo.Bind(wx.EVT_COMBOBOX,self.update_ocr)

        ocrSizer.Add(self.ocrText, 0, wx.ALL | wx.EXPAND, 0)
        ocrSizer.AddSpacer(10)
        ocrSizer.Add(self.ocrCombo, 0, wx.ALL | wx.EXPAND, 0)

        self.processButton = wx.Button(self,wx.ID_ANY,"Run processing",wx.DefaultPosition,wx.DefaultSize,0)
        self.processButton.Bind(wx.EVT_BUTTON,self.process_image)
        self.processButton.SetForegroundColour(TEXT_COLOR)
        self.processButton.SetBackgroundColour(BACKGROUND_COLOR)

        editSizer.Add(src_langSizer,1,wx.ALL,5)
        editSizer.Add(dest_langSizer,1,wx.ALL,5)
        editSizer.Add(translatorSizer, 1, wx.ALL,5)
        editSizer.Add(ocrSizer,1,wx.ALL,5)
        editSizer.Add(self.processButton,1,wx.ALL | wx.ALIGN_CENTER,5)

        mainSizer.Add(editSizer,1,0,5)

        self.Bind(EVT_IMAGE_PROCESS, self.callback_image_process)

        self.SetSizer(mainSizer)
        self.Layout()

        self.Centre(wx.BOTH)

        self.image_path=''

        for lang in LANG:
            self.dest_langCombo.Append(lang.capitalize())
            self.src_langCombo.Append(lang.capitalize())

    def help_menu(self,event):
        event.Skip()
        print('help_menu')

    def about_menu(self,event):
        event.Skip()
        print('about_menu')

    def context_menu(self,event):
        event.Skip()

    def save_menu(self,event):
        event.Skip()
        print('save_menu')
        self.translate()

    def open_menu(self,event):
        event.Skip()
        wildcard = "Open Image Files (*.jpg;*.png)|*.jpg;*.png|PNG files (*.png)|*.png"
        with wx.FileDialog(self, "Open image file", wildcard=wildcard,
        style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            self.image_path = fileDialog.GetPath()

    def update_translator(self,event):
        string=event.String
        string = string[0].lower() + string[1:]
        self.translator_engine=string

    def update_ocr(self,event):
        string=event.String
        string = string[0].lower() + string[1:]
        self.ocr=string

    def update_src_lang(self,event):
        string=event.String
        string = string[0].lower() + string[1:]
        self.src_lang=LANG[string]

    def update_dest_lang(self,event):
        string=event.String
        string = string[0].lower() + string[1:]
        self.dest_lang=LANG[string]

    def callback_image_process(self,event):
        self.progressDialog.Close()
        self.processImage.abort()
        self.imageCanvas.delete_all()
        self.translator=event.data[0]
        if self.processImage.mode_process==True:
            self.imageCanvas.update_image(self.translator.img_out)
            for text in self.translator.text:
                self.imageCanvas.add_text(text['string'],text['translated_string'],(text['x'],text['y']),text['max_width'],text['font_zize'])
        else:#Saving image
            wildcard = "JPG Files (*.jpg)|*.jpg|PNG files (*.png)|*.png"
            with wx.FileDialog(self, "Save Image File", wildcard=wildcard,
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
            
                if fileDialog.ShowModal() == wx.ID_CANCEL:
                    return 
                out_path = fileDialog.GetPath()
                cv2.imwrite(out_path,self.translator.img_out)

    def process_image(self,event):
            if self.src_lang ==self.dest_lang:
                wx.MessageDialog(None, 'The source and destination lang cannot be the same', 'Error', wx.OK | wx.ICON_EXCLAMATION).ShowModal()
            elif self.src_lang == '' or self.dest_lang=='' or self.translator_engine=='' or self.ocr=='':
                wx.MessageDialog(None, 'One on the combox are empty', 'Error', wx.OK | wx.ICON_EXCLAMATION).ShowModal()
            elif self.image_path=='':
                wx.MessageDialog(None, 'Any image are open', 'Error', wx.OK | wx.ICON_EXCLAMATION).ShowModal()
            else:
                img =cv2.imread(self.image_path)
                self.processImage=ImageProcess(self,img, self.ocr, self.translator_engine, self.src_lang, self.dest_lang)
                self.processImage.start()

                self.progressDialog = ProgressingDialog(self)
                if self.progressDialog.ShowModal()==wx.ID_CANCEL:
                    self.processImage.abort()

    def translate(self):
        self.translator.text.clear()
        for text in self.imageCanvas.text:
            text_object=text['text_object']
            text_object.CalcBoundingBox()
            pos=text_object.XY
            x=pos[0]
            y=abs(pos[1])
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
        self.processImage=ImageProcess(self,self.translator.img_out, self.ocr, self.translator_engine, self.src_lang, self.dest_lang)
        self.processImage.image_translator=self.translator
        self.processImage.mode_process=False
        self.processImage.start()

        self.progressDialog = ProgressingDialog(self)
        if self.progressDialog.ShowModal()==wx.ID_CANCEL:
            self.processImage.abort()
