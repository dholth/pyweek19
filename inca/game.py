"""
Platformer for PyWeek 19, "One Room".

Daniel Holth <dholth@fastmail.fm>, 2014
"""

import sys

# Fix 'PyTMX requires pygame' bug:
class Psych(object):
    flip = None
    rotate = None
sys.modules['pygame'] = 'not needed'
sys.modules['pygame.transform'] = Psych

import sdl
import pytmx

class Game(object):
    """
    Our game.
    """
    title = u"One Room"

    def __init__(self):
        pass

    def run(self):
        sdl.init(sdl.INIT_EVERYTHING)

        self.window = sdl.createWindow(self.title,
                                       sdl.WINDOWPOS_UNDEFINED,
                                       sdl.WINDOWPOS_UNDEFINED,
                                       1280, 720,
                                       sdl.WINDOW_SHOWN)

        self.renderer = renderer = self.window.createRenderer(-1, 0)
        renderer.renderSetLogicalSize(420, 240)
        renderer.setRenderDrawColor(0xff,0xff,0xff,0xff)
        renderer.renderClear()
        renderer.renderPresent()
        sdl.delay(1000)
        self.quit()

    def quit(self):
        self.renderer.destroyRenderer()
        self.window.destroyWindow()
        sdl.quit()
