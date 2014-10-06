"""
Load and render TMX maps, including camera logic.
"""

import inca.game

import os
import re
import sdl
import itertools
import logging

import pytmx
from pytmx.constants import TRANS_FLIPX, TRANS_FLIPY, TRANS_ROT

pytmx.load_pygame

log = logging.getLogger(__name__)

class Map(object):
    def __init__(self, filename):
        self.tmx = pytmx.TiledMap(filename)

    def load_images(self, renderer):
        """
        :type renderer: sdl.Renderer
        """
        sdl.image.init(sdl.image.INIT_PNG) # XXX okay to call multiple times?
        _load_images_sdl(self.tmx)
        # now load as textures...
        textures = {}
        for item in self.tmx.images:
            if item == 0: continue
            ts, bounds, flags = item
            if not ts.source in textures:
                textures[ts.source] = \
                    renderer.createTextureFromSurface(ts.image)
                ts.texture = textures[ts.source]

    def render(self, renderer):
        dest_rect = sdl.Rect((0,0,16,16))
        for x, y in itertools.product(range(self.tmx.width),
                                      range(self.tmx.height)):
            for layer in self.tmx.visible_tile_layers:
                image = self.tmx.get_tile_image(x, y, layer)
                if not image:
                    continue
                ts, bounds, flags = image
                dest_rect.x = x * 16
                dest_rect.y = y * 16
                renderer.renderCopy(ts.texture,
                                    (bounds[0][0], bounds[0][1],
                                     bounds[1][0], bounds[1][1]),
                                    dest_rect)

class Color(object):
    """Color from hex specification."""
    def __init__(self, spec):
        r, g, b = (int(x, 16) for x in re.findall('..', spec))
        self.rgba = (r, g, b, 0xff)

    def __repr__(self):
        return "Color('"+"".join(("%02x" % x) for x in self.rgba[:3])+"')"

def _load_images_sdl(tmxdata, *args, **kwargs):
    """  Utility function to load images.  Used internally!

    Modified from the pygame-specific pytmx loader.
    """

    # optional keyword arguments checked here
    pixelalpha = kwargs.get('pixelalpha', True)
    optional_gids = kwargs.get('optional_gids', None)
    load_all_tiles = kwargs.get('load_all', False)

    # change background color into something nice
    if tmxdata.background_color:
        tmxdata.background_color = Color(tmxdata.background_color)

    # initialize the array of images
    tmxdata.images = [0] * tmxdata.maxgid

    # load tileset image
    for ts in tmxdata.tilesets:
        # skip the tileset if it doesn't include a source image
        if ts.source is None:
            continue

        # Image loading is required to get width/height, but we will convert
        # it to subsurfaces or textures later:
        path = os.path.join(os.path.dirname(tmxdata.filename), ts.source)
        image = ts.image = sdl.image.load(path)
        w, h = image.w, image.h

        # margins and spacing
        tilewidth = ts.tilewidth + ts.spacing
        tileheight = ts.tileheight + ts.spacing
        tile_size = ts.tilewidth, ts.tileheight

        # some tileset images may be slightly larger than the tile area
        # ie: may include a banner, copyright, etc.  this compensates for that
        width = int((((w - ts.margin * 2 + ts.spacing) // tilewidth) * tilewidth) - ts.spacing)
        height = int((((h - ts.margin * 2 + ts.spacing) // tileheight) * tileheight) - ts.spacing)

        # trim off any pixels on the right side that isn't a tile.
        # this happens if extra stuff is included on the left, like a logo or
        # credits, not actually part of the tileset.
        width -= (w - ts.margin) % tilewidth

        # using product avoids the overhead of nested loops
        p = itertools.product(range(ts.margin, height + ts.margin, tileheight),
                              range(ts.margin, width + ts.margin, tilewidth))

        colorkey = getattr(ts, 'trans', None)
        if colorkey:
            colorkey = Color(colorkey)

        for real_gid, (y, x) in enumerate(p, ts.firstgid):
            if x + ts.tilewidth-ts.spacing > width:
                continue

            # map_gid returns a list of internal pytmx gids to load
            gids = tmxdata.map_gid(real_gid)

            # user may specify to load all gids, or to load a specific one
            if gids is None:
                if load_all_tiles or real_gid in optional_gids:
                    # TODO: handle flags? - might never be an issue, though
                    gids = [tmxdata.register_gid(real_gid, flags=0)]

            if gids:
                try:
                    bounds = ((x, y), tile_size)
                except ValueError:
                    log.error('Tile bounds outside bounds of tileset image')
                    raise

                for gid, flags in gids:
                    tmxdata.images[gid] = (ts, bounds, flags)

    # Dropped from pytmx:
    # load image layer images.
    # load images in tiles.

def test():
    game = inca.game.Game()
    game.init()
    map = Map(inca.game.resource('levels/level_1.tmx'))
    map.load_images(game.renderer)
    return (game, map)

if __name__ == "__main__":
    game, map = test()
