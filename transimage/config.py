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

app=wx.App() #A ugly to resolver an error

BACKGROUND_COLOR_HEX = '#303030'
HIGHLIGHT_COLOR_HEX = '#558de8'
CANVAS_COLOR_HEX = '#404040'
CANVAS_COLOR_HIGHLIGHT_HEX= '#353535'
TEXT_COLOR_HEX = '#ffffff'

BACKGROUND_COLOR = wx.Colour(BACKGROUND_COLOR_HEX)
HIGHLIGHT_COLOR = wx.Colour(HIGHLIGHT_COLOR_HEX)
CANVAS_COLOR = wx.Colour(CANVAS_COLOR_HEX)
CANVAS_COLOR_HIGHLIGHT = wx.Colour(CANVAS_COLOR_HIGHLIGHT_HEX)
TEXT_COLOR = wx.Colour(TEXT_COLOR_HEX)