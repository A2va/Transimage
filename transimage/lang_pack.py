import os
from zipfile import ZipFile
from urllib.request import urlretrieve

TESSDATA='https://github.com/tesseract-ocr/tessdata'
TESSDATA_BEST='https://github.com/tesseract-ocr/tessdata_best'

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

