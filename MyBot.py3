#!/usr/bin/env python
from ants import *

from random import shuffle

from collections import namedtuple
from collections import deque

import heapq

import logging
from time import time

MY_ANT = 0

class GameTimer():
  def __init__(self, ants):
    self.timers = {}
    self.ants = ants

  def start(self, name):
    self.timers[name] = self.ants.time_remaining()

  def stop(self, name):
    if name in self.timers:
      return name + " timer: " + str(self.timers[name] - self.ants.time_remaining())
      del self.timers[name]

# version 0.2.2
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

  def print_grid(self, path, closed_list = [], open_list = []):
    # Copy each line individually so we don't screw up grid
    g = [list(line) for line in self.environment.grid]
    for loc in open_list:
      g[loc[0]][loc[1]] = '_'
    for loc in closed_list:
      g[loc[0]][loc[1]] = '_'
    for loc in path:
      g[loc[0]][loc[1]] = 'X'
    for row in g:
      print(*row, sep='')

  def visualize_path(self, start, goal):
    path, open_list, closed_list = self.path_data(start, goal)
    if not path:
      return
    self.print_grid(path, open_list, closed_list)

  def visualize_bfs(self, start, goal_function):
    path, open_list, closed_list = self.bfs_path(start, goal_function)
    if not path:
      return
    self.print_grid(path, open_list, closed_list)

  def find_path(self, start_position, goal_position, next_turn_list = []):
    path, _, _ = self.calc_path(start_position, goal_position, next_turn_list)
    return path

  def path_data(self, start_position, goal_position):
    return self.calc_path(start_position, goal_position, [])

  def trace_path(self, final_node, open_nodes, closed_nodes):
    path = []
    current = final_node
    while current.parent:
      path.append(current.position)
      current = current.parent

    return path, open_nodes, closed_nodes

  def bfs_path(self, start_position, goal_function, next_turn_list = [], target_list = []):
    if (not self.environment.passable(start_position)):
      return None, None, None
    Node = namedtuple('Node', 'position parent depth')

    open_queue = deque()
    #TODO: these could probably just be sets this time around
    open_nodes = {}
    closed_nodes = {}
    current = Node(start_position, None, 0)
    open_queue.append(current)
    open_nodes[current.position] = current
    while open_queue:
      current = open_queue.popleft()
      if not self.environment.enough_time_to_path():
        return self.trace_path(current, open_nodes, closed_nodes)
      del open_nodes[current.position]
      closed_nodes[current.position] = (current)
      if goal_function(current.position):
        return self.trace_path(current, open_nodes, closed_nodes)
      for neighbor in self.environment.neighbors[current.position]:
        if (neighbor not in open_nodes and
            neighbor not in closed_nodes and
            (current.depth > 0 or neighbor not in next_turn_list) and
            self.environment.passable(neighbor)):
          new_node = Node(neighbor, current, current.depth + 1)
          open_queue.append(new_node)
          open_nodes[new_node.position] = new_node
    return None, None, None

  def calc_path(self, start_position, goal_position, next_turn_list):
    if (not self.environment.passable(start_position) or
        not self.environment.passable(goal_position)):
      return None, None, None
    Node = namedtuple('Node', 'position f g h parent depth')

    open_nodes = {}
    open_nodes_heap = []
    closed_nodes = {}

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
        return self.trace_path(current, open_nodes, closed_nodes)
      closed_nodes[current.position] = current
      for neighbor in self.environment.neighbors[current.position]:
        if (neighbor not in open_nodes and
            neighbor not in closed_nodes and
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

    self.exploration_targets = {}

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
        # logging.error("food from: " + str(ant_loc) + " to " + str(first_move))
        if first_move not in self.next_turn_list:
          self.do_move_location(ant_loc, first_move, ants)
          self.orders[ant_loc] = food_loc
          self.next_turn_list.add(first_move)
          self.targets.add(food_loc)

  def find_hills(self, ants):
    for hill, owner in self.enemy_hills.copy():
      # If we can see a hill but it's not in the enemy hills list,
      # that means we have destroyed it
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
        # logging.error("Remove: " + str(loc))
        self.unseen.remove(loc)

    def goal_check(test_loc):
      return test_loc in self.unseen and test_loc not in self.targets

    new_exploration_targets = {}
    logging.error("explore: " + str(self.exploration_targets.keys()))
    for ant_loc in ants.my_ants():
      if not ants.enough_time_to_path():
        return
      if ant_loc not in self.orders:
        if ant_loc in self.exploration_targets:
          logging.error("ant " + str(ant_loc) + " with goal " + str(self.exploration_targets[ant_loc]))
          if self.exploration_targets[ant_loc] in self.unseen:
            logging.error("Using previous path")
            path = self.search.find_path(ant_loc, self.exploration_targets[ant_loc], self.next_turn_list)
            continue
          else: 
            logging.error("not in unseen")
        logging.error("New BFS starting at " + str(ant_loc))
        path, _, _ = self.search.bfs_path(ant_loc, goal_check, self.next_turn_list)

        if path:
          first_move = path.pop()
        else:
          continue

        if first_move not in self.next_turn_list:
          self.do_move_location(ant_loc, first_move, ants)
          self.orders[ant_loc] = path[0]
          self.next_turn_list.add(first_move)
          self.targets.add(path[0])
          new_exploration_targets[first_move] = path[0]

    self.exploration_targets = new_exploration_targets

  def do_turn(self, ants):
    logging.error("*****")
    logging.error("Start turn")
    logging.error("*****")

    # self.initialize_timing()
    self.game_timer = GameTimer(ants)

    self.search = Search(ants)

    self.orders = {}
    self.next_turn_list = set()
    self.targets = set()

    # Do we need this?
    #for hill_loc in ants.my_hills():
    #  self.orders[hill_loc] = None
    #logging.error("move list start turn" + str(self.move_list))

    self.game_timer.start("food time")
    if ants.enough_time():
      self.find_food(ants)
    tt1 = self.game_timer.stop("food time")

    self.game_timer.start("hills time")
    if ants.enough_time():
      self.find_hills(ants)
    tt2 = self.game_timer.stop("hills time")

    self.game_timer.start("new time")
    if ants.enough_time():
      self.find_new(ants)
    tt3 = self.game_timer.stop("new time")

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
