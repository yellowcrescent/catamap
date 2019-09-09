#!/usr/bin/python3
"""

catamap.colors
Color definitions and functions
Translates Cataclysm ncurses colors to ANSI or RGB colors

License: GPLv3
Repo: <https://git.ycnrg.org/projects/GTOOL/repos/catamap>

Copyright (c) 2019 J. Hipps <jacob@ycnrg.org>
https://ycnrg.org/

"""

import re
import logging
from typing import NewType

import xtermcolor

from catamap import __version__, __date__

logger = logging.getLogger('catamap')
ColorPair = NewType('ColorPair', tuple)

COLORS = {
    'black': (16, (0, 0, 0)),
    'white': (15, (255, 255, 255)),
    'red': (1, (128, 0, 0)),
    'green': (2, (0, 128, 0)),
    'blue': (4, (0, 0, 128)),
    'cyan': (6, (0, 128, 128)),
    'magenta': (5, (128, 0, 128)),
    'yellow': (11, (255, 255, 0)),
    'light_gray': (7, (192, 192, 192)),
    'dark_gray': (8, (128, 128, 128)),
    'brown': (3, (128, 128, 0)),
    'light_red': (9, (255, 0, 0)),
    'light_green': (10, (0, 255, 0)),
    'light_blue': (12, (0, 0, 255)),
    'light_cyan': (14, (0, 255, 255)),
    'pink': (13, (255, 0, 255)),
}


def translate_color(cstr: str, cspace='ansi') -> ColorPair:
    """
    Translate Cataclysm color into (fg,bg) pair

    When @cspace is 'ansi', returns an ANSI/xterm256-compatible color code
    When @cspace is 'rgb', returns an RGB tuple (r,g,b)

    """
    cs = 0 if cspace == 'ansi' else 1

    try:
        ctype, s_fg, s_bg = re.match(r'^(?:([chi])_)?((?:light_|dark_)?[a-z]+)(?:_([a-z]+))?$', cstr, re.I).groups()
    except Exception as e:
        logger.error("failed to translate color '%s': %s", cstr, str(e))
        return None

    if s_fg == 'unset':
        logger.debug("c_unset, returning None")
        return None
    elif ctype == 'i':
        # set fg to black, bg to foreground color
        fg = COLORS['black'][cs]
        try:
            bg = COLORS[s_fg][cs]
        except:
            logger.error("color '%s' is not defined", s_fg)
    elif ctype == 'h':
        # highlight apparently just means a blue background?
        bg = COLORS['blue'][cs]
        try:
            fg = COLORS[s_fg][cs]
        except:
            logger.error("color '%s' is not defined", s_fg)
    else:
        if s_bg is None:
            bg = COLORS['black'][cs]
        else:
            try:
                bg = COLORS[s_bg][cs]
            except:
                logger.error("color '%s' is not defined", s_fg)
        try:
            fg = COLORS[s_fg][cs]
        except:
            logger.error("color '%s' is not defined", s_fg)

    return (fg, bg)

def colorize_ansi(instr: str, catacolor: str) -> str:
    """
    Colorize @instr using Cataclysm color string @catacolor

    Returns @instr wrapped in ANSI color escape codes, including
    a the color reset code. If no color could be matched, or
    c_unset is used, instr will be returned unchanged.
    """
    try:
        fg, bg = translate_color(catacolor, cspace='ansi')
    except:
        return instr
    return xtermcolor.colorize(instr, ansi=fg, ansi_bg=bg)
