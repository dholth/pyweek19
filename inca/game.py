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

from .util import clamp

log = logging.getLogger(__name__)

SHOW_INTRO = True

def resource(name):
    """
    Return a resource_filename from within our package.
    """
    return pkg_resources.resource_filename('inca', 'resources/' + name)

# Trick PyTMX into not requiring pygame
class Psych(object):
    flip = None
    rotate = None
sys.modules['pygame'] = 'not needed'
sys.modules['pygame.transform'] = Psych

import pytmx
import inca.map

WHITE = (0xff, 0xff, 0xff, 0xff)
BLACK = (0, 0, 0, 0xff)

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
        self.action = 0

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
        self.action = 0

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
    
        if keystate[sdl.SCANCODE_SPACE]:
            self.action = 1

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
                
            button = gamepad.gameControllerGetButton(sdl.CONTROLLER_BUTTON_B)
            if button:
                self.action = 1

GRAVITY = 8 * 9.8
VY_MAX = 60
VX_MAX = 60
ACCEL = 120
DRAG = 2.0
V_JUMP = -60

debug_points = []

class Physics(object):
    """
    Animate all sprites based on physics.
    """
    GRAVITY = GRAVITY
    VX_MAX = VX_MAX
    VY_MAX = VY_MAX

    def __init__(self, game):
        self.game = game
        
    def tick(self, dt):
        tmx = self.game.map.tmx
        coord_min = (0, 0)
        coord_max = (tmx.width * (tmx.tilewidth - 1),
                     tmx.height * (tmx.tileheight - 1))
        collideable = tmx.get_layer_by_name('Solid')
        treasure = tmx.get_layer_by_name('Treasure')
        for actor in self.game.actors:
            actor.vx = min(actor.vx, self.VX_MAX)
            if getattr(actor, 'mass', 0):
                actor.vy = min(actor.vy + self.GRAVITY * dt, self.VY_MAX)
            actor.y += actor.vy * dt
            actor.x += actor.vx * dt
            actor.x = clamp(actor.x, coord_min[0], coord_max[0])
            actor.y = clamp(actor.y, coord_min[1], coord_max[1])
            self.collide_world(actor, collideable, treasure, dt)
            
    def collide_world(self, actor, layer, treasure, dt):
        tile_size = (layer.parent.tilewidth, layer.parent.tileheight)
        center = ((int(actor.x) + tile_size[0] / 2),
                  (int(actor.y) + tile_size[1] / 2))
        
        # check to see if points near the corners of the actor
        # have collided with the world:
        test_points = [(center[0] - tile_size[0] // 4, actor.y + tile_size[1]),
                       (center[0] + tile_size[0] // 4, actor.y + tile_size[1]),
                       (center[0] - tile_size[0] // 4, actor.y + tile_size[1] - 6),
                       (center[0] + tile_size[0] // 4, actor.y + tile_size[1] - 6)]
        # debug_points.extend(test_points)

        on_tiles = [(int(point[0] // tile_size[0]), 
                     int(point[1] // tile_size[1])) for point in test_points]

        for on_tile in on_tiles:                           
            # Kill if outside map...
            if not ((0 <= on_tile[0] < layer.width) and
                (0 <= on_tile[1] < layer.height)):
                actor.vx = 0
                actor.vy = 0
                actor.mass = 0
                return
        
        sensors = [layer.data[on_tile[1]][on_tile[0]] for on_tile in on_tiles]
        
        if (sensors[0] and not sensors[2]) or (sensors[1] and not sensors[3]):
            actor.vx = actor.vx - (actor.vx * DRAG * dt)
            actor.vy = 0
            # may need to interleave move x, collide horizontal, 
            # move y, collide vertical operations in a specific
            # order for best behavior 
            actor.y = on_tile[1] * tile_size[1]
        
        if any(sensors):
            if actor.jump:
                actor.vy = V_JUMP
            else:
                actor.vy = 0
                
        # horizontal collision; offsets are specific for the character sprites
        # since they are narrower than the full 16px width.
        test_points = [
               (center[0] - 5, actor.y + tile_size[1] - 4),
               (center[0] + 5, actor.y + tile_size[1] - 4)]
        debug_points.extend(test_points)
        
        on_tiles = [(int(point[0]) // tile_size[0], 
                     int(point[1]) // tile_size[1]) for point in test_points]
        
        # wonky
        for gid in [treasure.data[on_tile[1]][on_tile[0]] for on_tile in set(on_tiles)]:
            if gid:
                treasure.data[on_tile[1]][on_tile[0]] = 0
        
        sensors = [layer.data[on_tile[1]][on_tile[0]] for on_tile in on_tiles]
        
        for i, gid in enumerate(sensors):
            if gid:
                if actor.action:
                    props = layer.parent.get_tile_properties_by_gid(gid)
                    if props and props.get('name', '') == 'Door':
                        layer.data[on_tiles[i][1]][on_tiles[i][0]] = 0
        
        for test, point in zip(sensors, test_points):
            if test:
                debug_points.append(point)
        
        if sensors[0]:
            debug_points.append(((on_tiles[1][0]) * tile_size[0] - 3, actor.y))
            actor.x = int(debug_points[-1][0])
            actor.vx = 0
            
        if sensors[1]:
            debug_points.append(((on_tiles[1][0] - 1) * tile_size[0] + 3, actor.y))
            actor.x = int(debug_points[-1][0])
            actor.vx = 0

class Game(object):
    """
    Our game.

    :type renderer: sdl.Renderer
    """
    window_title = u"One Room"
    window_size = (420, 240)

    def __init__(self):
        self.actors = []

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

        if SHOW_INTRO:
            self.title = Title(self)
            self.title.show()
            sdl.delay(1000)

            self.story = Story(self)
            self.story.show(renderer)
            sdl.delay(8000)

        self.critters = pytmx.TiledMap(resource('levels/critters.tmx'))
        self.map = inca.map.Map(resource('levels/level_1.tmx'))
        self.map.load_images(renderer)
        
        def load_actors():
            for ob in self.map.tmx.objects:          
                ob.mass = 1
                ob.vx = 0
                ob.vy = 0
                ob.jump = 0
                ob.action = 0
                self.actors.append(ob)

        load_actors()
        
        hero = None
        for actor in self.actors:
            if actor.name and 'Hero' in actor.name:
                hero = actor

        self.physics = Physics(self)

        event = sdl.Event()
        running = True

        input_handler = Input()

        def getSeconds():
            return sdl.getTicks() / 1000.

        last_frame = getSeconds()
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
                    
            frame = getSeconds()
            dt = frame - last_frame
            last_frame = frame
            
            self.physics.tick(dt)

            input_handler.frame()
            
            hero.vx += input_handler.x_axis * ACCEL * dt
            # hero.y += current_input.y_axis.
            hero.jump = input_handler.jump
            hero.action = input_handler.action

            self.map.look_at(int(hero.x), int(hero.y))

            renderer.setRenderDrawColor(*BLACK)
            renderer.renderClear()
            self.map.render(renderer)
            
            renderer.setRenderDrawColor(*WHITE)
            
            debug_points[:] = []
            while debug_points:
                point = debug_points.pop()
                renderer.renderDrawPoint(int(point[0] - self.map.pos[0]),
                                         int(point[1] - self.map.pos[1]))

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
        fg = sdl.Color((0, 0, 0, 0xff)).cdata[0]
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
