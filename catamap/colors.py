#!/usr/bin/python3
"""

catamap.colors
Color definitions and functions

License: GPLv3
Repo: <https://git.ycnrg.org/projects/GTOOL/repos/catamap>

Copyright (c) 2019 J. Hipps <jacob@ycnrg.org>
https://ycnrg.org/

"""

import re
import logging

import xtermcolor

from catamap import __version__, __date__

logger = logging.getLogger('catamap')

COLORS = {
    'black': 16,
    'white': 15,
    'red': 1,
    'green': 2,
    'blue': 4,
    'cyan': 6,
    'magenta': 5,
    'yellow': 11,
    'light_gray': 7,
    'dark_gray': 8,
    'brown': 3,
    'light_red': 9,
    'light_green': 10,
    'light_blue': 12,
    'light_cyan': 14,
    'pink': 13,
}


def translate_color(cstr):
    """
    Translate Cataclysm color into ANSI (fg,bg) pair
    """
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
        fg = COLORS['black']
        try:
            bg = COLORS[s_fg]
        except:
            logger.error("color '%s' is not defined", s_fg)
    elif ctype == 'h':
        # highlight apparently just means a blue background?
        bg = COLORS['blue']
        try:
            fg = COLORS[s_fg]
        except:
            logger.error("color '%s' is not defined", s_fg)
    else:
        if s_bg is None:
            bg = COLORS['black']
        else:
            try:
                bg = COLORS[s_bg]
            except:
                logger.error("color '%s' is not defined", s_fg)
        try:
            fg = COLORS[s_fg]
        except:
            logger.error("color '%s' is not defined", s_fg)

    return (fg, bg)

def colorize(instr, catacolor):
    """
    Colorize @instr using Cataclysm color string @catacolor
    """
    try:
        fg, bg = translate_color(catacolor)
    except:
        return instr
    return xtermcolor.colorize(instr, ansi=fg, ansi_bg=bg)
