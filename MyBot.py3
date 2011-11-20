#!/usr/bin/env python
from ants import *
import search

from random import shuffle

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
    self.unseen = set()
    for row in range(ants.rows):
      for col in range(ants.cols):
        self.unseen.add((row, col))

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
    for food_loc in ants.food():
      def goal_function(node):
        return node in self.my_ants and node not in self.orders
      self.my_ants = set(ants.my_ants())
      path, _, _ = self.search.bfs_path(food_loc, goal_function, self.next_turn_list)

      if path:
        first_move = path[1]
        ant_loc = path[0]
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
          self.unseen.add((row, col))

    # Remove currently visible territory
    for loc in self.unseen.copy():
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
        path = None
        if ant_loc in self.exploration_targets:
          logging.error("ant " + str(ant_loc) + " with goal " + str(self.exploration_targets[ant_loc]))
          if self.exploration_targets[ant_loc] in self.unseen:
            logging.error("Using previous path")
            path = self.search.find_path(ant_loc, self.exploration_targets[ant_loc], self.next_turn_list)
          else:
            del self.exploration_targets[ant_loc]
        if not path:
          logging.error("New BFS starting at " + str(ant_loc))
          self.game_timer.start("bfs time")
          path, open_nodes, closed_nodes = self.search.bfs_path(ant_loc, goal_check, self.next_turn_list)
          logging.error(self.game_timer.stop("bfs time"))

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

    self.search = search.Search(ants)

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
