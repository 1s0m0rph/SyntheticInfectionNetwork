from unittest import TestCase

from Map import *


class TestMapWriter(TestCase):

	def test_initialization(self):
		v = False
		# use the map reader since making one of these by hand is going to be a pain
		from PersonState import Location
		Location.LOCATION_ID_COUNTER = 0
		mr = MapReader(PUBLIC_BLOCK_SIZE=(2, 2), CAPACITY_PER_PIXEL=2, TIME_STEP_PER_PIXEL=2, RECORD_LOCATION_PIXELS=True)  # NEED to set record location pixels
		M = mr.create_map_from_file('../test_map_small.png')
		tl_tl_home = M.loc_list[0]  # top left home
		tl_home = M.loc_list[42]  # this is the home which is down-right of the top-left home (9th cell if counting left-right, top-bottom)
		br_shop = M.loc_list[175]  # this is the shop in the bottom right corner
		L_office = M.loc_list[119]  # this is the L-shaped office

		np.random.seed(0)
		from PersonState import Person
		Person.PERSON_ID_COUNTER = 0
		mw = MapWriter(M, '../test_map_small.png', 'mapwriter_data_test.psv')

		assert (len(mw.diseases) == 1)
		assert ('virus 0' in mw.diseases)
		assert (len(mw.population) == 100)

	def test_place_people(self):
		v = False
		# use the map reader since making one of these by hand is going to be a pain
		from PersonState import Location
		Location.LOCATION_ID_COUNTER = 0
		mr = MapReader(PUBLIC_BLOCK_SIZE=(2, 2), CAPACITY_PER_PIXEL=2, TIME_STEP_PER_PIXEL=2, RECORD_LOCATION_PIXELS=True)  # NEED to set record location pixels
		M = mr.create_map_from_file('../test_map_small.png')
		tl_tl_home = M.loc_list[0]  # top left home
		tl_home = M.loc_list[42]  # this is the home which is down-right of the top-left home (9th cell if counting left-right, top-bottom)
		br_shop = M.loc_list[175]  # this is the shop in the bottom right corner
		L_office = M.loc_list[119]  # this is the L-shaped office

		# put a bunch of randos in the tl home and yeet anyone that's in there
		mw = MapWriter(M, '../test_map_small.png', 'mapwriter_data_test.psv')
		tl_tl_home.people = []
		np.random.seed(0)
		from PersonState import Person
		Person.PERSON_ID_COUNTER = 0
		people = [
			Person(tl_tl_home, M),
			Person(tl_tl_home, M),
			Person(tl_tl_home, M),
			Person(tl_tl_home, M),
			Person(tl_tl_home, M),
		]

		# 5 should fit with the 1 space constraint

		ret = mw.place_people(tl_tl_home)

		# regress on this result
		assert (ret[people[0]] == (2, 4))
		assert (ret[people[1]] == (0, 3))
		assert (ret[people[2]] == (3, 1))
		assert (ret[people[3]] == (0, 1))
		assert (ret[people[4]] == (4, 3))

		# now cram 'em in *just* tight enough to cause it to warn us

		Person.PERSON_ID_COUNTER = 0
		mw = MapWriter(M, '../test_map_small.png', 'mapwriter_data_test.psv')
		tl_tl_home.people = []

		Person.PERSON_ID_COUNTER = 0
		people = [
			Person(tl_tl_home, M),
			Person(tl_tl_home, M),
			Person(tl_tl_home, M),
			Person(tl_tl_home, M),
			Person(tl_tl_home, M),
			Person(tl_tl_home, M),
			Person(tl_tl_home, M),
			Person(tl_tl_home, M),
			Person(tl_tl_home, M),
			Person(tl_tl_home, M)
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
		M = mr.create_map_from_file('../test_map_small.png')
		tl_tl_home = M.loc_list[0]  # top left home
		tl_home = M.loc_list[42]  # this is the home which is down-right of the top-left home (9th cell if counting left-right, top-bottom)
		br_shop = M.loc_list[175]  # this is the shop in the bottom right corner
		L_office = M.loc_list[119]  # this is the L-shaped office

		mw = MapWriter(M, '../test_map_small.png', 'mapwriter_data_test.psv')

		mw.load_sim_config(1)  # the first one

		pass
