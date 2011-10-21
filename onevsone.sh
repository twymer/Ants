#!/usr/bin/env sh
python ../ants_challenge/tools/playgame.py --player_seed 42 --end_wait=0.25 --verbose --log_dir game_logs --turns 1000 --map_file ../ants_challenge/tools/maps/maze/maze_1.map "$@" "python ../ants_challenge/tools/sample_bots/python/GreedyBot.py" "python3.2 MyBot.py" -So | java -jar ../ants_challenge/tools/visualizer.jar
