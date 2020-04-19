import deepmind_lab
import numpy as np
from collections import defaultdict
from scipy import ndimage
import matplotlib.pyplot as plt
import IPython.terminal.debugger as Debug


# actions in Deepmind
def _action(*entries):
    return np.array(entries, dtype=np.intc)


ACTION_LIST = [
        _action(-20, 0, 0, 0, 0, 0, 0),  # look_left
        _action(20, 0, 0, 0, 0, 0, 0),  # look_right
        _action(0, 0, 0, 1, 0, 0, 0),  # forward
        _action(0, 0, 0, -1, 0, 0, 0),  # backward
]


# valid observations
VALID_OBS = ['RGBD_INTERLEAVED',
             'RGB.LOOK_PANORAMA_VIEW',
             'RGB.LOOK_TOP_DOWN_VIEW',
             'DEBUG.POS.TRANS',
             'DEBUG.POS.ROT']


# Deepmind domain for random mazes with random start and goal positions
class RandomMaze(object):
    def __init__(self, level, observations, configs, reward_type='sparse-0', dist_epsilon=35):
        """
        Create gym-like domain interface
        :param level: name of the level (currently we only support one name "nav_random_nav")
        :param observations: list of observations [front view, panoramic view, top down view]
        :param configs: configuration of the lab [width, height, fps]
        """
        """ set up the 3D maze using default settings"""
        # set the level name
        self._level_name = level
        # set the level configuration
        self._level_configs = configs
        # check the validation of the observations
        assert set(observations) <= set(VALID_OBS), f"Observations contain invalid observations. Please check the " \
                                                    f"valid list here {VALID_OBS}."
        self._observation_names = observations + ['RGB.LOOK_RANDOM_VIEW', 'DEBUG.POS.TRANS', 'DEBUG.POS.ROT']
        # create the lab maze environment with default settings
        self._lab = deepmind_lab.Lab(self._level_name,
                                     self._observation_names,
                                     self._level_configs)

        """ observations from the maze """
        # current observations: contains all the required observations, since we only use a subset of it
        # (e.g. 8 observations). I call it "state"
        self._current_state = None
        # last observation
        self._last_observation = None
        # goal observation
        self._goal_observation = None
        # top down view for debugging or policy visualization
        self._top_down_obs = None
        # last distance
        self._last_distance = None
        # position info
        self._trans = None
        # orientation info
        self._rots = None

        """ configurable parameters for the maze"""
        # map name
        self.maze_name = "default_maze"
        # map size and seed (default: 5x5 maze with random seed set to be 1234)
        self.maze_size = [5, 5]
        self.maze_seed = 1234
        # maze map txt (default: 5x5 empty room)
        # note: "P" and "G" are necessary to generate the start agent and the goal.
        # Omitting the "G" will lead to no visual goal generated in the maze.
        self.maze_map_txt = "*****\n*P  *\n*   *\n*  G*\n*****"
        # maze texture name (default)
        self.maze_texture = "MISHMASH"
        # maze wall posters proportion (default)
        self.maze_decal_freq = "0.1"

        """ configurable parameters for the navigation"""
        # start and goal position w.r.t. rough map
        self.start_pos = [1, 1, 0]
        self.goal_pos = [3, 3, 0]
        # global orientations: [0, 45, 90, 135, 180, 225, 270, 315]
        self.orientations = np.arange(0, 360, 45)
        # reward configurations
        self.reward_type = reward_type
        # terminal conditions
        self.dist_epsilon = dist_epsilon

        # plotting objects
        self.fig, self.arrays = None, None
        self.img_artists = []

    # reset function
    def reset(self, configs):
        """
        Reset function based on configurations
        :param configs:
        :return:
        """
        """ Check configurations validation """
        assert type(configs) == defaultdict, f"Invalid configuration type. It should be collections.defaultdict, " \
                                             f"but get {type(configs)}"

        """ 3D maze configurations """
        """
            if configs['update'] is true, update the whole maze. 
                -- name
                -- size
                -- random seed
                -- texture
                -- decal posters on the wall
                -- maze layout in txt file
            
            if configs['update'] is false, the maze won't be update
            only the start and goal positions might be updated.
        """
        if configs['update']:
            # initialize the name
            self.maze_name = configs['maze_name'] if configs['maze_name'] else self.maze_name
            # initialize the size
            self.maze_size = configs['maze_size'] if configs['maze_size'] else self.maze_size
            # initialize the seed
            self.maze_seed = configs['maze_seed'] if configs['maze_seed'] else self.maze_seed
            # initialize the texture
            self.maze_texture = configs['maze_texture'] if configs['maze_texture'] else self.maze_texture
            # initialize the wall posters
            self.maze_decal_freq = configs['maze_decal_freq'] if configs['maze_decal_freq'] else self.maze_decal_freq
            # initialize the map
            self.maze_map_txt = configs['maze_map_txt'] if configs['maze_map_txt'] else self.maze_map_txt

            """ send the parameters to lua """
            # send the maze configurations
            self._lab.write_property("params.maze_configs.name", self.maze_name)
            self._lab.write_property("params.maze_configs.size", str(self.maze_size[0]))
            self._lab.write_property("params.maze_configs.seed", str(self.maze_seed))
            self._lab.write_property("params.maze_configs.texture", self.maze_texture)
            self._lab.write_property("params.maze_configs.decal_freq", str(self.maze_decal_freq))
            self._lab.write_property("params.maze_configs.map_txt", self.maze_map_txt)

        """ Navigation configurations"""
        """
            start amd goal positions will be updated if configs['start_pos'] and configs['goal_pos'] are not NONE.
        """
        # send initial position
        if configs['start_pos']:
            self.start_pos = configs['start_pos'] if configs['start_pos'] else self.start_pos
            self.start_pos = self.position_map2maze(self.start_pos, self.maze_size)
            self._lab.write_property("params.start_pos.x", str(self.start_pos[0]))
            self._lab.write_property("params.start_pos.y", str(self.start_pos[1]))
            self._lab.write_property("params.start_pos.yaw", str(self.start_pos[2]))
        # send target position
        if configs['goal_pos']:
            self.goal_pos = configs['goal_pos'] if configs['goal_pos'] else self.goal_pos
            self.goal_pos = self.position_map2maze(self.goal_pos, self.maze_size)
            self._lab.write_property("params.goal_pos.x", str(self.goal_pos[0]))
            self._lab.write_property("params.goal_pos.y", str(self.goal_pos[1]))
            self._lab.write_property("params.goal_pos.yaw", str(self.goal_pos[2]))
            # send the view position
            self._lab.write_property("params.view_pos.x", str(self.goal_pos[0]))
            self._lab.write_property("params.view_pos.y", str(self.goal_pos[1]))
            self._lab.write_property("params.view_pos.z", str(31.125))
            self._lab.write_property("params.view_pos.yaw", str(self.goal_pos[2]))

        """ update the environment """
        if configs['update']:
            self._lab.reset(episode=0)
        else:
            self._lab.reset()

        """ initialize the 3D maze"""
        # initialize the current state
        self._current_state = self._lab.observations()
        # initialize the current observations
        # By default, the observation for current state is the first observation
        self._last_observation = self._current_state[self._observation_names[0]]
        # initialize the top down view
        self._top_down_obs = self._current_state['RGB.LOOK_TOP_DOWN_VIEW']
        # initialize the goal observations
        self._goal_observation = self.get_random_observations(self.goal_pos)
        # initialize the positions and orientations
        self._trans = self._current_state['DEBUG.POS.TRANS']
        self._rots = self._current_state['DEBUG.POS.ROT']
        # initialize the distance
        self._last_distance = np.inf

        return self._last_observation, self._goal_observation, self._trans, self._rots

    # step function
    def step(self, action):
        """ step #(num_steps) in Deepmind Lab"""
        # take one step in the environment
        self._lab.step(ACTION_LIST[action], num_steps=4)

        """ check the terminal and return observations"""
        if self._lab.is_running():  # If the maze is still running
            # get the next state
            self._current_state = self._lab.observations()
            # get the next observations
            self._last_observation = self._current_state[self._observation_names[0]]
            # get the next top down observations
            self._top_down_obs = self._current_state['RGB.LOOK_TOP_DOWN_VIEW']
            # get the next position
            pos_x, pos_y, pos_z = self._current_state['DEBUG.POS.TRANS'].tolist()
            # get the next orientations
            pos_pitch, pos_yaw, pos_roll = self._current_state['DEBUG.POS.ROT'].tolist()
            # check if the agent reaches the goal given the current position and orientation
            terminal, dist = self.reach_goal([pos_x, pos_y, pos_yaw])
            # update the current distance between the agent and the goal
            self._last_distance = dist
            # update the rewards
            reward = self.compute_reward(dist)
            # update the positions and rotations
            self._trans = [pos_x, pos_y, pos_z]
            self._rots = [pos_pitch, pos_yaw, pos_roll]
        else:
            # set the terminal reward
            reward = 0.0
            # set the terminal flag
            terminal = True
            # set the current observation
            self._last_observation = np.copy(self._last_observation)
            # set the top down observation
            self._top_down_obs = np.copy(self._top_down_obs)
            # set the position and orientations
            self._trans = np.copy(self._trans)
            self._rots = np.copy(self._rots)
            # set the distance
            self._last_distance = self._last_distance

        return self._last_observation, reward, terminal, self._last_distance, self._trans, self._rots, dict()

    # render function
    def render(self, mode='rgb_array', close=False):
        if mode == 'rgb_array':
            return self._lab.observations()
        else:
            super(RandomMazeV1, self).render(mode=mode)  # just raise an exception

    # close the deepmind
    def close(self):
        self._lab.close()

    # seed function
    def seed(self, seed=None):
        self._lab.reset(seed=seed)

    # obtain goal image
    def get_random_observations(self, pos):
        """
        Function is used to get the observations at any position with any orientation.
        :param pos: List contains [x, y, ori]
        :return: List of egocentric observations at position (x, y)
        """
        # store observations
        ego_observations = []
        # re-arrange the observations of the agent
        ori_idx = list(self.orientations).index(pos[2])
        re_arranged_ori_indices = list(range(ori_idx, 8, 1)) + list(range(0, ori_idx, 1))
        angles = self.orientations[re_arranged_ori_indices]
        # obtain the egocentric observations
        self._lab.write_property("params.view_pos.x", str(pos[0] + 1))
        self._lab.write_property("params.view_pos.y", str(pos[1] + 1))
        for a in angles:
            self._lab.write_property("params.view_pos.yaw", str(a))
            ego_observations.append(self._lab.observations()['RGB.LOOK_RANDOM_VIEW'])
        return np.array(ego_observations, dtype=np.uint8)

    def reach_goal(self, current_pos):
        # compute the distance and angle error
        dist = self.compute_distance(current_pos, self.goal_pos)
        if dist < self.dist_epsilon:
            return 1, dist
        else:
            return 0, dist

    def compute_reward(self, dist):
        if self.reward_type == 'sparse-0':
            reward = 1 if dist < self.dist_epsilon else 0
        elif self.reward_type == 'sparse-1':
            reward = 0 if dist < self.dist_epsilon else -1
        elif self.reward_type == 'dense-euclidean':
            reward = dist
        else:
            raise Exception("Invalid reward type, Desired one in sparse-0, sparse-1, dense-euclidean but get {}"
                            .format(self.reward_type))
        return reward

    # show the panoramic view
    def show_panorama_view(self, time_step=None, obs_type='agent'):
        assert len(self._last_observation.shape) == 4, f"Invalid observation, expected observation should be " \
                                                       f"RGB.LOOK_PANORAMA_VIEW, but get {self._observation_names[0]}." \
                                                       f" Please check the observation list. The first one should be " \
                                                       f"RGB.LOOK_PANORAMA_VIEW."
        # set the observation: agent view or goal view
        if obs_type == 'agent':
            observations = self._last_observation
        else:
            observations = self._goal_observation
        # init or update data
        if time_step is None:
            self.fig, self.arrays = plt.subplots(3, 3)
            self.img_artists.append(self.arrays[0, 1].imshow(observations[0]))
            self.img_artists.append(self.arrays[0, 0].imshow(observations[1]))
            self.img_artists.append(self.arrays[1, 0].imshow(observations[2]))
            self.img_artists.append(self.arrays[1, 1].imshow(ndimage.rotate(self._top_down_obs, -90)))
            self.img_artists.append(self.arrays[2, 0].imshow(observations[3]))
            self.img_artists.append(self.arrays[2, 1].imshow(observations[4]))
            self.img_artists.append(self.arrays[2, 2].imshow(observations[5]))
            self.img_artists.append(self.arrays[1, 2].imshow(observations[6]))
            self.img_artists.append(self.arrays[0, 2].imshow(observations[7]))
        else:
            self.img_artists[0].set_data(observations[0])
            self.img_artists[1].set_data(observations[1])
            self.img_artists[2].set_data(observations[2])
            self.img_artists[3].set_data(ndimage.rotate(self._top_down_obs, -90))
            self.img_artists[4].set_data(observations[3])
            self.img_artists[5].set_data(observations[4])
            self.img_artists[6].set_data(observations[5])
            self.img_artists[7].set_data(observations[6])
            self.img_artists[8].set_data(observations[7])
        self.fig.canvas.draw()
        plt.pause(0.0001)

    # show the front view
    def show_front_view(self, time_step=None):
        assert len(self._last_observation.shape) == 3, f"Invalid observation, expected observation should be " \
                                                       f"RGBD_INTERLEAVED, but get {self._observation_names[0]}." \
                                                       f" Please check the observation list. The first one should be" \
                                                       f" RGBD_INTERLEAVED."
        # init or update data
        if time_step is None:
            self.fig, self.arrays = plt.subplots(1, 2)
            self.img_artists.append(self.arrays[0].imshow(self._last_observation))
            self.img_artists.append(self.arrays[1].imshow(ndimage.rotate(self._top_down_obs, -90)))
        else:
            self.img_artists[0].set_data(self._last_observation)
            self.img_artists[1].set_data(ndimage.rotate(self._top_down_obs, -90))
        self.fig.canvas.draw()
        plt.pause(0.0001)

    @staticmethod
    def compute_distance(pos_1, pos_2):
        return np.sqrt((pos_1[0] - pos_2[0])**2 + (pos_1[1] - pos_2[1])**2)

    @staticmethod
    def position_map2maze(pos, size):
        # convert the positions on the map to the positions in the 3D maze.
        # Note: the relation between the positions on the 2D map and the 3D maze is as follows:
        #      2D map: row, col
        #      3D maze: (y + 1 - 1) * 100 + 50, (maze_size - x) * 100 + 50
        return [pos[1] * 100 + 50, (size[1] - pos[0] - 1) * 100 + 50, pos[2]]