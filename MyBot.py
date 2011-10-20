#!/usr/bin/env python
from ants import *

class MyBot:
  def __init__(self):
    # define class level variables, will be remembered between turns
    pass

  def do_setup(self, ants):
    self.hills = []
    self.unseen = []
    for row in range(ants.rows):
      for col in range(ants.cols):
        self.unseen.append((row, col))

  def do_move_direction(self, loc, direction, ants):
    new_loc = ants.destination(loc, direction)
    if (ants.unoccupied(new_loc) and new_loc not in self.orders):
      ants.issue_order((loc, direction))
      self.orders[new_loc] = loc
      return True
    else:
      return False

  def do_move_location(self, loc, dest, ants):
    directions = ants.direction(loc, dest)
    for direction in directions:
      if self.do_move_direction(loc, direction, ants):
        self.targets[dest] = loc
        return True
        break
    else:
      return False

  def find_food(self, ants):
    ant_dist = []
    for food_loc in ants.food():
      for ant_loc in ants.my_ants():
        dist = ants.distance(ant_loc, food_loc)
        ant_dist.append((dist, ant_loc, food_loc))
    ant_dist.sort()
    for dist, ant_loc, food_loc in ant_dist:
      if food_loc not in self.targets and ant_loc not in self.targets.values():
        self.do_move_location(ant_loc, food_loc, ants)

  def find_hills(self, ants):
    for hill_loc, hill_owner in ants.enemy_hills():
      if hill_loc not in self.hills:
        self.hills.append(hill_loc)
    ant_dist = []
    for hill_loc in self.hills:
      for ant_loc in ants.my_ants():
        if ant_loc not in self.orders.values():
          dist = ants.distance(ant_loc, hill_loc)
          ant_dist.append((dist, ant_loc))
    ant_dist.sort()
    for dist, ant_loc in ant_dist:
      self.do_move_location(ant_loc, hill_loc, ants)

  def find_new_territory(self, ants):
    for loc in self.unseen[:]:
      if ants.visible(loc):
        self.unseen.remove(loc)
    for ant_loc in ants.my_ants():
      if ant_loc not in self.orders.values():
        unseen_dist = []
        for unseen_loc in self.unseen:
          dist = ants.distance(ant_loc, unseen_loc)
          unseen_dist.append((dist, unseen_loc))
        unseen_dist.sort()
        for dist, unseen_loc in unseen_dist:
          if self.do_move_location(ant_loc, unseen_loc, ants):
            break

  def unblock_hills(self, ants):
    for hill_loc in ants.my_hills():
      if hill_loc in ants.my_ants() and hill_loc not in self.orders.values():
        for direction in ('n','e','s','w'):
          if self.do_move_direction(hill_loc, direction, ants):
            break

  def do_turn(self, ants):
    self.orders = {}
    self.targets = {}
    for hill_loc in ants.my_hills():
      self.orders[hill_loc] = None

    self.find_food(ants)
    self.find_hills(ants)
    self.find_new_territory(ants)
    self.unblock_hills(ants)

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
