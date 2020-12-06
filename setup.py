import sys
from cx_Freeze import setup, Executable
from PIL import Image
filename = 'icons/logo_icon.png'
img = Image.open(filename)
img.save('icons/logo_icon.ico')

build_options = {"packages": ["torch","torchvision"],
                "include_files":["tesseract-ocr","icons","font"]
              }

base = None
if sys.platform == "win32":
    base = "Win32GUI"

executables = [Executable("main.py",targetName="Transimage.exe", base=base)]

setup(  name = "Transimage",
        version = "0.1",
        description = "An image translator",
        options = {"build_exe": build_options},
        executables = executables)