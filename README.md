# dmlab_random_maze
## Introduction
This project provides the codes for a customized version of Deepmind 3D maze domain. In this version, you can
construct 3D maze using external txt files. By passing designed parameters from python to lua, you can customize
the 3D maze.
## Installation
* Clone this project.
* Clone and install the Deepmind Lab by following the instructions [here](https://github.com/deepmind/lab).
* Copy the `nav_random_maze.lua` file in lua in to the `lab\game_scripts\levels\` in Deepmind Lab.
* Wrap the Deepmind into a PIP package by following the instructions [here](https://github.com/deepmind/lab/blob/master/python/pip_package/README.md).
* Create a virtual environment using conda and install the Deepmind PIP package.
## Extra Dependencies
* numpy
* scipy
* matplotlib
* ipython
## Test
After the installation, you can test the environment using the following command under the repo root directory:
```
python dmlab_demo.py
```
## Customized variables
We follow the strategy of passing the customized variables from python to lua file. In the python api. we define
the following customized variables.

First of all, we define the variables related to the maze appearance.
* params.maze_configs.name (str): name of the 3D maze
* params.maze_configs.size (str): size of the 3D maze (size x size)
* params.maze_configs.seed (str): random seed of the 3D maze
* params.maze_configs.texture (str): texture\theme of the 3D maze
* params.maze_configs.decal_freq (str): rate of posters on the wall
* params.maze_configs.map_txt (str): txt map of the 3D maze

Then, we define the variables related to start and goal positions.
* params.start_pos.x (str): x
* params.start_pos.y (str): y
* params.start_pos.yaw (str): orientation 
* params.goal_pos.x (str): x
* params.goal_pos.y (str): y
* params.goal_pos.yaw (str): orientation

Note: start_pos/goal_pos should follow the format (x, y, ori). Specifically,
given a 5x5 map as follows where `P` indicates the start pos and `G` indicates
the goal position.
```
* * * * *
* P     *
*   * * *
*     G *
* * * * *
```
Then, the input `start_pos = (1, 1, 0)` while the `goal_pos = (3, 3, 0)`. 

Finally, we can pass the parameters settings from python to lua using the following:
```python
self._lab.write_property("params.maze_configs.name", self.maze_name)
```
Please refer the `reset` function in `env\LabEnv.py` for more details. 
## Acknowledgement
Thanks for the instructions from authors of Deepmind Lab. Thanks for the in-depth discussions with David Klee. I also
bootstrap some code from David's implementation.
