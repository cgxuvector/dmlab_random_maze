local pickups = require "common.pickups"
local custom_observations = require "decorators.custom_observations"
local property_decorator = require "decorators.property_decorator"
local timeout = require "decorators.timeout"
local game = require "dmlab.system.game"
local tensor = require "dmlab.system.tensor"
local make_map = require "common.make_map"
local texture_set = require "themes.texture_sets"

-- parameters between python and lua
local api = {
    _properties = {
        -- maze configurations
	-- -- name: name of the maze
	-- -- size: size of the maze (square)
	-- -- seed: random seed
	-- -- txt: txt map
	-- -- texture: texture name (MISHMASH, TRON, MINESWEEPER, TETRIS, GO, PACMAN, INVISIBLE_WALLS)
	-- -- decal_freq: frequency of the posters on the wall
        maze_configs = {
            name = 'maze_5x5',
	    size = '5',
	    seed = '1234',
            map_txt = "*****\n*APA*\n*A***\n*AAG*\n*****\n",
            texture = "MISHMASH",
            decal_freq = '0.1'
        },
        -- start position
	-- -- trans: (x, y, z)
	-- -- rots: (pitch, yaw, roll)
        start_pos = {
            x = '250',
            y = '350',
	    z = '31.125',
            yaw = '0'
        },
        -- goal position
	-- -- trans: (x, y, z)
	-- -- rots: (pitch, yaw, roll)
        goal_pos = {
            x = '350',
            y = '150',
	    z = '31.125',
	    yaw = '0'
        },
	-- random position
	-- -- trans: (x, y, z)
	-- -- rots: (pitch, yaw, roll)
	view_pos = {
	    x = '0',
	    y = '0',
	    z = '0',
	    pitch = '0',
	    yaw = '0',
	    roll = '0'
	}
    }
}

-- This callback is used to set pickup operations
-- The default is A = apple_reward, G = goal
function api:createPickup(className)
    return pickups.defaults[className]
end

-- auxiliary functions
function update_texture(texture_name)
     -- set the texture
    local texture = nil
    if texture_name == "TRON" then
        texture = texture_set.TRON
    elseif texture_name == "MINESWEEPER" then
	texture = texture_set.MINESWEEPER
    elseif texture_name == "TETRIS" then
        texture = texture_set.TETRIS
    elseif texture_name == "GO" then
	texture = texture_set.GO 
    elseif texture_name == "PACMAN" then 
        texture = texture_set.PACMAN
    elseif texture_name == "INVISIBLE_WALLS" then
        texture = texture_set.INVISIBLE_WALLS
    else
	texture = texture_set.MISHMASH
    end
    return texture
end

-- print information
function print_api_info()
    print("Api information: ")
    print("Maze size = ", api._properties.maze_configs.size)
    print("Maze ranom seed = ", api._properties.maze_configs.seed)
    print("Start pos = ", api._properties.start_pos.x, api._properties.start_pos.y, api._properties.start_pos.z, api._properties.start_pos.yaw)
    print("Goal pos = ", api._properties.goal_pos.x, api._properties.goal_pos.y, api._properties.goal_pos.z, api._properties.goal_pos.yaw)
    print("Maze txt map = ", api._properties.maze_configs.map_txt)
    print("Maze name = ", api._properties.maze_configs.name)
    print("Maze seed = ", api._properties.maze_configs.seed)
    print("Maze texture = ", api._properties.maze_configs.texture)
    print("Maze decal freq = ", api._properties.maze_configs.decal_freq)
    print("---------------------------------")
end

-- This callback is used when reset is called
-- if pass episode == 0, a new maze will be reloaded and made.
function api:start(episode, seed)
    if episode == 0 then
	make_map.random():seed(tonumber(api._properties.maze_configs.seed))
        self._maze = make_map.makeMap{
            mapName = api._properties.maze_configs.name,
	    mapEntityLayer = api._properties.maze_configs.map_txt,
	    useSkybox = true,
	    decalFrequency = tonumber(api._properties.maze_configs.decal_freq),
	    textureSet = update_texture(api._properties.maze_configs.texture)	
        }
     end
end

-- This callback is used when the map is reloaded (fast load).
function api:nextMap() 
    local mazeName = self._maze
    self._maze = ""
    return mazeName
end

-- This callback is used to set the start and goal positions
function api:updateSpawnVars(spawnVars)
    -- set start position and orientation
    if spawnVars.classname == "info_player_start" then
	-- set orientation
	spawnVars.angle = self._properties.start_pos.yaw
	-- set position
        spawnVars.origin = self._properties.start_pos.x .. " " .. self._properties.start_pos.y .. " " .. self._properties.start_pos.z
	-- set orientation variance to be 0
	spawnVars.randomAngleRange = "0"	
    -- set goal position
    elseif spawnVars.classname == "goal" then	
	spawnVars.count = '10'
	spawnVars.origin = self._properties.goal_pos.x .. " " .. self._properties.goal_pos.y .. " " .. self._properties.goal_pos.z
    elseif spawnVars.classname == 'apple_reward' then
        spawnVars.count = '1'
    end
    return spawnVars
end

-- customized panoramic view
-- Note: pos and look represent camera position and angle respectively. The data type is table with number element
-- Pos = {x, y, z}
-- Look = {pitch, yaw, roll} => {head up(-)/down(+), head right(-1)/left(+), roll}
local SCREEN = game:screenShape()
local SHAPE = SCREEN.buffer
local function panoramaView()
    -- observe function
    local function angleLook(yaw)
        local info = game:playerInfo()
        local pos = info.eyePos
        local look = game:playerInfo().angles
        look[2] = look[2] + yaw
        local buffer = game:renderCustomView{
	    width = SHAPE.width,
            height = SHAPE.height,
	    pos = pos,
            look = look,
            renderPlayer = false,
        }
        return buffer:clone()
    end
    -- obtain the panoramic views
    -- front left    front    fron right
    -- left                        right
    -- back left     back     back right
    local front = angleLook(0)
    local front_left = angleLook(45)
    local left = angleLook(90)
    local back_left = angleLook(135)
    local back = angleLook(180)
    local back_right = angleLook(225)
    local right = angleLook(270)
    local front_right = angleLook(315)
    -- store the panoramic view
    local shape = front:shape() 
    local panorama = tensor.ByteTensor(8, shape[1], shape[2], shape[3])
    panorama:select(1, 1):copy(front)
    panorama:select(1, 2):copy(front_left)
    panorama:select(1, 3):copy(left)
    panorama:select(1, 4):copy(back_left)
    panorama:select(1, 5):copy(back)
    panorama:select(1, 6):copy(back_right)
    panorama:select(1, 7):copy(right)
    panorama:select(1, 8):copy(front_right)
    -- return the panorama
    return panorama
end

-- customized view in top down view
local function topDownView()
    local view_scope = api._properties.maze_configs.size * 100
    local buffer = game:renderCustomView{
            width = view_scope,
	    height = view_scope,
	    pos = {view_scope/2, view_scope/2, 50 + view_scope/2},
            look = {90, 0, 0},
            renderPlayer = false,
    }
    return buffer:clone()
end

-- customized view in random position and orientation
local function randomView()
    local pos = api._properties.view_pos
    local buffer = game:renderCustomView{
        width = SHAPE.width,
	height = SHAPE.height,
	pos = {tonumber(pos.x), 
	       tonumber(pos.y), 
	       tonumber(pos.z)},
        look = {0, tonumber(pos.yaw), 0},
	renderPlayer = false,
    }
    return buffer:clone()
end

-- decorate the api of customized observations
custom_observations.decorate(api)
custom_observations.addSpec('RGB.LOOK_PANORAMA_VIEW', 'Bytes', {8, SHAPE.height, SHAPE.width, 3}, panoramaView)
custom_observations.addSpec('RGB.LOOK_TOP_DOWN_VIEW', 'Bytes', {SHAPE.height, SHAPE.width, 3}, topDownView)
custom_observations.addSpec('RGB.LOOK_RANDOM_VIEW', 'Bytes', {SHAPE.height, SHAPE.width, 3}, randomView)

-- decorate the api of property
property_decorator.decorate(api)
property_decorator.addReadWrite('params', api._properties)

-- decorate the time to be 10 minutes
timeout.decorate(api, 10 * 60)
return api
