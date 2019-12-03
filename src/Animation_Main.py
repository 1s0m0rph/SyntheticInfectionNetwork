from Map import *

v = False
mr = MapReader(PUBLIC_BLOCK_SIZE=(2, 2), CAPACITY_PER_PIXEL=2, TIME_STEP_PER_PIXEL=2, RECORD_LOCATION_PIXELS=True)  # NEED to set record location pixels

mw = MapWriter()
mw.img_expansion_factor = 3
mw.desaturate_map = True
mw.color_map = MapWriter.DISEASE_STATE_COLOR_MAP_SIMPLIFIED
mw.initialize_all('test_map_small.png', 'small_test_all_diseases_map_pop150.psv',mr)

#dewit
mw.animate('all_diseases_small_pop150.gif')