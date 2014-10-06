"""
Platformer for PyWeek 19, "One Room".

Daniel Holth <dholth@fastmail.fm>, 2014
"""

import sys
import pkg_resources

def resource(name):
    """
    Return a resource_filename from within our package.
    """
    return pkg_resources.resource_filename('inca', 'resources/'+name)

# Trick PyTMX into not requiring pygame
class Psych(object):
    flip = None
    rotate = None
sys.modules['pygame'] = 'not needed'
sys.modules['pygame.transform'] = Psych

import sdl
import pytmx

WHITE = (0xff,0xff,0xff,0xff)
BLACK = (0,0,0,0xff)

class Game(object):
    """
    Our game.

    :type renderer: sdl.Renderer
    """
    title = u"One Room"
    size = (420, 240)

    def __init__(self):
        pass

    def run(self):
        sdl.init(sdl.INIT_EVERYTHING)
        sdl.image.init(sdl.image.INIT_PNG)

        self.window = sdl.createWindow(self.title,
                                       sdl.WINDOWPOS_UNDEFINED,
                                       sdl.WINDOWPOS_UNDEFINED,
                                       1280, 720,
                                       sdl.WINDOW_SHOWN)

        self.renderer = renderer = self.window.createRenderer(-1, 0)
        renderer.renderSetLogicalSize(*self.size)
        renderer.setRenderDrawColor(*WHITE)
        renderer.renderClear()
        renderer.renderPresent()

        self.title = Title(self)
        self.title.show()

        self.quit()

    def quit(self):
        self.title.destroy()
        self.renderer.destroyRenderer()
        self.window.destroyWindow()
        sdl.quit()


class ImageSprite(object):
    def __init__(self, renderer, name):
        image = sdl.image.load(name)
        self.w = image.w
        self.h = image.h
        self.image_tex = renderer.createTextureFromSurface(image)
        self.renderer = renderer
        image.freeSurface()

    def show(self, renderer):
        """
        Center and display image.
        """
        w, h = renderer.renderGetLogicalSize()[-2:]
        print w, h
        offset_x = (w - self.w) // 2
        offset_y = (h - self.h) // 2
        renderer.renderCopy(self.image_tex, None,
                            (offset_x, offset_y, self.w, self.h))

    def destroy(self):
        self.image_tex.destroyTexture()

class Title(object):
    """
    Show the title screen.
    """
    def __init__(self, game):
        """
        :type game: Game
        """
        self.game = game
        self.image = ImageSprite(self.game.renderer, resource('title.png'))

    def show(self):
        renderer = self.game.renderer
        renderer.setRenderDrawColor(*WHITE)
        self.image.show(renderer)
        renderer.renderPresent()
        sdl.delay(2000)

    def destroy(self):
        self.image.destroy()