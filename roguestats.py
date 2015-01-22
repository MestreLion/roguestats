#!/usr/bin/env python
# coding: UTF-8
#
# roguestats.py: Statistics on Monsters and Levels for the game Rogue
#
#    Copyright (C) 2015 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. See <http://www.gnu.org/licenses/gpl.html>

'''Main module and entry point'''

# Next steps:
# - Numpy

import os
import sys
import string
import logging
import argparse
import hashlib
import json
import math
from xdg.BaseDirectory import xdg_cache_home

log = logging.getLogger(__name__)

MONSTERS = string.ascii_uppercase


def pretty(obj, indent=1, intlen=2, sortk=True, keylen=2, precision=1, simplelists=False, blankzeros=False, _lvl=0):
    '''Helper function to format lists and dictionaries'''
    sep = " " * indent
    kw = dict(indent=indent,
              intlen=intlen,
              sortk=sortk,
              keylen=keylen,
              precision=precision,
              simplelists=simplelists,
              blankzeros=blankzeros,
              )

    # Dictionaries
    if isinstance(obj, dict):
        return ('{\n%s%s\n%s}') % (
            sep * _lvl,
            (",\n%s" % (sep * _lvl)).join(['%*s: %s' % (keylen+2, '"%s"' % k, pretty(v, _lvl=_lvl+1, **kw))
                                           for k, v in sorted(obj.iteritems(),
                                                              key=lambda (k, v): (k, v)
                                                                                 if sortk
                                                                                 else (v, k))]),
            sep * (_lvl-1))

    elif isinstance(obj, (list, tuple)):

        # Lists of lists
        if not simplelists and obj and isinstance(obj[0], (list, tuple)):
            return ('[\n%s%s\n%s]') % (
                sep * _lvl,
                (",\n%s" % (sep * _lvl)).join(['%s' % pretty(v, _lvl=_lvl+1, **kw)
                                               for v in obj]),
                sep * (_lvl-1))

        # Simple lists
        else:
            return ('[ %s ]') % ", ".join([pretty(v, _lvl=_lvl+1, **kw)
                                         for v in obj])

    # Zeros
    elif blankzeros and obj == 0:
        if isinstance(obj, int):
            return " " * intlen
        else:
            return " " * (intlen + precision + 1)

    # Integers
    elif isinstance(obj, int):
        return "%*d" % (intlen, obj)

    # Floats
    elif isinstance(obj, float):
        return "%*.*f" % (intlen+precision+1, precision, obj)

    else:
        return '%*s' % (intlen, json.dumps(obj))


def monster_range(monsterlist):
    '''Calculate first and last level of a monster
        `monsterlist` is the level distribution of the monster
        Return a tuple (first, last), or (0, 0) if monster does not occur in any level
        (for example, Dragon is never spawned as a wander monster)
    '''
    minl = maxl = 0
    for level, num in enumerate(monsterlist, 1):
        if num > 0:
            if minl == 0:
                minl = level
            maxl = level
        else:
            if maxl != 0:
                break
    return minl, maxl


def read_data(fp, cachefile=None):
    ''' Parse the raw data into 2 dictionaries, wander and level monsters
    '''
    lmonsters = {}
    wmonsters = {}
    monsters = 0

    log.debug("Reading file '%s'", fp.name)
    for i, line in enumerate(fp):
        monsters += len(line) - 1  # discard trailing '\n'
        level = (i // 2) + 1
        if i % 2 == 0:
            d = lmonsters
        else:
            d = wmonsters
        d.setdefault(level, len(MONSTERS) * [0])
        for m, monster in enumerate(MONSTERS):
            d[level][m] += line.count(monster)

    assert len(lmonsters) == len(wmonsters), "Bad input data"

    lines = i + 1
    header = dict(filename=os.path.abspath(fp.name),
                  levels=lines / 2,
                  monstersperline=monsters / lines,
                  totalmonsters=monsters)

    # Save to cache
    if cachefile is not None:
        try:
            log.debug("Saving data to cache file '%s'", cachefile)
            data = dict(header=header,
                        lmonsters=lmonsters,
                        wmonsters=wmonsters,
                        monsters={"": list(MONSTERS)},
                        )
            try:
                os.makedirs(os.path.dirname(cachefile), 0700)
            except OSError as e:
                if e.errno != 17:  # File exists
                    raise

            with open(cachefile, 'w') as fp:
                intlen = int(math.log10(max(sum(lmonsters.values() +
                                                wmonsters.values(), [])))) + 1
                fp.write(pretty(data, intlen=intlen) + '\n')

        except IOError as e:
            log.warn("Could not write cache '%s': %s", cachefile, e)

    return lmonsters, wmonsters


def parseargs(argv=None):
    parser = argparse.ArgumentParser(
        description="Statistics on Monsters and Levels for the game Rogue",)

    parser.add_argument('--quiet', '-q', dest='loglevel',
                        const=logging.WARNING, default=logging.INFO,
                        action="store_const",
                        help="Suppress informative messages.")

    parser.add_argument('--verbose', '-v', dest='loglevel',
                        const=logging.DEBUG,
                        action="store_const",
                        help="Verbose mode, output extra info.")

    parser.add_argument('--level-weight', '-l', dest='level_weight', default=1, type=int,
                           help="Weight of monsters spawned at level initialization. [Default: %(default)s]")

    parser.add_argument('--wander-weight', '-w', dest='wander_weight', default=1, type=int,
                           help="Weight of wander monsters spawned afterwards.  [Default: %(default)s]")

    parser.add_argument('infile', nargs='?', default=sys.stdin,
                        type=argparse.FileType('r'),
                        help="Input file to process, as generated by C helper 'roguemonsters'"
                            "[Default: read from stdin]")

    args = parser.parse_args(argv)
    args.stdin = (args.infile.name == "<stdin>")  # not perfect detection, but good enough

    return args


def main(argv=None):
    args = parseargs(argv)
    logging.basicConfig(level=args.loglevel)

    # Level and Wander weights
    weights = (abs(args.level_weight),
               abs(args.wander_weight))

    # Read cache file, if available
    if not args.stdin:
        cachefile = os.path.join(xdg_cache_home,
                                 _myname,
                                 "%s_%s.json" % (_myname,
                                                 hashlib.md5(args.infile.name +
                                                             str(os.path.getmtime(args.infile.name))
                                                             ).hexdigest()))
        try:
            with open(cachefile, 'r') as fp:
                log.debug("Reading from cache file '%s'", cachefile)
                data = json.load(fp)
                lmonsters = data['lmonsters']
                wmonsters = data['wmonsters']
        except IOError:
            lmonsters, wmonsters = read_data(args.infile, cachefile)
    else:
        lmonsters, wmonsters = read_data(args.infile)

    # Add weighted Wander and Level monsters to get Levels dictionary
    levels = {level: [nl * weights[0] +
                      nw * weights[1]
                      for nl, nw in zip(ll, lw)]
              for level, ((_, ll), (_, lw))
              in enumerate(zip(sorted(lmonsters.iteritems(), key=lambda _: int(_[0])),
                               sorted(wmonsters.iteritems(), key=lambda _: int(_[0]))),
                           1)}

    # Normalize the data
    for level, data in levels.iteritems():
        total = sum(data)
        if total:
            levels[level] = [100. * _ / total for _ in data]

    # Transpose Levels to get Monsters
    monsters = {monster: [_[m] for _ in levels.itervalues()]
                for m, monster in enumerate(MONSTERS)}

    print "Main data: Monsters per Level, normalized as percentage of level"
    print pretty({"": list(MONSTERS)}, intlen=4)
    print pretty(levels,   blankzeros=True)
    print pretty(monsters, blankzeros=True)

    ranges = {monster: monster_range(data) for monster, data in monsters.iteritems()}

    print "Monsters level range: first and last level of each monster"
    print pretty(ranges, keylen=1)
    print "Sorted by level:"
    print pretty(ranges, keylen=1, sortk=False)

    print "Monster types in each level:"
    print pretty({level: "".join([MONSTERS[m]
                                  for m, num in enumerate(data)
                                  if num > 0])
                  for level, data in levels.iteritems()},
                 intlen=4)

    print "Monster distribution in each level, sorted by most frequent monster:"
    print pretty({level: "".join(zip(*sorted([(num, MONSTERS[m])
                                              for m, num in enumerate(data)
                                              if num > 0],
                                             reverse=True))[1])
                  for level, data in levels.iteritems()},
                 simplelists=True)

    print "Distribution in levels for each monster, sorted by most frequent level:"
    print pretty({monster: zip(*sorted([(num, level)
                                        for level, num in enumerate(data, 1)
                                        if num > 0],
                                       reverse=True))[1]
                  for monster, data in monsters.iteritems()},
                 simplelists=True, keylen=1)




if __name__ == '__main__':
    _myname = os.path.basename(os.path.splitext(__file__)[0])
    sys.exit(main())
else:
    _myname = __name__
