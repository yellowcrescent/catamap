#!/usr/bin/python3
"""

catamap.cli
CLI Entry-point

License: GPLv3
Repo: <https://git.ycnrg.org/projects/GTOOL/repos/catamap>

Copyright (c) 2019 J. Hipps <jacob@ycnrg.org>
https://ycnrg.org/

"""

import os
import logging
import logging.handlers
from argparse import ArgumentParser

from catamap.gamedata import GameData
from catamap.parse_overmap import World, OvermapTile
from catamap import __version__, __date__

logger = logging.getLogger('catamap')

def setup_logging(clevel=logging.INFO, flevel=logging.DEBUG, logfile=None):
    """configure logging using standard logging module"""
    logger.setLevel(logging.DEBUG)

    con = logging.StreamHandler()
    con.setLevel(clevel)
    if clevel == logging.DEBUG:
        con_format = logging.Formatter("%(levelname)s: [%(module)s.%(funcName)s() @ %(lineno)d] %(message)s")
    else:
        con_format = logging.Formatter("%(levelname)s: %(message)s")
    con.setFormatter(con_format)
    logger.addHandler(con)

    if logfile:
        try:
            flog = logging.handlers.WatchedFileHandler(logfile)
            flog.setLevel(flevel)
            flog_format = logging.Formatter("[%(asctime)s] %(name)s: %(levelname)s: [%(module)s.%(funcName)s() @ %(lineno)d] %(message)s")
            flog.setFormatter(flog_format)
            logger.addHandler(flog)
        except Exception as e:
            logger.warning("Failed to open logfile %s: %s", logfile, str(e))

def parse_cli():
    """parse CLI options with argparse"""
    aparser = ArgumentParser(description="Cataclysm DDA map rendering tool")
    aparser.set_defaults(release=None, update=False, logfile=None, loglevel=logging.INFO)

    aparser.add_argument("worldname", action="store", nargs="?", metavar="PATH", help="Name of save game world")
    aparser.add_argument("--gamepath", "-p", action="store", metavar="PATH", help="Path to base game directory")
    aparser.add_argument("--debug", "-d", action="store_const", dest="loglevel", const=logging.DEBUG, help="Show debug messages")
    aparser.add_argument("--logfile", "-l", action="store", metavar="LOGPATH", help="Path to output logfile [default: %(default)s]")
    aparser.add_argument("--version", "-V", action="version", version="%s (%s)" % (__version__, __date__))
    return aparser.parse_args()

def _main():
    """
    Main CLI entry-point
    """
    args = parse_cli()
    setup_logging(args.loglevel, flevel=args.loglevel, logfile=args.logfile)

    # XXX-TESTING ##
    savepath = os.path.join(args.gamepath, 'save', args.worldname)
    gdata = GameData(args.gamepath)
    otile = OvermapTile(0, 0, '/opt/CataclysmDDA/tiles/userdata.debug/save/OMTest/o.0.0')
    otile.resolve_symbols(gdata)
    print(otile.render_overmap_ansi())
    #World(savepath, gdata)
    ###

if __name__ == '__main__':
    _main()
