#!/usr/bin/env python
from ants import *
import search

import heapq
from collections import deque
from math import sqrt

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
        return True
    else:
      return False

  def find_food(self, ants):
    def goal_function(node):
      return node in self.my_ants and node not in self.orders
    for food_loc in ants.food():
      if not ants.enough_time_to_path():
        return

      self.my_ants = set(ants.my_ants())
      path, _, _ = self.search.bfs_path(food_loc,
                                        goal_function,
                                        self.next_turn_list)
      if path:
        first_move = None
        if len(path) > 1:
          first_move = path[1]
        else:
          first_move = food_loc
        ant_loc = path[0]
        self.do_move_location(ant_loc, first_move, ants)
        self.orders[ant_loc] = food_loc
        self.next_turn_list.add(first_move)
        self.targets.add(food_loc)

  def find_hills(self, ants):
    for hill in self.enemy_hills.copy():
      # If we can see a hill but it's not in the enemy hills list,
      # that means we have destroyed it
      if ants.visible(hill) and not hill in ants.enemy_hills_locs():
        logging.error("*** REMOVE HILL ***")
        self.enemy_hills.remove(hill)

    self.enemy_hills |= ants.enemy_hills_locs()

    def goal_function(node):
      return node in self.my_ants and node not in self.orders
    for hill in self.enemy_hills:
      if not ants.enough_time_to_path():
        return

      self.my_ants = set(ants.my_ants())
      path, _, _ = self.search.bfs_path(hill,
                                        goal_function,
                                        self.next_turn_list)
      if path:
        first_move = None
        if len(path) > 1:
          first_move = path[1]
        else:
          first_move = hill
        ant_loc = path[0]
        self.do_move_location(ant_loc, first_move, ants)
        self.orders[ant_loc] = hill
        self.next_turn_list.add(first_move)
        self.targets.add(hill)

  def find_new(self, ants):
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

    def goal_function(test_loc):
      return test_loc in self.unseen and test_loc not in self.targets

    for ant_loc in ants.my_ants():
      if not ants.enough_time_to_path():
        return

      if ant_loc not in self.orders:
        path, _, _ = self.search.bfs_path(ant_loc,
                                          goal_function,
                                          self.next_turn_list)
        if path:
          first_move = path.pop()
        else:
          continue

        if first_move not in self.next_turn_list:
          self.do_move_location(ant_loc, first_move, ants)
          self.orders[ant_loc] = path[0]
          self.next_turn_list.add(first_move)
          self.targets.add(path[0])

  def do_combat(self, ants):
    # TODO: Notes:
    # Does not account for ants on both sides of attack radius
    attack_radius2 = ants.attackradius2

    my_ants = ants.my_ants()
    enemy_ants = ants.enemy_ants_locs()
    for my_ant in my_ants:
      if my_ant in self.orders:
        continue
      opponents = []
      for enemy_ant in enemy_ants:
        if (ants.distance_formula(my_ant, enemy_ant) <
            sqrt(attack_radius2) + 1):
          opponents.append(enemy_ant)
      friends = [my_ant]
      if opponents:
        for friendly_ant in my_ants:
          if (ants.distance_formula(friendly_ant, enemy_ant) <
              sqrt(attack_radius2) + 1):
            friends.append(friendly_ant)

        logging.error(str(len(friends)) + " vs " + str(len(opponents)))
        if len(friends) > len(opponents):
          for friend in friends:
            # TODO: path find instead
            # TODO: move to center point?
            self.do_move_location(friend, opponents[0], ants)
            # TODO:
            # self.next_turn_list.add(first_move)
        else:
          for friend in friends:
            direction = ants.direction(friend, opponents[0])[0]
            directions = { 'n':'s', 'e':'w', 'w':'e', 's':'n' }
            self.do_move_direction(friend, directions[direction], ants)


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

    self.game_timer.start("combat time")
    self.do_combat(ants)
    tt0 = self.game_timer.stop("combat time")

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
