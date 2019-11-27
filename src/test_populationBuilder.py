from unittest import TestCase

from SINUtil import *
from PersonState import Person, PopulationBuilder

class TestPopulationBuilder(TestCase):
	from Map import MapReader
	v = False
	# use the map reader since making one of these by hand is going to be a pain
	mr = MapReader(PUBLIC_BLOCK_SIZE=(2, 2), CAPACITY_PER_PIXEL=2, TIME_STEP_PER_PIXEL=2)
	M = mr.create_map_from_file('../test_map_small.png')
	tl_tl_home = M.loc_list[0]	#top left home
	tl_home = M.loc_list[42]  # this is the home which is down-right of the top-left home (9th cell if counting left-right, top-bottom)
	br_shop = M.loc_list[175]  # this is the shop in the bottom right corner
	L_office = M.loc_list[119]  # this is the L-shaped office

	def test_assign_primitive_details(self):
		np.random.seed(0)
		p = Person(self.tl_home,self.M)
		pb = PopulationBuilder(self.M,1)
		pb.assign_primitive_details(p)

		#normal unit stuff
		assert(p.home == self.tl_home)
		assert(p.M == self.M)
		assert(p.currentLocation == self.tl_home)
		for t in range(*p.sleep_schedule):
			assert(not time_within_tuple(t,p.work_schedule))#not asleep during work

		pass

	def test_assign_coworkers(self):
		np.random.seed(0)
		people = [Person(self.tl_home,self.M),
				  Person(self.tl_tl_home,self.M),
				  Person(self.tl_home,self.M),
				  Person(self.tl_home,self.M),
				  Person(self.tl_tl_home,self.M)]
		pb = PopulationBuilder(self.M, 5)
		for p in people:
			pb.assign_primitive_details(p)
			#make sure their workplace is all the same
			p.set_workplace(self.L_office)

		#now assign coworkers
		for p in people:
			pb.assign_coworkers(p)

		pass

	def test_assign_partners(self):
		np.random.seed(0)
		people = [Person(self.tl_home, self.M),
				  Person(self.tl_home, self.M),
				  Person(self.tl_home, self.M),
				  Person(self.tl_home, self.M),
				  Person(self.tl_home, self.M)]
		pb = PopulationBuilder(self.M, 5)
		pb.set_partners_distribution(lambda num_people_in_house: min(int(coinflip(0.5)),num_people_in_house))

		for p in people:
			pb.assign_primitive_details(p)

		for p in people:
			pb.assign_partners(p)

		pass

	def test_assign_friends(self):
		np.random.seed(0)
		people = [Person(self.tl_home, self.M),
				  Person(self.tl_tl_home, self.M),
				  Person(self.tl_home, self.M),
				  Person(self.tl_home, self.M),
				  Person(self.tl_tl_home, self.M)]
		pb = PopulationBuilder(self.M, 5)
		for p in people:
			pb.assign_primitive_details(p)
			# make sure they all hang out at least at one particular place
			p.add_place(self.br_shop)

		for p in people:
			pb.assign_friends(p)

		pass


	def test_create_population(self):
		#BIG MAMMA
		pb = PopulationBuilder(self.M,100)
		plist = pb.create_population()
		pass
