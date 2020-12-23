import os
import easyocr.config as easyocr_lang
import image_translator.utils.lang as image_translator_lang
from easyocr.config import mo
from zipfile import ZipFile
from urllib.request import urlretrieve
from transimage.lang import LANG,LANG_DICT

TESSDATA='https://github.com/tesseract-ocr/tessdata/raw/master'
TESSDATA_BEST='https://github.com/tesseract-ocr/tessdata_best/raw/master'

def download_lang(lang,progress_dialog):
    tesseract_url=f'{TESSDATA_BEST}/{lang}.traineddata'

    lang_code_tesseract=image_translator_lang.OCR_LANG[lang][0]
    if not os.path.exists(f'tesseract-ocr/tessdata/{lang_code_tesseract}.traineddata'):
        download(tesseract_url,'tesseract-ocr/tessdata',progress_dialog)

    lang_code_easyocr=image_translator_lang.OCR_LANG[lang][1]
    file=''
    if lang_code_easyocr in easyocr_lang.latin_lang_list:
        file='latin.pth'
    elif lang_code_easyocr in easyocr_lang.arabic_lang_list:
        file='arabic.pth'
    elif lang_code_easyocr in easyocr_lang.bengali_lang_list:
        file='bengali.pth'
    elif lang_code_easyocr in easyocr_lang.cyrillic_lang_list:
        file='cyrillic.pth'
    elif lang_code_easyocr in easyocr_lang.devanagari_lang_list:
        file='devanagari.pth'
    elif lang_code_easyocr == 'th':
        file='thai.pth'
    elif lang_code_easyocr == 'ch_sim':
        file='chinese_sim.pth'
    elif lang_code_easyocr == 'ch_tra':
        file='chinese.pth'
    elif lang_code_easyocr == 'ja':
        file='japanese.pth'
    elif lang_code_easyocr == 'ko':
        file='korean.pth'
    elif lang_code_easyocr == 'ta':
        file='tamil.path'
    elif lang_code_easyocr == 'te':
        file='telegu.pth'
    elif lang_code_easyocr == 'kn':
        file='kannada.pth'
    if file is not '' and not os.path.exists(f'easyocr/model/{file}'):
        url= easyocr_lang.model_url[file][0]
        download(url,'easyocr/model',progress_dialog,file)

def download(url, path,progress_dialog,filename=None):

    if filename is not None:
        file = os.path.join(path, 'temp.zip')
        urlretrieve(url, file,reporthook=progress_bar(progress_dialog))
        with ZipFile(file, 'r') as zipObj:
            zipObj.extract(filename, path)
        os.remove(file)
    else:
        file = os.path.join(path,url.split('/')[-1])
        urlretrieve(url, file,reporthook=progress_bar(progress_dialog))


def progress_bar(progress_dialog):
    def progress_hook(count, block_size, total_size):
        progress_size = int(count * block_size)
        
        percent = min(int(count*block_size*100/total_size),100)
        progress_dialog.Update(percent)

    return progress_hook

