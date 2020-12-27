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

import wx

SETTINGS_FILE = 'settings.json'
LABEL_SIZE=12

def convert_hexa(value):
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

BACKGROUND_COLOR_HEX = '#303030'
HIGHLIGHT_COLOR_HEX = '#558de8'
CANVAS_COLOR_HEX = '#404040'
CANVAS_COLOR_HIGHLIGHT_HEX= '#353535'
TEXT_COLOR_HEX = '#ffffff'

# Reminder: The stars (*) unpack the tuple into tree arguments 
BACKGROUND_COLOR = wx.Colour(*convert_hexa(BACKGROUND_COLOR_HEX))
HIGHLIGHT_COLOR = wx.Colour(*convert_hexa(HIGHLIGHT_COLOR_HEX))
CANVAS_COLOR = wx.Colour(*convert_hexa(CANVAS_COLOR_HEX))
CANVAS_COLOR_HIGHLIGHT = wx.Colour(*convert_hexa(CANVAS_COLOR_HIGHLIGHT_HEX))
TEXT_COLOR = wx.Colour(*convert_hexa(TEXT_COLOR_HEX))

