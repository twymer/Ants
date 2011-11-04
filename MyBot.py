#!/usr/bin/env python
from random import shuffle
from ants import *
from collections import namedtuple
import logging

from time import time

class MyBot:
  # define class level variables, will be remembered between turns
  def __init__(self):
    self.move_list = {}
    self.initialize_global_timing()

  def initialize_global_timing(self):
    self.global_pathing_time = 0
    self.global_tracing_time = 0

  def initialize_timing(self):
    self.pathing_time = 0
    self.tracing_time = 0
    self.find_new_time = 0

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

  def find_path(self, start_position, goal_position, ants):
    Node = namedtuple('Node', 'position f g h parent depth')
    #logging.error("find_path")

    # TODO: This doesn't consider map wrap around
    # Source: http://theory.stanford.edu/~amitp/GameProgramming/Heuristics.html
    def manhattan_distance(start, goal):
      d = 4 # movement cost
      return d * (abs(start[0] - goal[0]) + abs(start[1] - goal[1]))

    def neighbors(pos):
      directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
      return [((pos[0] + d_row) % ants.rows, (pos[1] + d_col) % ants.cols)
          for (d_row, d_col) in directions]

    def trace_path(final_node):
      #logging.error("start trace path")
      t = time()
      path = []
      current = final_node
      while current.parent is not None:
        path.append(current.position)
        current = current.parent
      #logging.error("end trace path")

      self.tracing_time += time() - t
      return path

    def has_node_with_position(node_list, position):
      return any(position == node.position for node in node_list)

    #logging.error("passable start? " + str(ants.passable(start)))
    #logging.error("passable goal? " + str(ants.passable(target)))

    open_set = set()
    closed_set = set()

    start_h = manhattan_distance(start_position, goal_position)
    current = Node(start_position, start_h, 0, start_h, None, 0)
    open_set.add(current)
    while open_set:
      # Grab item with minimum F value
      current = min(open_set, key=lambda x:x.f)
      #logging.error("current.position " + str(current.position))
      #logging.error("goal " + str(goal))
      if current.position == goal_position:
        #logging.error("start: " + str(start))
        #logging.error("****")
        logging.error("steps to find path: " + str(current.depth))
        #logging.error("****")
        return trace_path(current)
      open_set.remove(current)
      closed_set.add(current)
      for neighbor in neighbors(current.position):
        #logging.error("  in open? " + str(has_node(open_list, neighbor)))
        #logging.error("  in closed? " + str(has_node(closed_list, neighbor)))
        #logging.error("  is passable? " + str(ants.passable(neighbor)))
        if ants.passable(neighbor) and not has_node_with_position(open_set, neighbor) and not has_node_with_position(closed_set, neighbor):
          new_g = current.g + 1
          new_h = manhattan_distance(neighbor, goal_position)
          new = Node(
            neighbor,
            new_g,
            new_h,
            new_g + new_h,
            current,
            current.depth + 1)
          #logging.error("  neighbor " + str(neighbor))
          #logging.error("  how far in? " + str(current[NUM]))
          #logging.error("  g? " + str(current[G]))
          #logging.error("  h? " + str(current[H]))
          #logging.error("  f=g+h? " + str(current[F]))
          open_set.add(new)
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

    #logging.error("ant_dist: " + str(ant_dist))

    for dist, ant_loc, food_loc in ant_dist:
      if food_loc not in self.targets and ant_loc not in self.targets.values() and ant_loc not in self.move_list and not any(food_loc in x for x in self.move_list.values()):
        logging.error("Find food path from " + str(ant_loc) + " to " + str(food_loc))
        t = time()
        path = self.find_path(ant_loc, food_loc, ants)
        #logging.error("path time: " + str(time() - t))
        if path:
          #logging.error("path found!")
          self.move_list[ant_loc] = path
        else:
          # Go ahead and add the ant with no path to move list... this usually
          # means a game bug and we don't want to go crazy trying to path him
          # TODO: fix this..
          self.move_list[ant_loc] = None

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
      if ant_loc not in self.move_list:
        logging.error("Find hills path")
        t = time()
        path = self.find_path(ant_loc, hill_loc, ants)
        self.pathing_time += time() - t
        logging.error("path time: " + str(time() - t))
        if path:
          self.move_list[ant_loc] = path
        else:
          # Go ahead and add the ant with no path to move list... this usually
          # means a game bug and we don't want to go crazy trying to path him
          # TODO: fix this..
          self.move_list[ant_loc] = None

  def find_new(self, ants):
    time_start = time()
    path_time_start = self.pathing_time

    for loc in self.unseen[:]:
      if ants.visible(loc):
        self.unseen.remove(loc)

    for ant_loc in ants.my_ants():
      if ant_loc in self.move_list:
        continue

      #check
      unseen_dist = []
      for unseen_loc in self.unseen:
        dist = ants.distance(ant_loc, unseen_loc)
        unseen_dist.append((dist, unseen_loc))
      unseen_dist.sort()

      for dist, unseen_loc in unseen_dist:
        if self.move_list and ant_loc not in self.move_list and not any(unseen_loc in x for x in self.move_list.values()):
          logging.error("Find territory path from " + str(ant_loc) + " to " + str(unseen_loc))
          t = time()
          path = self.find_path(ant_loc, unseen_loc, ants)
          self.pathing_time += time() - t
          logging.error("path time: " + str(time() - t))
          if path:
            #logging.error("added to move list")
            self.move_list[ant_loc] = path
          else:
            # Go ahead and add the ant with no path to move list... this usually
            # means a game bug and we don't want to go crazy trying to path him
            # TODO: fix this..
            self.move_list[ant_loc] = None
    self.find_new_time += time() - time_start - self.pathing_time - path_time_start

  def do_turn(self, ants):
    self.initialize_timing()
    t = time()
    self.orders = {}
    self.targets = {}
    #logging.error("*****")
    #logging.error("*****")
    #logging.error("*****")
    logging.error("*****")
    logging.error("Start turn")
    logging.error("*****")

    # Do we need this?
    #for hill_loc in ants.my_hills():
    #  self.orders[hill_loc] = None
    #logging.error("move list start turn" + str(self.move_list))

    self.find_food(ants)
    self.find_new(ants)
    self.find_hills(ants)

    #logging.error("targets: " + str(self.targets))

    new_move_list = {}
    for ant_loc, ant_moves in self.move_list.items():
      if ant_moves:
        next_move = ant_moves.pop()
      else:
        break
      if self.do_move_location(ant_loc, next_move, ants):
        # This will become the global move list later
        # containing only successfully walked paths
        if len(ant_moves):
          new_move_list[next_move] = ant_moves
      else:
        logging.error("move failed! " + str(ant_loc) + " to " + str(next_move))

    # TODO: If this gets large, will we need to not slam garbage collection
    # so hard?
    self.move_list = new_move_list

    logging.error("*****")
    logging.error("*****")
    self.global_pathing_time += self.pathing_time - self.tracing_time
    logging.error("turns pathing time: " + str(self.pathing_time - self.tracing_time))
    logging.error("global pathing time: " + str(self.global_pathing_time))

    self.global_tracing_time += self.tracing_time
    logging.error("turns tracing time: " + str(self.tracing_time))
    logging.error("global tracing time: " + str(self.global_tracing_time))
    logging.error("*****")
    logging.error("*****")
    logging.error("non pathing time: " + str(time() - t - self.pathing_time))
    logging.error("find new time: " + str(self.find_new_time))
    logging.error("End turn")

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
