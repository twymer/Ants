from collections import namedtuple
from time import time
import logging
import heapq
from collections import deque

class Environment:
  def __init__(self):
    self.grid = []
    self.neighbors = {}
    self.rows = 0
    self.cols = 0

  # Used in ants library to check if there is an ant already there
  def unoccupied(self, position):
    return True

  # Determine if there is an obstacle blocking the way
  def passable(self, position):
    return self.grid[position[0]][position[1]] != "%"

  def load_map(self, file_name):
    self.grid = []
    f = open(file_name, 'r')
    for line in f:
      self.grid.append(list(line.strip()))
    f.close()

    self.rows = len(self.grid)
    self.cols = len(self.grid[0])

    directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
    for r in range(self.rows):
      for c in range(self.cols):
        self.neighbors[(r,c)] = [((r + d_row) % self.rows, (c + d_col) % self.cols)
          for (d_row, d_col) in directions]

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
      if current.depth > 30:
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

if __name__ == '__main__':
  e = Environment()

  # e.load_map("little_maze.txt")
  # print(s.find_path((20, 21), (6, 21), e))
  e.load_map("big_maze.txt")
  s = Search(e)
  # for i in range(e.cols()):
  #   for j in range(e.rows()):

  for i in range(20):
    for j in range(20):
      if e.passable((i,j)):
        def goal(node):
          return node == (i,j)
        s.bfs_path((2,2), goal)
  # print(s.find_path((2, 2), (47, 81), e))
