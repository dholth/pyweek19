"""
Run with 'python -m inca'
"""
import logging
logging.basicConfig(level=logging.DEBUG)

import inca.game
game = inca.game.Game()
game.init()
game.run()