#!/usr/bin/env python
from ants import *

# define a class with a do_turn method
# the Ants.run method will parse and update bot input
# it will also run the do_turn method for us
class MyBot:
  def __init__(self):
    # define class level variables, will be remembered between turns
    pass

  # do_setup is run once at the start of the game
  # after the bot has received the game settings
  # the ants class is created and setup by the Ants.run method
  def do_setup(self, ants):
    # initialize data structures after learning the game settings
    pass

  # do turn is run once per turn
  # the ants class has the game state and is updated by the Ants.run method
  # it also has several helper methods to use
  def do_turn(self, ants):
    # track all moves, prevent collisions
    orders = {}
    def do_move_direction(loc, direction):
      new_loc = ants.destination(loc, direction)
      if (ants.unoccupied(new_loc) and new_loc not in orders):
        ants.issue_order((loc, direction))
        orders[new_loc] = loc
        return True
      else:
        return False

    # default move
    for ant_loc in ants.my_ants():
      directions = ('n','e','s','w')
      for direction in directions:
        if do_move_direction(ant_loc, direction):
          break

if __name__ == '__main__':
  # psyco will speed up python a little, but is not needed
  try:
    import psyco
    psyco.full()
  except ImportError:
    pass

  try:
    # if run is passed a class with a do_turn method, it will do the work
    # this is not needed, in which case you will need to write your own
    # parsing function and your own game state class
    Ants.run(MyBot())
  except KeyboardInterrupt:
    print('ctrl-c, leaving ...')
