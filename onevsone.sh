#!/usr/bin/env sh

# Random walk
# python ../ants_challenge/tools/playgame.py --player_seed 42 --end_wait=0.25 --verbose --log_dir game_logs --turns 1000 --map_file ../ants_challenge/tools/maps/random_walk/random_walk_02p_01.map "$@" "python ../ants_challenge/tools/sample_bots/python/GreedyBot.py" "python3.2 MyBot.py" --log_dir ../ants_challenge/game_logs -e -So | java -jar ../ants_challenge/tools/visualizer.jar

# Maze
python ../ants_challenge/tools/playgame.py --player_seed 42 --end_wait=0.25 --verbose --log_dir game_logs --turns 1000 --map_file ../ants_challenge/tools/maps/maze/maze_4.map "$@" "python ../ants_challenge/tools/sample_bots/python/GreedyBot.py" "python3.2 MyBot.py3" --log_dir ../ants_challenge/game_logs -e -So | java -jar ../ants_challenge/tools/visualizer.jar

# Multi maze
# python ../ants_challenge/tools/playgame.py --player_seed 42 --end_wait=0.25 --verbose --log_dir game_logs --turns 1000 --map_file ../ants_challenge/tools/maps/multi_hill_maze/multi_maze_01.map "$@" "python ../ants_challenge/tools/sample_bots/python/GreedyBot.py" "python3.2 MyBot.py" --log_dir ../ants_challenge/game_logs -e -So | java -jar ../ants_challenge/tools/visualizer.jar
