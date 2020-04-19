import random
import os
from envs.LabEnv import RandomMaze
from collections import defaultdict
import IPython.terminal.debugger as Debug


def sample_maze():
    # load all example maze names
    maze_names = os.listdir('./example/maps')
    # sample a maze
    name = random.sample(maze_names, 1)[0]
    with open('./example/maps/' + name, 'r') as f:
        lines = f.readlines()
        map_txt = [l for l in lines]
    # obtain the maze size
    size = int(name.split('_')[1])
    # obtain the valid positions
    valid_pos = []
    for i, l in enumerate(map_txt):
        for j, s in enumerate(l):
            if s == ' ' or s == 'P' or s == 'G':
                valid_pos.append([i, j])

    return name, size, map_txt, valid_pos


def print_maze_info(configs):
    print("Maze info: ")
    print("Maze name = ", configs["maze_name"])
    print("Maze size = ", configs["maze_size"])
    print("Maze seed = ", configs["maze_seed"])
    print("Maze texture = ", configs["maze_texture"])
    print("Maze decal freq = ", configs["maze_decal_freq"])
    print("Maze map txt = ", configs["maze_map_txt"])
    # initialize the maze start and goal positions
    print("Start pos = ", configs["start_pos"])
    print("Goal pos = ", configs["goal_pos"])
    print("Update flag = ", configs["update"])
    print('----------------------------')


def run_demo():
    # level name
    level = "nav_random_maze"

    # desired observations
    observation_list = ['RGBD_INTERLEAVED',
                        'RGB.LOOK_PANORAMA_VIEW',
                        'RGB.LOOK_TOP_DOWN_VIEW'
                        ]

    # configurations
    configurations = {
        'width': str(160),
        'height': str(160),
        "fps": str(60)
    }

    # maze theme and posters
    theme_list = ["TRON", "MINESWEEPER", "TETRIS", "GO", "PACMAN", "INVISIBLE_WALLS"]
    decal_list = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

    # mapper
    maze_name, maze_size, maze_map_txt, maze_valid_pos = sample_maze()

    # create the map environment
    myEnv = RandomMaze(level,
                       observation_list,
                       configurations)

    # initialize the maze environment
    maze_configs = defaultdict(lambda: None)
    maze_configs["maze_name"] = f"maze_{maze_size}x{maze_size}"  # string type name
    maze_configs["maze_size"] = [maze_size, maze_size]  # [int, int] list
    maze_configs["maze_seed"] = '1234'  # string type number
    maze_configs["maze_texture"] = random.sample(theme_list, 1)[0]  # string type name in theme_list
    maze_configs["maze_decal_freq"] = random.sample(decal_list, 1)[0]  # float number in decal_list
    maze_configs["maze_map_txt"] = "".join(maze_map_txt)  # string type map
    # initialize the maze start and goal positions
    maze_configs["start_pos"] = maze_valid_pos[0] + [0]  # start position on the txt map [rows, cols, orientation]
    maze_configs["goal_pos"] = maze_valid_pos[-1] + [0]  # goal position on the txt map [rows, cols, orientation]
    maze_configs["update"] = True  # update flag
    # set the maze
    print_maze_info(maze_configs)
    myEnv.reset(maze_configs)

    # # create observation windows
    # myEnv._last_observation = myEnv.get_random_observations(myEnv.position_map2maze([1, 3, 0], myEnv.maze_size))
    # myEnv.show_panorama_view()
    myEnv.show_front_view()

    # start test
    time_steps_num = 10000
    random.seed(maze_configs["maze_seed"])
    ep = 0
    pos_len = 1
    for t in range(time_steps_num):
        # sample an action
        act = random.sample(range(4), 1)[0]
        # agent takes the action
        myEnv.step(act)

        # for a random maze view
        # myEnv._last_observation = myEnv.get_random_observations(myEnv.position_map2maze([1, 3, 0], myEnv.maze_size))
        # for the panorama view
        # myEnv.show_panorama_view(t)
        # for the front view
        myEnv.show_front_view(t)

        # test episode length is 20
        if t % 20 == 0:
            ep += 1
            # reset the whole maze after 10 episodes
            if ep % 10 == 0:
                # randomly sample a maze
                maze_name, maze_size, maze_map_txt, maze_valid_pos = sample_maze()
                # set the new maze params
                maze_configs["maze_name"] = f"maze_{maze_size}x{maze_size}"
                maze_configs["maze_size"] = [maze_size, maze_size]
                maze_configs["maze_seed"] = '1234'
                maze_configs["maze_map_txt"] = "".join(maze_map_txt)
                maze_configs["start_pos"] = maze_valid_pos[0] + [0]
                maze_configs["goal_pos"] = maze_valid_pos[-1] + [0]
                maze_configs["maze_decal_freq"] = random.sample(decal_list, 1)[0]
                maze_configs["maze_texture"] = random.sample(theme_list, 1)[0]
                maze_configs["update"] = True
                print_maze_info(maze_configs)
                # set the maze
                myEnv.reset(maze_configs)
                pos_len = 1
            else:  # for a fixed maze, sequentially set the start along the valid positions on the map
                # e.g. 5x5 maze txt
                #    ---------> cols
                #    | * * * * *
                #    | * P     *
                #    | *   * * *
                #    | *     G *
                #    | * * * * *
                #   rows
                #     P = (1, 1)
                #     G = (3, 3)
                #    type = [rows, cols, orientation]
                #    start_pos = (1, 1, 0)
                #    goal_pos = (3, 3, 0)
                #   where 0 is the orientation in [0, 360]
                maze_configs["start_pos"] = maze_valid_pos[pos_len] + [0]
                pos_len = pos_len + 1 if pos_len + 1 < len(maze_valid_pos) else len(maze_valid_pos) - 1
                maze_configs["goal_pos"] = maze_valid_pos[-1] + [0]
                maze_configs["update"] = False
                print("Ep = {}, Start = {}, Goal = {}".format(ep, maze_configs['start_pos'], maze_configs['goal_pos']))
                myEnv.reset(maze_configs)


if __name__ == '__main__':
    run_demo()


