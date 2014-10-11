"""
Load and render TMX maps, including camera logic.
"""

import inca.game

import os
import re
import sdl
import itertools
import logging

from .util import clamp

import pytmx
from pytmx.constants import TRANS_FLIPX, TRANS_FLIPY, TRANS_ROT

log = logging.getLogger(__name__)

class Map(object):
    def __init__(self, filename, screen_size=(420,240)):
        self.tmx = pytmx.TiledMap(filename)
        self.pos = [0, 0]
        self.tile_size = [16, 16]
        self.screen_size = screen_size
        
    @property
    def width_px(self):
        return self.tmx.width * self.tile_size[0]
    
    @property
    def height_px(self):
        return self.tmx.height * self.tile_size[1]
    
    def look_at(self, x, y):
        """
        Camera logic.
        1. Camera does not like to move. The character should stay within an
           imaginary box centered on the screen.
        2. Camera does not like to show outside the map.
        TODO: Take into account direction of travel.
        """        
        slack = 30
        
        newpos = self.pos[:]
        
        centered = [x - self.screen_size[0] / 2,
                    y - self.screen_size[1] / 2]

        if centered[0] > newpos[0] + slack:
            newpos[0] = centered[0] - slack
        elif centered[0] < newpos[0] - slack:
            newpos[0] = centered[0] + slack

        newpos[0] = clamp(newpos[0], 0, max(0, self.width_px - self.screen_size[0]))
        newpos[1] = clamp(newpos[1], 0, self.height_px - self.screen_size[1])
                
        self.pos = newpos

    def load_images(self, renderer):
        """
        :type renderer: sdl.Renderer
        """
        sdl.image.init(sdl.image.INIT_PNG)  # XXX okay to call multiple times?
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
        viewport = sdl.Rect()
        renderer.renderGetViewport(viewport)
        
        # Only render those tiles inside our viewport with a little overlap
        ranges = []
        for (pos, tile_size, dimension, ceiling) in \
            ((self.pos[0], self.tile_size[0], viewport.w, self.tmx.width),
             (self.pos[1], self.tile_size[1], viewport.h, self.tmx.height)):
            start = max(0, pos // tile_size)
            end = min(start + dimension // tile_size + 2, ceiling)
            ranges.append(xrange(start, end))
        
        dest_rect = sdl.Rect((0, 0, 16, 16))
        for x, y in itertools.product(*ranges):
            for layer in self.tmx.visible_tile_layers:
                image = self.tmx.get_tile_image(x, y, layer)
                if not image:
                    continue
                ts, bounds, flags = image
                dest_rect.x = (x * 16) - self.pos[0]
                dest_rect.y = (y * 16) - self.pos[1]
                rot = 90 if (flags & TRANS_ROT) else 0
                renderer.renderCopyEx(ts.texture,
                    (bounds[0][0], bounds[0][1],
                     bounds[1][0], bounds[1][1]),
                     dest_rect,
                     rot,
                     None,
                     (flags & (TRANS_FLIPX ^ (rot and TRANS_FLIPX)) and sdl.FLIP_HORIZONTAL) |
                     (flags & (TRANS_FLIPY) and sdl.FLIP_VERTICAL))

        for ob in self.tmx.objects:
            ts, bounds, flags = self.tmx.get_tile_image_by_gid(ob.gid)
            renderer.renderCopyEx(ts.texture,
                    (bounds[0][0], bounds[0][1],
                     bounds[1][0], bounds[1][1]),
                     (int(ob.x) - self.pos[0], int(ob.y) - self.pos[1], 
                      bounds[1][0], bounds[1][1]),
                     0,
                     None,
                     0)

class Color(object):
    """Color from hex specification."""
    def __init__(self, spec):
        r, g, b = (int(x, 16) for x in re.findall('..', spec))
        self.rgba = (r, g, b, 0xff)

    def __repr__(self):
        return "Color('" + "".join(("%02x" % x) for x in self.rgba[:3]) + "')"

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
            key = sdl.mapRGB(image.format, *colorkey.rgba[:3])
            image.setColorKey(True, key)

        for real_gid, (y, x) in enumerate(p, ts.firstgid):
            if x + ts.tilewidth - ts.spacing > width:
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
