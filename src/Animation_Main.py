from Map import *

v = False
mr = MapReader(PUBLIC_BLOCK_SIZE=(2, 2), CAPACITY_PER_PIXEL=2, TIME_STEP_PER_PIXEL=2, RECORD_LOCATION_PIXELS=True)  # NEED to set record location pixels
M = mr.create_map_from_file('test_map_small.png')

mw = MapWriter(M, 'test_map_small.png', 'small_test_virus0_map.psv')

#dewit
mw.animate('virus0_small.gif')