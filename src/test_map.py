from unittest import TestCase

from Map import *

class TestMap(TestCase):
	def test_get_path(self):
		v = False
		#use the map reader since making one of these by hand is going to be a pain
		mr = MapReader(PUBLIC_BLOCK_SIZE=(2,2),CAPACITY_PER_PIXEL=2,TIME_STEP_PER_PIXEL=2)
		m = mr.create_map_from_file('../test_map_small.png')
		tl_home = m.loc_list[42]#this is the home which is down-right of the top-left home (9th cell if counting left-right, top-bottom)
		br_shop = m.loc_list[175]#this is the shop in the bottom right corner
		L_office = m.loc_list[119]#this is the L-shaped office

		home_office = m.get_path(tl_home,L_office,verbose=v)
		home_shop = m.get_path(tl_home,br_shop,verbose=v)
		shop_office = m.get_path(br_shop,L_office,verbose=v)