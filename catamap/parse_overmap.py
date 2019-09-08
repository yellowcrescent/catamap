#!/usr/bin/python3
"""

catamap.parse_overmap
Parse overmap tiles

License: GPLv3
Repo: <https://git.ycnrg.org/projects/GTOOL/repos/catamap>

Copyright (c) 2019 J. Hipps <jacob@ycnrg.org>
https://ycnrg.org/


Save filename formats (all files JSON with optional comment on line 1):

[savedir]/o.OMT_X.OMT_Y - Overmap tiles
[savedir]/maps/SEG_X.SEG_Y.SEG_Z - Overmap segment directory (SEG_SZ * SEG_SZ)
[savedir]/maps/SEG_X.SEG_Y.SEG_Z/OM_X.OM_Y.OM_Z.map - Submap

"""

import os
import re
import json
import logging

from catamap.gamedata import GameData
from catamap.colors import colorize
from catamap import __version__, __date__

logger = logging.getLogger('catamap')

OMT_SZ = 180        # Overmap tile size (X & Y)
SEG_SZ = 32         # Segment size
MAP_SZ = 12         # Map size

ULINES = {
    'end_south':    ('\u2502', 'VLINE',     0b1010, 1,  2),     # Vertical line
    'end_north':    ('\u2502', 'VLINE',     0b1010, 4,  2),     # Vertical line
    'ns':           ('\u2502', 'VLINE',     0b1010, 5,  0),     # Vertical line
    'end_west':     ('\u2500', 'HLINE',     0b0101, 2,  2),     # Horizontal line
    'end_east':     ('\u2500', 'HLINE',     0b0101, 8,  2),     # Horizontal line
    'ew':           ('\u2500', 'HLINE',     0b0101, 10, 0),     # Horizontal line
    'ne':           ('\u2514', 'LLCORNER',  0b1100, 3,  1),     # Lower left corner
    'es':           ('\u250C', 'ULCORNER',  0b0110, 6,  1),     # Upper left corner
    'sw':           ('\u2510', 'URCORNER',  0b0011, 12, 1),     # Upper right corner
    'wn':           ('\u2518', 'LRCORNER',  0b1001, 9,  1),     # Lower right corner
    'nes':          ('\u251C', 'LTEE',      0b1110, 7,  3),     # Tee pointing right
    'new':          ('\u2534', 'BTEE',      0b1101, 11, 3),     # Tee pointing up
    'nsw':          ('\u2524', 'RTEE',      0b1011, 13, 3),     # Tee pointing left
    'esw':          ('\u252C', 'TTEE',      0b0111, 14, 3),     # Tee pointing down
    'isolated':     ('\u253C', 'PLUS',      0b1111, 0,  4),     # Large Plus or cross over
    'nesw':         ('\u253C', 'PLUS',      0b1111, 15, 4),     # Large Plus or cross over
}

UHOMES = {
    'north':    "^",
    'south':    "v",
    'east':     ">",
    'west':     "<",
}

URDIST = {
    'north':    0,
    'west':     1,
    'south':    2,
    'east':     3,
}

class World(object):
    """
    Loads a world from the provided directory path,
    then loads all overmaps, etc.
    [World] -> Overmaps -> Maps -> Submaps
    """
    path = None
    tiles = {}
    gdata = None

    def __init__(self, path, gamedata: GameData):
        self.gdata = gamedata
        self.path = os.path.realpath(os.path.expanduser(path))
        logger.debug("loading save data from directory: %s", self.path)
        self.load_world()

    def load_world(self):
        """
        Read files from save directory, then load all necessary dependencies
        """
        r_omap = re.compile(r'^o\.(?P<om_x>[\-0-9]+)\.(?P<om_y>[\-0-9]+)$')
        try:
            for tfile in os.scandir(self.path):
                if r_omap.match(tfile):
                    omapgd = r_omap.match(tfile).groupdict()
                    omt_x = int(omapgd['x'])
                    omt_y = int(omapgd['y'])
                    if self.tiles.get(omt_x) is None:
                        self.tiles[omt_x] = {}
                    logger.debug("found overmap tile at <%d, %d> from file %s", omt_x, omt_y, tfile)
                    self.tiles[omt_x][omt_y] = OvermapTile(omt_x, omt_y, omapgd)
                    self.tiles[omt_x][omt_y].resolve_symbols(self.gdata)
        except Exception as e:
            logger.error("failed to load overmap tiles: %s", str(e))
            return False
        return True

    def get_tile(self, x, y):
        """
        Returns overmap tile at x,y
        """
        try:
            return self.tiles[x][y]
        except:
            logger.debug("no overmap tile at <%d, %d>", x, y)
            return None

class OvermapTile(object):
    """
    Loads a single overmap tile, and all associated submap tiles for each map tile
    World -> [Overmaps] -> Maps -> Submaps
    """
    x = None
    y = None
    filename = None
    tiles = {}

    def __init__(self, x, y, filename):
        logger.debug("init overmapTile at <%d, %d> (%s)", x, y, os.path.realpath(filename))
        self.x = x
        self.y = y
        self.filename = filename
        self.parse()

    def parse(self):
        """
        Parse a single overmap sector from JSON file
        """
        try:
            with open(self.filename) as f:
                # discard first line
                vline = f.readline()
                if not vline.startswith('#'):
                    f.seek(0)
                omjson = json.load(f)
        except Exception as e:
            logger.error("failed to parse JSON file '%s': %s", self.filename, str(e))
            return None

        # Init Z-levels
        for tz in range(-10, 11):
            self.tiles[tz] = {}

        # Read layers
        # Starts with Z-level -10 up through +10 (21 total)
        tz = -10
        for tlayer in omjson['layers']:
            idex = 0
            for ttype, tlen in tlayer:
                for tdex in range(tlen):
                    coord = (*self.itoxy(idex), tz)
                    # FIXME - change None to actual filename
                    self.tiles[tz][idex] = SubmapTile(*coord, ttype, None)
                    idex += 1
            tz += 1

    def itoxy(self, idex):
        """
        Convert tile index to (x,y)
        """
        return (int(idex % OMT_SZ), int(idex / OMT_SZ))

    def xytoi(self, x, y):
        """
        Convert (x,y) to tile index
        """
        return int(y * OMT_SZ) + int(x)

    def get_tile(self, x, y, z=0):
        """
        Fetch tile at (x,y,z)
        """
        try:
            return self.tiles[z][self.xytoi(x, y)]
        except:
            logger.debug("no map tile at <%d, %d, %d>", x, y, z)
            return None

    def resolve_symbols(self, gdata: GameData):
        """
        Resolves data from @gdata to each overmap section
        @returns True on success, False on failure
        """
        try:
            logger.debug("len(gdata.overmap_terrain) = %d", len(gdata.overmap_terrain))
        except KeyError:
            logger.error("overmap_terrain not loaded")
            return False

        r_ulines = re.compile(r'_(%s)$' % ('|'.join(ULINES)))
        r_compass = re.compile(r'_(north|south|east|west)$')
        uline_syms = {x[0]: x[2] for x in ULINES.values()}

        for zlevel in self.tiles:
            for tindex in self.tiles[zlevel]:
                # check for LINEAR matches
                if r_ulines.search(self.tiles[zlevel][tindex].omtype):
                    omtype = r_ulines.sub('', self.tiles[zlevel][tindex].omtype)
                    overmap_terrain = gdata.overmap_terrain.get(omtype)
                    if overmap_terrain is not None:
                        if 'LINEAR' in overmap_terrain.get('flags', []):
                            self.tiles[zlevel][tindex].overmap_terrain = overmap_terrain

                            # generate symbol for matching line direction
                            ulmatch = False
                            for tu in ULINES:
                                if self.tiles[zlevel][tindex].omtype.endswith('_' + tu):
                                    self.tiles[zlevel][tindex].osym = ULINES[tu][0]
                                    ulmatch = True
                                    break
                            if not ulmatch:
                                logger.warning("no ULINES direction match for %s", self.tiles[zlevel][tindex].omtype)
                            continue
                    else:
                        logger.debug("no matching overmap_terrain for %s", omtype)

                # for remaining non-transport stuff...
                omtype = r_compass.sub('', self.tiles[zlevel][tindex].omtype)
                overmap_terrain = gdata.overmap_terrain.get(omtype)
                self.tiles[zlevel][tindex].overmap_terrain = overmap_terrain
                if overmap_terrain is None:
                    logger.warning("failed to get overmap_terrain for %s", omtype)
                    continue

                # ensure homes and other buildings using '^' point in the correct direction
                if overmap_terrain.get('sym') == '^':
                    ulmatch = False
                    for tu in UHOMES:
                        if self.tiles[zlevel][tindex].omtype.endswith('_' + tu):
                            self.tiles[zlevel][tindex].osym = UHOMES[tu][0]
                            ulmatch = True
                            break
                    if not ulmatch:
                        logger.warning("no UHOMES direction match for %s", self.tiles[zlevel][tindex].omtype)

                # ensure line symbols for structures are rotated in the correct direction
                elif overmap_terrain.get('sym') in uline_syms:
                    # determine rotation distance from north
                    rot_dist = 0
                    for tu in URDIST:
                        if self.tiles[zlevel][tindex].omtype.endswith('_' + tu):
                            rot_dist = URDIST[tu]
                            break

                    # determine new symbol
                    # get current bit pattern for rotation
                    cr_bits = uline_syms[overmap_terrain['sym']]

                    # rotate symbol by amount specified in URDIST (0, 1, 2, 3)
                    # mask out 'overflow' and shift back to the beginning
                    cr_rot = (cr_bits << rot_dist & 0b01111) | (((cr_bits << rot_dist) & 0b011110000) >> 4)
                    self.tiles[zlevel][tindex].osym = [x for x in ULINES.values() if x[2] == cr_rot][0][0]

        return True

    def get_overmap(self, z=0):
        """
        Generates a symbolic representation of overmap, similar to in-game
        Returns a 2D [y][x] array of (symbol, color, name, id)
        """
        omap = []

        for y in range(OMT_SZ):
            tline = []
            for x in range(OMT_SZ):
                ttile = self.get_tile(x, y, z)
                if ttile is None:
                    tline.append(('#', 'gray', 'Unexplored', None))
                else:
                    omter = ttile.overmap_terrain
                    if omter is None:
                        tline.append(('!', 'gray', 'Unknown', None))
                        logger.warning("missing overmap_terrain data at <%d,%d> (omtype=%s)", x, y, ttile.omtype)
                    else:
                        try:
                            sym = ttile.osym if ttile.osym is not None else omter.get('sym', '?')
                            tline.append((sym, omter.get('color'), omter.get('name'), omter.get('id')))
                            if sym is None:
                                logger.warning("missing symbol for <%d,%d> (omtype=%s)", x, y, ttile.omtype)
                                tline.append(('?', 'gray', 'Unknown', None))
                        except Exception as e:
                            logger.warning("failed to get overmap info for <%d,%d> (omtype=%s): %s", x, y, ttile.omtype, str(e))
                            tline.append(('?', 'gray', 'Unknown', None))
            omap.append(tline)
        return omap

    def render_overmap_ansi(self, z=0):
        """
        Returns an ANSI representation of overmap
        """
        omap = self.get_overmap(z)
        outstr = ""
        for y in range(OMT_SZ):
            for x in range(OMT_SZ):
                # TODO: add ANSI color
                outstr += colorize(omap[y][x][0], omap[y][x][1])
            outstr += '\n'
        return outstr

class SubmapTile(object):
    """
    Loads a single map tile, and all associated submap tiles
    World -> Overmaps -> [Maps] -> Submaps
    """
    x = None
    y = None
    z = None
    omtype = None
    overmap_terrain = None
    osym = None

    def __init__(self, x, y, z, omtype, filename):
        #logger.debug("init overmapTile [%s] <%d, %d, %d> (%s)", omtype, x, y, z, filename)
        self.x = x
        self.y = y
        self.z = z
        self.omtype = omtype

def omttoseg(x, y, z):
    """
    Translate overmap coordinates to segment number
    """
    def omtdiv(v, m):
        if v >= 0:
            return int(v / m)
        return int((v - m + 1) / m)
    return (omtdiv(x, SEG_SZ), omtdiv(y, SEG_SZ), z)
