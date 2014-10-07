"""
Platformer for PyWeek 19, "One Room".

Daniel Holth <dholth@fastmail.fm>, 2014
"""

import math
import sys
import pkg_resources
import textwrap
import logging

import sdl

log = logging.getLogger(__name__)

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

import inca.map

WHITE = (0xff,0xff,0xff,0xff)
BLACK = (0,0,0,0xff)

class Input(object):
    """
    Handle input events from sdl, converting them into game commands.
    """
    DEAD_ZONE = 32768 // 4

    def __init__(self):
        self.gamepads = []
        self.x_axis = 0
        self.y_axis = 0
        self.jump = 0

    def handle(self, event):
        """
        Return True if event was handled by us.
        """
        if event.type == sdl.CONTROLLERDEVICEADDED:
            gamepad = sdl.gameControllerOpen(event.cdevice.which)
            self.gamepads.append(gamepad)
            return True
        elif event.type == sdl.CONTROLLERDEVICEREMOVED:
            which = event.cdevice.which
            gamepads = [gamepad for gamepad in self.gamepads
                if sdl.joystickInstanceID(sdl.gameControllerGetJoystick(gamepad)) == which]
            self.gamepads = gamepads
            log.debug("%r", self.gamepads)
            return True
        return False

    def frame(self):
        """
        Make sense of input state.
        """
        self.x_axis = 0
        self.y_axis = 0
        self.jump = 0

        keystate, _ = sdl.getKeyboardState()
        if keystate[sdl.SCANCODE_LEFT]:
            self.x_axis = -1
        elif keystate[sdl.SCANCODE_RIGHT]:
            self.x_axis = 1

        if keystate[sdl.SCANCODE_UP]:
            self.y_axis = -1
        elif keystate[sdl.SCANCODE_DOWN]:
            self.y_axis = 1

        if keystate[sdl.SCANCODE_LSHIFT]:
            self.jump = 1

        for gamepad in self.gamepads:
            x_axis = gamepad.gameControllerGetAxis(sdl.CONTROLLER_AXIS_LEFTX)
            if abs(x_axis) > self.DEAD_ZONE:
                self.x_axis = math.copysign(1, x_axis)

            y_axis = gamepad.gameControllerGetAxis(sdl.CONTROLLER_AXIS_LEFTY)
            if abs(y_axis) > self.DEAD_ZONE:
                self.y_axis = math.copysign(1, y_axis)

            button = gamepad.gameControllerGetButton(sdl.CONTROLLER_BUTTON_A)
            if button:
                self.jump = 1

        return dict(x_axis=self.x_axis, y_axis=self.y_axis, jump=self.jump)

class Game(object):
    """
    Our game.

    :type renderer: sdl.Renderer
    """
    window_title = u"One Room"
    window_size = (420, 240)

    def __init__(self):
        pass

    def init(self):
        sdl.init(sdl.INIT_EVERYTHING)
        sdl.image.init(sdl.image.INIT_PNG)
        sdl.ttf.init()

        self.window = sdl.createWindow(self.window_title,
                                       sdl.WINDOWPOS_UNDEFINED,
                                       sdl.WINDOWPOS_UNDEFINED,
                                       1280, 720,
                                       sdl.WINDOW_HIDDEN)

        self.renderer = self.window.createRenderer(-1, sdl.RENDERER_PRESENTVSYNC)

    def run(self):
        self.window.showWindow()

        renderer = self.renderer
        renderer.renderSetLogicalSize(*self.window_size)
        renderer.setRenderDrawColor(*WHITE)
        renderer.renderClear()
        renderer.renderPresent()

        if False:
            self.title = Title(self)
            self.title.show()
            sdl.delay(1000)

            self.story = Story(self)
            self.story.show(renderer)
            sdl.delay(8000)

        self.map = inca.map.Map(resource('levels/level_1.tmx'))
        self.map.load_images(renderer)

        event = sdl.Event()
        running = True

        input_handler = Input()

        last_input = {}

        look_x = 0
        look_y = 0

        while running:
            while event.pollEvent():
                if input_handler.handle(event):
                    continue
                elif event.type == sdl.QUIT:
                    running = False
                    break
                elif event.type == sdl.KEYDOWN:
                    if event.key.keysym.sym == sdl.K_ESCAPE:
                        running = False
                        break
            current_input = input_handler.frame()
            if current_input != last_input:
                print current_input
                last_input = current_input
            look_x += current_input['x_axis']
            look_y += current_input['y_axis']

            self.map.look_at(look_x, look_y)

            renderer.setRenderDrawColor(*BLACK)
            renderer.renderClear()
            self.map.render(renderer)
            renderer.renderPresent()

        self.quit()

    def quit(self):
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
                                                  game.window_size[1])
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
