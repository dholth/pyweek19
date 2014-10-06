"""
Platformer for PyWeek 19, "One Room".

Daniel Holth <dholth@fastmail.fm>, 2014
"""

import sys
import pkg_resources
import textwrap

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
        sdl.ttf.init()

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
        sdl.delay(500)
        self.story = Story(self)
        self.story.show(renderer)
        sdl.delay(6000)

        self.quit()

    def quit(self):
        self.title.destroy()
        self.renderer.destroyRenderer()
        self.window.destroyWindow()
        sdl.quit()


class CenteredSprite(object):
    def __init__(self, renderer, surface):
        self.w = surface.w
        self.h = surface.h
        self.image_tex = renderer.createTextureFromSurface(surface)
        self.renderer = renderer
        surface.freeSurface()

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


class ImageSprite(CenteredSprite):
    """CenteredSprite loaded from image filename rather than a surface."""
    def __init__(self, renderer, name):
        image = sdl.image.load(name)
        super(ImageSprite, self).__init__(renderer, image)


class Story(object):
    """
    Story? Who needs a story???
    """

    text = textwrap.dedent(
        u"The year is 1532. "
        u"The Inca Atahualpa has been captured by the Spanish. "
        u"To spare his life, the Inca offers to pay a ransom - "
        u"Filling a large room once with gold, and twice with silver. "
        u"\nIt's your job to go and get it.")

    def __init__(self, game):
        fg = sdl.Color((0,0,0,0xff)).cdata[0]
        self.font = sdl.ttf.openFont(resource('fonts/kenpixel.ttf'), 8)
        surf = sdl.ttf.renderUTF8_Blended_Wrapped(self.font,
                                                  self.text,
                                                  fg,
                                                  game.size[1])
        self.sprite = CenteredSprite(game.renderer, surf)

    def show(self, renderer):
        renderer.setRenderDrawColor(*WHITE)
        renderer.renderClear()
        self.sprite.show(renderer)
        renderer.renderPresent()


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

    def destroy(self):
        self.image.destroy()