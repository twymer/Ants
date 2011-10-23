#!/usr/bin/env python
from random import shuffle
from ants import *
import logging

from time import time

class MyBot:
  # define class level variables, will be remembered between turns
  def __init__(self):
    self.checked_paths = set()
    self.direction_time = 0
    self.destination_time = 0
    self.food_time = 0
    self.hill_time = 0
    self.new_time = 0
    self.wander_time = 0
    self.unblock_time = 0

  def do_setup(self, ants):
    self.hills = []
    self.unseen = []
    for row in range(ants.rows):
      for col in range(ants.cols):
        self.unseen.append((row, col))

  def inactive_ants(self, ants):
    return [ant_loc for ant_loc in ants.my_ants() if ant_loc not in self.orders.values()]

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

  #TODO: At this state, path exists just checks for a direct
  # navigatable path. Later we should search for a path possibility and
  # follow that.
  def path_exists(self, loc, dest, ants):
    step_loc = loc
    if loc == dest:
      return True

    while step_loc != dest:
      t = time()
      directions = ants.direction(step_loc, dest)
      self.direction_time += time() - t
      for direction in directions:
        t = time()
        step_loc = ants.destination(step_loc, direction)
        self.destination_time += time() - t
        if ants.passable(step_loc):
          break
      else:
        # We hit this when all directions were not passable
        #logging.error("Direction time: " + str(self.direction_time))
        #logging.error("Destination time: " + str(self.destination_time))
        return False
    #logging.error("Direction time: " + str(self.direction_time))
    #logging.error("Destination time: " + str(self.destination_time))
    return True

    #if not ants.passable(dest):
    #  return False

    ##TODO: Using ants direction to step this probably isn't good
    #test_loc = loc
    ##TODO: Recurse this or track steps so we can bubble back up
    ## and memoize them
    #loc_list = set()
    #while test_loc != dest:
    #  loc_list.add(test_loc)
    #  if (test_loc, dest, True) in self.checked_paths:
    #    for good_loc in loc_list:
    #      self.checked_paths.add((good_loc, dest, True))
    #    return True
    #  elif (test_loc, dest, False) in self.checked_paths:
    #    for bad_loc in loc_list:
    #      self.checked_paths.add((bad_loc, dest, False))
    #    return False
    #  directions = ants.direction(test_loc, dest)
    #  #TODO: More than one direction
    #  direction = directions[0]
    #  logging.error("*****")
    #  test_loc = ants.destination(test_loc, direction)
    #  logging.error("new loc: " + str(test_loc))
    #  logging.error("dest: " + str(dest))
    #  if not ants.passable(test_loc):
    #    for bad_loc in loc_list:
    #      self.checked_paths.add((good_loc, dest, False))
    #    return False
    #for good_loc in loc_list:
    #  self.checked_paths.add((good_loc, dest, True))
    #return True

  def find_food(self, ants):
    ant_dist = []
    for food_loc in ants.food():
      for ant_loc in ants.my_ants():
        dist = ants.distance(ant_loc, food_loc)
        ant_dist.append((dist, ant_loc, food_loc))
    ant_dist.sort()
    for dist, ant_loc, food_loc in ant_dist:
      if food_loc not in self.targets and ant_loc not in self.targets.values():
        # TODO: Instead of bailing on this food if a path isn't known, 
        # we should still move in the best direction possible.
        #logging.error("Find food path exists: " + str(ant_loc) + str(food_loc))
        if self.path_exists(ant_loc, food_loc, ants):
          self.do_move_location(ant_loc, food_loc, ants)

  def find_hills(self, ants):
    for hill_loc, hill_owner in ants.enemy_hills():
      if hill_loc not in self.hills:
        self.hills.append(hill_loc)
    ant_dist = []
    for hill_loc in self.hills:
      for ant_loc in self.inactive_ants(ants):
        # TODO: Instead of bailing on this food if a path isn't known, 
        # we should still move in the best direction possible.
        #logging.error("Find hills path exists: " + str(ant_loc) + str(hill_loc))
        if ant_loc not in self.orders.values():
          if self.path_exists(ant_loc, hill_loc, ants):
            dist = ants.distance(ant_loc, hill_loc)
            ant_dist.append((dist, ant_loc))
    ant_dist.sort()
    for dist, ant_loc in ant_dist:
      self.do_move_location(ant_loc, hill_loc, ants)

  def find_new_territory(self, ants):
    return True
    count = 0
    for loc in self.unseen[:]:
      if ants.visible(loc):
        self.unseen.remove(loc)
    for ant_loc in self.inactive_ants(ants):
      unseen_dist = []
      for unseen_loc in self.unseen:
        dist = ants.distance(ant_loc, unseen_loc)
        unseen_dist.append((dist, unseen_loc))
      unseen_dist.sort()
      for dist, unseen_loc in unseen_dist:
        # TODO: Instead of bailing on this food if a path isn't known, 
        # we should still move in the best direction possible.
        #logging.error(str(ant_loc))
        #logging.error(str(self.orders.values()))
        if ant_loc in self.orders.values():
          break
        count += 1
        if count > 15:
          # this is getting expensive, get out before we timeout!
          break
        if self.path_exists(ant_loc, unseen_loc, ants):
          if self.do_move_location(ant_loc, unseen_loc, ants):
            break
        else:
          break

    #logging.error("count: " + str(count))

  def wander_like_a_drunk(self, ants):
    # TODO: NOT REALLY RANDOM?
    directions = ['n','e','s','w']
    for ant_loc in ants.my_ants():
      if ant_loc not in self.orders.values():
        shuffle(directions)
        for direction in directions:
          if self.do_move_direction(ant_loc, direction, ants):
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

    #logging.error("Start turn")

    t = time()
    #logging.error("find food")
    self.find_food(ants)
    self.food_time += time() - t

    t = time()
    #logging.error("find hills")
    self.find_hills(ants)
    self.hill_time += time() - t

    t = time()
    #logging.error("find territory")
    self.find_new_territory(ants)
    self.new_time += time() - t

    t = time()
    self.unblock_hills(ants)
    self.unblock_time += time() - t

    t = time()
    #logging.error("drunk")
    self.wander_like_a_drunk(ants)
    self.wander_time += time() - t

    #logging.error("food: " + str(self.food_time))
    #logging.error("hills: " + str(self.hill_time))
    #logging.error("new: " + str(self.new_time))
    #logging.error("wander: " + str(self.wander_time))
    #logging.error("unblock: " + str(self.unblock_time))

    self.food_time = self.hill_time = self.new_time = self.wander_time = 0

if __name__ == '__main__':
  try:
    import psyco
    psyco.full()
  except ImportError:
    pass
  try:
    Ants.run(MyBot())
  except KeyboardInterrupt:
    print('ctrl-c, leaving ...')
