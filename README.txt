Running the Game
================

This game requires PyPy, pysdl2-cffi, and pytmx. You will have to install PyPy
manually, and install pip into PyPy. (Technically it should just run more slowly 
in CPython.) 

After that, the easiest way to install the dependencies is to run 
"pip install -e ." in its directory. Then run the game with "python -m inca". 
The game is written for Python 2.7.

Use arrow keys, shift to jump, and space bar for action.

This game also supports gamepads.

Installing pysdl2-cffi
======================

pysdl2-cffi requires the SDL2 libraries to be installed, and this game uses
SDL2, SDL_ttf, and SDL_image. pysdl2-cffi has its own installation instructions.
On OSX, it's best to install the Framework builds into /Library/Frameworks/...;
on Windows, install the 32-bit versions of Python and SDL2, and make sure the
SDL2 dlls are on PATH or in the current directory. On Linux just install with 
the OS package manager.  