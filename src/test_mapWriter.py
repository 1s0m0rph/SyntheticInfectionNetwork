from unittest import TestCase

from Map import *


class TestMapWriter(TestCase):

	def test_initialization(self):
		v = False
		# use the map reader since making one of these by hand is going to be a pain
		from PersonState import Location
		Location.LOCATION_ID_COUNTER = 0
		mr = MapReader(PUBLIC_BLOCK_SIZE=(2, 2), CAPACITY_PER_PIXEL=2, TIME_STEP_PER_PIXEL=2, RECORD_LOCATION_PIXELS=True)  # NEED to set record location pixels

		np.random.seed(0)
		from PersonState import Person
		Person.PERSON_ID_COUNTER = 0
		mw = MapWriter()
		mw.initialize_all('../test_map_small.png', 'mapwriter_data_test.psv',mr)

		assert (len(mw.diseases) == 1)
		assert ('virus 0' in mw.diseases)
		assert (len(mw.population) == 100)

	def test_place_people(self):
		v = False
		# use the map reader since making one of these by hand is going to be a pain
		from PersonState import Location
		Location.LOCATION_ID_COUNTER = 0
		mr = MapReader(PUBLIC_BLOCK_SIZE=(2, 2), CAPACITY_PER_PIXEL=2, TIME_STEP_PER_PIXEL=2, RECORD_LOCATION_PIXELS=True)  # NEED to set record location pixels
		mw = MapWriter()
		mw.read_img('../test_map_small.png',mr)
		mw.read_data('mapwriter_data_test.psv')
		mw.format_img()
		tl_tl_home = mw.M.loc_list[0]  # top left home

		# put a bunch of randos in the tl home
		np.random.seed(0)
		from PersonState import Person
		Person.PERSON_ID_COUNTER = 0
		people = [
			Person(tl_tl_home, mw.M),
			Person(tl_tl_home, mw.M),
			Person(tl_tl_home, mw.M),
			Person(tl_tl_home, mw.M),
			Person(tl_tl_home, mw.M),
		]

		# 5 should fit with the 1 space constraint

		ret = mw.place_people(tl_tl_home)

		# regress on this result
		assert (ret[people[0]] == (17, 16))
		assert (ret[people[1]] == (14, 8))
		assert (ret[people[2]] == (0, 15))
		assert (ret[people[3]] == (10, 2))
		assert (ret[people[4]] == (18, 7))

		# now cram 'em in *just* tight enough to cause it to warn us

		Person.PERSON_ID_COUNTER = 0
		mw = MapWriter()
		mw.initialize_all('../test_map_small.png', 'mapwriter_data_test.psv', mr)

		Person.PERSON_ID_COUNTER = 0
		people = [
			Person(tl_tl_home, mw.M),
			Person(tl_tl_home, mw.M),
			Person(tl_tl_home, mw.M),
			Person(tl_tl_home, mw.M),
			Person(tl_tl_home, mw.M),
			Person(tl_tl_home, mw.M),
			Person(tl_tl_home, mw.M),
			Person(tl_tl_home, mw.M),
			Person(tl_tl_home, mw.M),
			Person(tl_tl_home, mw.M)
		]

		assert (funcall_throws_error(mw.place_people, tl_tl_home, error_on_overlay=True))

	def test_load_sim_config(self):
		np.random.seed(0)
		v = False
		# use the map reader since making one of these by hand is going to be a pain
		from PersonState import Location, Person
		Location.LOCATION_ID_COUNTER = 0
		Person.PERSON_ID_COUNTER = 0
		mr = MapReader(PUBLIC_BLOCK_SIZE=(2, 2), CAPACITY_PER_PIXEL=2, TIME_STEP_PER_PIXEL=2, RECORD_LOCATION_PIXELS=True)  # NEED to set record location pixels

		mw = MapWriter()
		mw.initialize_all('../test_map_small.png', 'mapwriter_data_test.psv', mr)

		mw.load_sim_config(1)  # the first one

		pass

	def test_expand_img(self):
		mw = MapWriter()
		#initialize the map
		loc_list = []
		loc_px = {}
		from PersonState import Location
		for i in range(3):
			for j in range(3):
				l = Location('home',1)
				px = (i,j)
				loc_list.append(l)
				loc_px.update({l:{px}})

		mw.M = Map(loc_list)
		mw.M.loc_px = loc_px

		#reset the source image to something more predictable
		src_img_test = [[(i,i+1,i+2,i+3) for i in range(0,12,4)] for _ in range(3)]
		mw.img_src = src_img_test
		mw.img_expansion_factor = 3
		post_expansion = [[(0,1,2,3),(0,1,2,3),(0,1,2,3),(4,5,6,7),(4,5,6,7),(4,5,6,7),(8,9,10,11),(8,9,10,11),(8,9,10,11)],
						  [(0,1,2,3),(0,1,2,3),(0,1,2,3),(4,5,6,7),(4,5,6,7),(4,5,6,7),(8,9,10,11),(8,9,10,11),(8,9,10,11)],
						  [(0,1,2,3),(0,1,2,3),(0,1,2,3),(4,5,6,7),(4,5,6,7),(4,5,6,7),(8,9,10,11),(8,9,10,11),(8,9,10,11)],
						  [(0,1,2,3),(0,1,2,3),(0,1,2,3),(4,5,6,7),(4,5,6,7),(4,5,6,7),(8,9,10,11),(8,9,10,11),(8,9,10,11)],
						  [(0,1,2,3),(0,1,2,3),(0,1,2,3),(4,5,6,7),(4,5,6,7),(4,5,6,7),(8,9,10,11),(8,9,10,11),(8,9,10,11)],
						  [(0,1,2,3),(0,1,2,3),(0,1,2,3),(4,5,6,7),(4,5,6,7),(4,5,6,7),(8,9,10,11),(8,9,10,11),(8,9,10,11)],
						  [(0,1,2,3),(0,1,2,3),(0,1,2,3),(4,5,6,7),(4,5,6,7),(4,5,6,7),(8,9,10,11),(8,9,10,11),(8,9,10,11)],
						  [(0,1,2,3),(0,1,2,3),(0,1,2,3),(4,5,6,7),(4,5,6,7),(4,5,6,7),(8,9,10,11),(8,9,10,11),(8,9,10,11)],
						  [(0,1,2,3),(0,1,2,3),(0,1,2,3),(4,5,6,7),(4,5,6,7),(4,5,6,7),(8,9,10,11),(8,9,10,11),(8,9,10,11)],
						  ]
		mw.expand_img()
		assert(mw.img_src == post_expansion)
		assert(mw.M.loc_px[mw.M.loc_list[0]] == {(0,0),(0,1),(0,2),
												 (1,0),(1,1),(1,2),
												 (2,0),(2,1),(2,2)})