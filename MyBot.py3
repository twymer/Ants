#!/usr/bin/env python
from random import shuffle
from ants import *
from collections import namedtuple
import logging
import heapq

from time import time

MY_ANT = 0

# version 0.1.2
class Search:
  def __init__(self, env):
    self.environment = env
    self.N = self.environment.rows
    self.M = self.environment.cols

  def manhattan_distance(self, start, goal):
    d = 1
    s0 = start[0]
    g0 = goal[0]
    # TODO: Remove this before end of contest
    # Or investigate using an assert and python -O on server to stop the check
    if s0 >= self.N or g0 >= self.N:
      raise ValueError("Row value out of bounds")
    if s0 > g0:
      g0, s0 = s0, g0

    s1 = start[1]
    g1 = goal[1]
    # TODO: Remove this before end of contest
    if s1 >= self.M or g1 >= self.M:
      raise ValueError("Column value out of bounds")
    if s1 > g1:
      g1, s1 = s1, g1

    return d * (min((g0 - s0, s0 + self.N - g0)) + min((g1 - s1, s1 + self.M - g1)))

  def visualize_path(self, start, goal):
    path, open_list, closed_list = self.path_data(start, goal)
    if not path:
      return
    # Copy each line individually so we don't screw up grid
    g = [list(line) for line in self.environment.grid]
    for loc in open_list:
      g[loc[0]][loc[1]] = 'o'
    for loc in closed_list:
      g[loc[0]][loc[1]] = 'o'
    for loc in path:
      g[loc[0]][loc[1]] = 'x'
    for row in g:
      print(*row, sep='')

  def find_path(self, start_position, goal_position, next_turn_list = []):
    path, _, _ = self.calc_path(start_position, goal_position, next_turn_list)
    return path

  def path_data(self, start_position, goal_position):
    return self.calc_path(start_position, goal_position, [])

  def calc_path(self, start_position, goal_position, next_turn_list):
    if (not self.environment.passable(goal_position) or
        not self.environment.passable(goal_position)):
      return None, None, None
    Node = namedtuple('Node', 'position f g h parent depth')
    #logging.error("find_path")

    def trace_path(final_node, open_nodes, closed_nodes):
      t = time()
      path = []
      current = final_node
      while current.parent is not None:
        path.append(current.position)
        current = current.parent

      # self.tracing_time += time() - t
      return path, open_nodes, closed_nodes

    open_nodes = {}
    open_nodes_heap = []
    closed_nodes = {}
    open_heap = []

    start_h = self.manhattan_distance(start_position, goal_position)
    current = Node(start_position, start_h, 0, start_h, None, 0)
    open_nodes[current.position] = current
    heapq.heappush(open_nodes_heap, (current.f, current))
    while open_nodes:
      # Grab item with minimum F value
      _, current = heapq.heappop(open_nodes_heap)
      del open_nodes[current.position]
      #current = min(open_nodes.values(), key=lambda x:x.f)
      if current.position == goal_position:
        # logging.error("steps to find path: " + str(current.depth))
        return trace_path(current, open_nodes, closed_nodes)
      closed_nodes[current.position] = current
      for neighbor in self.environment.neighbors[current.position]:
        if (neighbor not in open_nodes and # and not open
            neighbor not in closed_nodes and # or closed
            (current.depth > 0 or neighbor not in next_turn_list) and # if occupied and next to start
            self.environment.passable(neighbor)): # if occupied and next to start
          new_g = current.g + 1
          new_h = self.manhattan_distance(neighbor, goal_position)
          new = Node(
            neighbor,
            new_g + new_h,
            new_g,
            new_h,
            current,
            current.depth + 1)
          open_nodes[new.position] = new
          heapq.heappush(open_nodes_heap, (new.f, new))
      # If first item has no neighbors, ant is trapped, put a noop on his move list
      if current.depth == 0 and len(open_nodes) == 0:
        return [current.position], None, None

    # Making it through the loop means we explored all points reachable but
    # did not find our goal
    return None, None, None

class MyBot:
  # define class level variables, will be remembered between turns
  def __init__(self):
    self.enemy_hills = set()
    self.initialize_timing()

  def initialize_global_timing(self):
    pass
    # self.inner_unseen_time = 0
    # self.unseen_pathing_time = 0
    # self.global_pathing_time = 0
    # self.global_tracing_time = 0

  def initialize_timing(self):
    self.inner_unseen_time = 0
    self.unseen_pathing_time = 0
    self.unseen_time = 0
    self.find_food_time = 0

  def do_setup(self, ants):
    self.hills = []

    # TODO: Store last time a location was seen
    # so that we don't ever run out of territory to search
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
        # self.targets[dest] = loc
        return True
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
      if food_loc not in self.targets and ant_loc not in self.orders:
        path = self.search.find_path(ant_loc, food_loc, self.next_turn_list)
        if path:
          first_move = path.pop()
        else:
          continue
        logging.error("food from: " + str(ant_loc) + " to " + str(first_move))
        if first_move not in self.next_turn_list:
          self.do_move_location(ant_loc, first_move, ants)
          self.orders[ant_loc] = food_loc
          self.next_turn_list.add(first_move)
          self.targets.add(food_loc)

  def find_hills(self, ants):
    for hill, owner in self.enemy_hills.copy():
      # If we can see a hill but it's not in the enemy hills list,
      # that means we have destroyed it
      logging.error("enemy hills: " + str(ants.enemy_hills()))
      logging.error("hill: " + str(hill))
# hill_loc in x for x in self.move_list.values()
      if ants.visible(hill) and not any(hill == x[0] for x in ants.enemy_hills()):
        logging.error("*** REMOVE HILL ***")
        self.enemy_hills.remove((hill, owner))

    self.enemy_hills = self.enemy_hills.union(ants.enemy_hills())

    # TODO: unchecked
    for hill_loc, hill_owner in self.enemy_hills:
      if hill_loc not in self.hills:
        self.hills.append(hill_loc)
    ant_dist = []
    for hill_loc in self.hills:
      for ant_loc in ants.my_ants():
        if ant_loc not in self.orders:
          dist = ants.distance(ant_loc, hill_loc)
          ant_dist.append((dist, ant_loc, hill_loc))
    ant_dist.sort()

    # self.orders = {}
    # self.next_turn_list = set()
    # self.targets = set()
    for dist, ant_loc, hill_loc in ant_dist:
      if ant_loc not in self.orders and hill_loc not in self.targets:
        path = self.search.find_path(ant_loc, hill_loc, self.next_turn_list)
        if path:
          first_move = path.pop()
        else:
          continue
        logging.error("hill from: " + str(ant_loc) + " to " + str(first_move))
        if first_move not in self.next_turn_list:
          self.do_move_location(ant_loc, first_move, ants)
          self.orders[ant_loc] = hill_loc
          self.next_turn_list.add(first_move)
          self.targets.add(hill_loc)

  def find_new(self, ants):
    logging.error("Unseen size: " + str(len(self.unseen)))
    # Reset list now that it's empty..
    if len(self.unseen) == 0:
      logging.error("Unseen list reset!")
      for row in range(ants.rows):
        for col in range(ants.cols):
          self.unseen.append((row, col))

    # Remove currently visible territory
    for loc in self.unseen[:]:
      if ants.visible(loc):
        logging.error("Remove: " + str(loc))
        self.unseen.remove(loc)

    for ant_loc in ants.my_ants():
      logging.error("ant_loc: " + str(ant_loc))
      logging.error("ant_loc in unseen?: " + str(ant_loc in self.unseen))
      if ant_loc in self.orders:
        continue

      inner_t = ants.time_remaining()
      unseen_dist_heap = []
      for unseen_loc in self.unseen:
        if unseen_loc == ant_loc:
          continue
        if len(unseen_dist_heap) > 2000:
          logging.error("stop .. " + str(len(self.unseen)))
          break
        if unseen_loc in self.targets:
          continue
        dist = self.search.manhattan_distance(ant_loc, unseen_loc)
        # unseen_dist.append((dist, unseen_loc))
        heapq.heappush(unseen_dist_heap, (dist, unseen_loc))
      logging.error("find and sort distances took " + str(inner_t - ants.time_remaining()))
      self.inner_unseen_time += inner_t - ants.time_remaining()


      # for dist, unseen_loc in unseen_dist:
      while unseen_dist_heap:
        dist, unseen_loc = heapq.heappop(unseen_dist_heap)
        if unseen_loc not in self.targets and ant_loc not in self.orders:
          # TODO: this code isn't very DRY
          if not self.enough_time_to_path(ants):
            return
          path = self.search.find_path(ant_loc, unseen_loc, self.next_turn_list)
          if path:
            first_move = path.pop()
          else:
            logging.error("no path from " + str(unseen_loc) + " to " + str(unseen_loc))
            continue
          logging.error("new from: " + str(ant_loc) + " to " + str(first_move))
          if first_move not in self.next_turn_list:
            self.do_move_location(ant_loc, first_move, ants)
            self.orders[ant_loc] = unseen_loc
            self.next_turn_list.add(first_move)
            self.targets.add(unseen_loc)
            break
          else:
            logging.error("first move taken")


  def enough_time(self, ants):
    allowable_time_percent = 30
    if ants.time_remaining() / ants.turntime > allowable_time_percent / 100:
      return True
    else:
      logging.error("***")
      logging.error("***")
      logging.error("***")
      logging.error("OUT OF TIME!")
      logging.error("***")
      logging.error("***")
      logging.error("***")
      return False

  def enough_time_to_path(self,ants):
    logging.error("time remaining: " + str(ants.time_remaining() / ants.turntime))
    allowable_time_percent = 10
    if ants.time_remaining() / ants.turntime > allowable_time_percent / 100:
      return True
    else:
      logging.error("***")
      logging.error("OUT OF TIME TO PATH!")
      logging.error("***")

  def do_turn(self, ants):
    logging.error("*****")
    logging.error("Start turn")
    logging.error("*****")

    self.initialize_timing()
    t = time()

    self.search = Search(ants)

    self.orders = {}
    self.next_turn_list = set()
    self.targets = set()

    # Do we need this?
    #for hill_loc in ants.my_hills():
    #  self.orders[hill_loc] = None
    #logging.error("move list start turn" + str(self.move_list))

    tt1 = ants.time_remaining()
    if self.enough_time(ants):
      self.find_food(ants)
    tt1 -= ants.time_remaining()

    tt2 = ants.time_remaining()
    if self.enough_time(ants):
      self.find_hills(ants)
    tt2 -= ants.time_remaining()

    tt3 = ants.time_remaining()
    if self.enough_time(ants):
      self.find_new(ants)
    tt3 -= ants.time_remaining()

    logging.error("food time: " + str(tt1))
    logging.error("hills time: " + str(tt2))
    logging.error("explore time: " + str(tt3))

    logging.error("*****")
    logging.error("End turn")
    logging.error("Took " + str(ants.turntime - ants.time_remaining()) + " of total " + str(ants.turntime))
    logging.error("inner unseen time: " + str(self.inner_unseen_time))
    self.initialize_timing()
    logging.error("*****")

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
