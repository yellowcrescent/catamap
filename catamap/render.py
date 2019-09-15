#!/usr/bin/python3
"""

catamap.render
Image rendering functions
Uses Pillow and FreeType2

License: GPLv3
Repo: <https://git.ycnrg.org/projects/GTOOL/repos/catamap>

Copyright (c) 2019 J. Hipps <jacob@ycnrg.org>
https://ycnrg.org/

"""

import logging
from typing import NewType

from PIL import Image, ImageDraw, ImageFont

from catamap import __version__, __date__

logger = logging.getLogger('catamap')


class OvermapTileImage(object):
    """
    Renders an overmap tile to a PIL Image object
    """
    im = None               # Image object
    draw = None             # ImageDraw object
    font = None             # ImageFont object
    lfont = None            # Line-drawing ImageFont object
    bg = (0, 0, 0, 255)     # RGBA bg color
    rmode = 'text'          # Render mode (text, tiles, vector)
    single = False          # Single-tile mode (when enabled, removes outer padding)
    fpadding = 4            # Text mode: outer glyph padding
    fpad_bot = 4            # Text mode: inner bottom glyph pad
    fpad_left = 0           # Text mode: inner left glyph pad
    t_w = 0                 # OM Tile width
    t_h = 0                 # OM Tile height
    i_w = 0                 # Image width
    i_h = 0                 # Image height
    f_w = 0                 # Font width
    f_h = 0                 # Font height

    def __init__(self, t_w, t_h, fontpath, fontsize=24, bg=(0, 0, 0, 255), rendermode='text',
                 fpadding=4, single=False):
        self.t_w = t_w
        self.t_h = t_h
        self.rmode = rendermode
        self.bg = bg
        self.fpadding = fpadding
        self.single = single

        try:
            self.font = ImageFont.FreeTypeFont(fontpath, size=fontsize)
            #self.lfont = self.font.font_variant(size=int(fontsize + 2))
            self.lfont = self.font.font_variant(size=(fontsize - 2))
            logger.debug("using font: %s (%s)", *self.font.getname())
        except Exception as e:
            logger.error("failed to open font '%s': %s", fontpath, str(e))

        self._init_image()

    def _init_image(self):
        """
        Initialize image with correct dimensions, depending on options
        """
        # calculate dimensions
        # this assumes a fixed-width font is used!
        self.f_w, self.f_h = self.font.getsize('X')
        logger.debug("calculated font glyph size (unpadded): %d x %d", self.f_w, self.f_h)
        if self.font.getsize('X')[0] != self.font.getsize('!')[0]:
            logger.warning("chosen font is not fixed-width. this will likley break image output!")

        # calculate image size
        self.i_w = ((self.f_w + self.fpadding) * self.t_w) - (0 if self.single else self.fpadding)
        self.i_h = ((self.f_h + self.fpadding) * self.t_h) - (0 if self.single else self.fpadding)
        logger.debug("calculated image size: %d x %d", self.i_w, self.i_h)

        # create image & draw objects
        self.im = Image.new('RGBA', (self.i_w, self.i_h), self.bg)
        self.draw = ImageDraw.Draw(self.im)

    def plot_tile(self, x, y, txt, fg, bg, line=False):
        """
        Draw single char/tile on overmap

        @x and @y are overmap coordinates
        @txt is map symbol
        @fg and @bg are (r,g,b) tuples
        If @line is true, alternate font is used
        """
        tx_x = x * (self.f_w + self.fpadding)
        tx_y = y * (self.f_h + self.fpadding)
        bg_x1 = tx_x
        bg_y1 = tx_y
        bg_x2 = (x + 1) * (self.f_w + self.fpadding)
        bg_y2 = (y + 1) * (self.f_h + self.fpadding)

        # Use alternate font if line=True
        if line:
            tfont = self.font
        else:
            tx_x += self.fpad_left
            tx_y -= self.fpad_bot
            tfont = self.lfont

        if bg is not None:
            self.draw.rectangle(((bg_x1, bg_y1), (bg_x2, bg_y2)), fill=bg)
        self.draw.text((tx_x, tx_y), txt, fill=fg, font=tfont)

    def save_image(self, filename):
        """
        Output image to file @filename
        """
        self.im.save(filename)
        logger.debug("wrote output to %s", filename)
