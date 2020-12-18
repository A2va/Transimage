# Copyright (C) 2020  A2va

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

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