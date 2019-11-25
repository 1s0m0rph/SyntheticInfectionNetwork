from unittest import TestCase

from Map import *


class TestMapReader(TestCase):
	def test_assign_number_to_contiguous_block(self):
		img = [[0, 0, 0, 2, 0],
			   [1, 1, 0, 2, 0],
			   [1, 1, 6, 2, 0],
			   [2, 2, 2, 2, 0],
			   [1, 1, 1, 1, 0],
			   [6, 6, 6, 6, 6]]  # asymmetric so we can make sure we didn't swap any ys or xs

		mr = MapReader()
		mr.img = img

		mr.assign_number_to_contiguous_block(0, 0)

		assert (mr.img == [[8, 8, 8, 2, 0],
						   [1, 1, 8, 2, 0],
						   [1, 1, 6, 2, 0],
						   [2, 2, 2, 2, 0],
						   [1, 1, 1, 1, 0],
						   [6, 6, 6, 6, 6]]
				)

		mr.assign_number_to_contiguous_block(2, 2)

		assert (mr.img == [[8, 8, 8, 2, 0],
						   [1, 1, 8, 2, 0],
						   [1, 1, 6, 2, 0],
						   [2, 2, 2, 2, 0],
						   [1, 1, 1, 1, 0],
						   [6, 6, 6, 6, 6]]
				)

		# limits testing
		mr.assign_number_to_contiguous_block(4, 2, 4 + 2, 2 + 2, 4, 2)

		assert (mr.img == [[8, 8, 8, 2, 0],
						   [1, 1, 8, 2, 0],
						   [1, 1, 6, 2, 9],
						   [2, 2, 2, 2, 9],
						   [1, 1, 1, 1, 0],
						   [6, 6, 6, 6, 6]]
				)

	def test_assign_all_blocks(self):
		img = [[0, 0, 0, 2, 0],
			   [1, 1, 0, 2, 0],
			   [1, 1, 6, 2, 0],
			   [2, 2, 2, 2, 0],
			   [1, 1, 1, 1, 0],
			   [6, 6, 6, 6, 6]]  # asymmetric so we can make sure we didn't swap any ys or xs

		mr = MapReader()
		mr.img = img

		mr.assign_all_blocks(do_adjacencies=False)

		assert (mr.img == [[8, 8, 8, 9, 10],
						   [11, 11, 8, 9, 10],
						   [11, 11, 6, 9, 10],
						   [9, 9, 9, 9, 10],
						   [12, 12, 12, 12, 10],
						   [6, 6, 6, 6, 6]]
				)

		img = [[4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4],
			   [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4],
			   [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4],
			   [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4],
			   [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4],
			   [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4],
			   [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4],
			   [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4],
			   [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4],
			   [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4],
			   [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4]]  # testing the block limits

		mr = MapReader()
		mr.img = img

		mr.assign_all_blocks(do_adjacencies=False)

		assert (mr.img == [[8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 9],
						   [8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 9],
						   [8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 9],
						   [8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 9],
						   [8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 9],
						   [8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 9],
						   [8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 9],
						   [8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 9],
						   [8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 9],
						   [8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 9],
						   [10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 11]]
				)

		assert (len(mr.loc_list) == 4)
		assert (mr.loc_list[0].loc_type == 'public')
		assert (mr.loc_list[3].mapx_center == 10)
		assert (mr.loc_list[3].mapy_center == 10)

	def test_assign_loc_adjacencies(self):
		img = [[8, 8, 8, 9, 10],
			   [11, 11, 8, 9, 10],
			   [11, 11, 6, 9, 10],
			   [9, 9, 9, 9, 10],
			   [12, 12, 12, 12, 10],
			   [6, 6, 6, 6, 6]]

		mr = MapReader()
		mr.img = img

		from PersonState import Location
		mr.loc_list = [Location('home'),
					   Location('convention'),
					   Location('home'),
					   Location('office'),
					   Location('convention')]

		mr.assign_loc_adjacencies(0,0)#the first one in the list; i.e. the first home
		assert(mr.loc_list[1] in mr.loc_list[0].adj_locs)
		assert(mr.loc_list[3] in mr.loc_list[0].adj_locs)

		mr.assign_loc_adjacencies(0,3)#the second one in the list
		assert(mr.loc_list[0] in mr.loc_list[1].adj_locs)
		assert(mr.loc_list[2] in mr.loc_list[1].adj_locs)
		assert(mr.loc_list[3] in mr.loc_list[1].adj_locs)
		assert(mr.loc_list[4] in mr.loc_list[1].adj_locs)

	def test_create_map_from_file(self):
		fname = '../test_map_0.png'
		#this has 1 hospital
		#1 convention
		#13 office
		#13 shops
		#298 homes
		#and, for the sake of regression testing, 518 public cells
		mr = MapReader()

		m = mr.create_map_from_file(fname)

		counts = [0,0,0,0,0,0,0]
		for loc in m.loc_list:
			loc_i = LOC_TYPE_INDEX[loc.loc_type]
			counts[loc_i] += 1

		assert(counts == [298,13,1,13,518,1,0])