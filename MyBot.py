#!/usr/bin/env python
from random import shuffle
from ants import *
import logging

from time import time

class MyBot:
  # define class level variables, will be remembered between turns
  def __init__(self):
    self.move_list = {}

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
    else:
      return False

  def find_path(self, start, target, ants):
    # Source: http://theory.stanford.edu/~amitp/GameProgramming/Heuristics.html
    # TODO: This doesn't consider map wrap around
    def manhattan_distance(start, goal):
      d = 1 # movement cost
      return d * (abs(start[0] - goal[0]) + abs(start[1] - goal[1]))

    def neighbors(pos):
      directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
      return [((pos[0] + d_row) % ants.rows, (pos[1] + d_col) % ants.cols)
          for (d_row, d_col) in directions]

    def trace_path(node):
      #logging.error("start trace path")
      path = []
      current = node
      while current[PARENT] is not None:
        #logging.error("parent!")
        path.append(current[POS])
        current = current[PARENT]
      #logging.error("end trace path")
      #logging.error("returned path: " + str(path))
      return path

    def has_node(node_list, pos):
      #logging.error("*** has node ***")
      #logging.error("given[pos] " + str(pos))
      #logging.error("node_list[pos] " + str(node_list))
      return any(pos == node[POS] for node in node_list)
      #logging.error("val " + str(val))
      #logging.error("*** has node ***")

    # f = g + h
    POS, F, G, H, PARENT, NUM = range(6)

    open_list = []
    closed_list = []

    start_h = manhattan_distance(start, target)
    current = [start, start_h, 0, start_h, None, 0]
    open_list.append(current)
    while open_list:
      # Grab item with minimum F value
      current = min(open_list, key=lambda x:x[F])
      #logging.error("current[POS] " + str(current[POS]))
      #logging.error("target " + str(target))
      if current[POS] == target:
        #logging.error("****")
        #logging.error("****")
        #logging.error("start: " + str(start))
        return trace_path(current)
      open_list.remove(current)
      closed_list.append(current)
      for neighbor in neighbors(current[POS]):
        if ants.passable(neighbor) and not has_node(open_list, neighbor) and not has_node(closed_list, neighbor):
          new = [0,0,0,0,0,0]
          new[POS] = neighbor
          new[G] = current[G] + 1
          new[H] = manhattan_distance(new[POS], target)
          new[F] = new[G] + new[H]
          new[PARENT] = current
          new[NUM] = current[NUM] + 1
          open_list.append(new)
    # Making it through the loop means we explored all points reachable but
    # did not find our goal
    return None

  def find_food(self, ants):
    ant_dist = []
    for food_loc in ants.food():
      for ant_loc in ants.my_ants():
        dist = ants.distance(ant_loc, food_loc)
        ant_dist.append((dist, ant_loc, food_loc))
    ant_dist.sort()

    for dist, ant_loc, food_loc in ant_dist:
      if food_loc not in self.targets and ant_loc not in self.targets.values() and ant_loc not in self.move_list and food_loc not in self.move_list.values():
        dist, ant_loc, food_loc = ant_dist[0]
        #logging.error("***")
        path = self.find_path(ant_loc, food_loc, ants)
        if path:
          self.move_list[ant_loc] = path
        #logging.error("***")

  def find_hills(self, ants):
    for hill_loc, hill_owner in ants.enemy_hills():
      if hill_loc not in self.hills:
        self.hills.append(hill_loc)
    ant_dist = []
    for hill_loc in self.hills:
      for ant_loc in ants.my_ants():
        if ant_loc not in self.move_list:
          dist = ants.distance(ant_loc, hill_loc)
          ant_dist.append((dist, ant_loc))
    ant_dist.sort()

    for dist, ant_loc in ant_dist:
      path = self.find_path(ant_loc, hill_loc, ants)
      if path:
        self.move_list[ant_loc] = path

  def find_new(self, ants):
    for loc in self.unseen[:]:
      if ants.visible(loc):
        self.unseen.remove(loc)
    for ant_loc in ants.my_ants():
      #check
      unseen_dist = []
      for unseen_loc in self.unseen:
        dist = ants.distance(ant_loc, unseen_loc)
        unseen_dist.append((dist, unseen_loc))
      unseen_dist.sort()

      for dist, unseen_loc in unseen_dist:
        if unseen_loc not in self.move_list.values() and ant_loc not in self.move_list:
          path = self.find_path(ant_loc, unseen_loc, ants)
          if path:
            self.move_list[ant_loc] = path

  def do_turn(self, ants):
    self.orders = {}
    self.targets = {}

    # Do we need this?
    #for hill_loc in ants.my_hills():
    #  self.orders[hill_loc] = None

    self.find_food(ants)
    self.find_new(ants)

    #logging.error("targets: " + str(self.targets))
    #logging.error("move list post food" + str(self.move_list))

    new_move_list = {}
    for ant_loc, ant_moves in self.move_list.items():
      #logging.error("we be movin")
      #logging.error("ant_loc " + str(ant_loc))
      #logging.error("ant_moves " + str(ant_moves))
      next_move = ant_moves.pop()
      #logging.error("next move " + str(next_move))
      #logging.error("they be hatin")
      if self.do_move_location(ant_loc, next_move, ants):
        #logging.error("Moved ant " + str(ant_loc) + " to " + str(next_move))
        # This will become the global move list later
        # containing only successfully walked paths
        if len(ant_moves):
          new_move_list[next_move] = ant_moves
      #else:
      #  logging.error("move failed!")

    # TODO: If this gets large, will we need to not slam garbage collection
    # so hard?
    self.move_list = new_move_list

    #logging.error("End turn")

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
