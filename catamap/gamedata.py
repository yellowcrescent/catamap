#!/usr/bin/python3
"""

catamap.gamedata
Parse game JSON data

License: GPLv3
Repo: <https://git.ycnrg.org/projects/GTOOL/repos/catamap>

Copyright (c) 2019 J. Hipps <jacob@ycnrg.org>
https://ycnrg.org/


[data/json]/overmap - Overmap tile data


"""

import os
import json
import logging

from catamap import __version__, __date__

logger = logging.getLogger('catamap')

C_TYPEMAP = {
    'mapgen': list,
    'monstergroup': list,
    'snippet': list,
}


class GameData(object):
    """
    Master class to load and contain all game JSON data
    """
    _gamedir = None
    _data = {}

    def __init__(self, gamedir):
        if os.path.basename(os.path.realpath(gamedir)) == 'json':
            self._gamedir = os.path.expanduser(gamedir)
        else:
            self._gamedir = os.path.expanduser(os.path.join(gamedir, 'data', 'json'))

        # load relavent all gamedata
        self._recurse_load_dir('mapgen')
        self._recurse_load_dir('overmap')

        self._resolve_deps()

    def _recurse_load_dir(self, subpath) -> int:
        """
        Recursively load JSON from subdirectories
        Following the CDDA model, we load top-down (eg. root/file.json before root/sub/file2.json)
        @return Number of failed files (zero on success)
        """
        basepath = os.path.join(self._gamedir, subpath)
        logger.debug("loading %s [%s]", subpath, basepath)

        jtotal = 0
        jfailed = 0
        for tdir, dlist, flist in os.walk(basepath):
            logger.debug("enter: %s (%d files, %d subdirs)", tdir, len(flist), len(dlist))
            for tfile in flist:
                if tfile.endswith('.json'):
                    tfile_real = os.path.join(tdir, tfile)
                    if not self._load_one_json(tfile_real):
                        jfailed += 1
                    jtotal += 1
        logger.debug("finished loading %d JSON files (%d failed)", jtotal, jfailed)
        return jfailed

    def _load_one_json(self, fpath) -> bool:
        """
        Load a single JSON file
        @return True/False on success/fail
        """
        logger.debug("parsing %s", fpath)

        try:
            with open(fpath) as f:
                jdata = json.load(f)
        except Exception as e:
            logger.error("failed to load %s: %s", fpath, str(e))
            return False

        # for JSON files with a single object, repack into list
        if not isinstance(jdata, list):
            logger.debug("repacking single object into list")
            jdata = [jdata]

        for tobj in jdata:
            ttype = tobj.get('type')
            if not ttype:
                logger.warning("'type' not defined in %s", fpath)

            tobj['__loaded_from'] = fpath

            # on first use, create object (list, dict) for specific
            # 'type'; default is dict
            if self._data.get(ttype) is None:
                if ttype in C_TYPEMAP:
                    self._data[ttype] = C_TYPEMAP[ttype]()
                else:
                    self._data[ttype] = {}

            # update data store with new object
            if isinstance(self._data[ttype], dict):
                tid = tobj.get('id') if tobj.get('id') else tobj.get('abstract')
                if tid is None:
                    logger.warning("load_one_json: %s: expected 'id' field for type %s, but none defined", fpath, ttype)
                if self._data[ttype].get(ttype):
                    logger.warning("load_one_json: %s: type=%s id=%s already exists, but redefining!", fpath, ttype, tid)
                self._data[ttype][tid] = tobj
            elif isinstance(self._data[ttype], list):
                self._data[ttype].append(tobj)
            else:
                logger.error("type %s not implemented", str(type(self._data[ttype])))

        return True

    def _resolve_deps(self, rpass=1):
        """
        Resolve dependencies (copy-from, etc.)

        @pass determines which pass to perform. this should not be set by the caller,
        as this function will call itself again to do the remaining passes.
        Pass 1) Resolve abstract items first
        Pass 2) Resolve remaining items
        """
        logger.debug("resolving dependencies in gamedata: pass %d", rpass)
        for ttype in self._data:
            if C_TYPEMAP.get(ttype) is list:
                logger.debug("skipping type '%s'", ttype)
                continue

            for tid in self._data[ttype]:
                titem = self._data[ttype][tid]
                if rpass == 1 and titem.get('abstract') is None:
                    continue
                elif rpass == 2 and titem.get('abstract') is not None:
                    continue

                # check for dependencies
                if titem.get('copy-from'):
                    tdep_id = titem['copy-from']
                    tdep = self._data[ttype].get(tdep_id)
                    if tdep is None:
                        logger.error("%s: missing copy-from dependency '%s'", tid, tdep_id)
                        continue

                    # resolve subdeps up to 16 levels deep, bottom-up
                    deps = [tdep]
                    dep_ids = [tdep_id]
                    for i in range(16):
                        if tdep.get('copy-from'):
                            nextdep_id = tdep['copy-from']
                            nextdep = self._data[ttype].get(nextdep_id)
                            if nextdep is None:
                                logger.error("%s: missing copy-from dependency '%s'", tdep_id, nextdep_id)
                                break
                            deps.append(nextdep)
                            dep_ids.append(nextdep_id)
                            tdep_id = nextdep_id
                            tdep = nextdep
                        else:
                            break

                    # merge
                    newobj = {}
                    logger.debug("resolve deps: %s->%s", tid, '->'.join(dep_ids))
                    for tobj in reversed(deps):
                        newobj.update(tobj)
                    newobj.update(titem)
                    self._data[ttype][tid] = newobj

        if rpass == 1:
            return self._resolve_deps(rpass=2)
        return True

    def __getattr__(self, aname):
        if aname.startswith('_'):
            return super().__getattr__(aname)
        else:
            if aname in self._data:
                return self._data[aname]
            else:
                raise KeyError(aname)

    def __getitem__(self, aname):
        return self.__getattr__(aname)
