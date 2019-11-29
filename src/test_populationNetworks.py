import unittest

from SINUtil import *
from PersonState import Person, PopulationBuilder

class TestNetworks(unittest.TestCase):
	from Map import MapReader
	v = False
	# use the map reader since making one of these by hand is going to be a pain
	mr = MapReader(PUBLIC_BLOCK_SIZE=(2, 2), CAPACITY_PER_PIXEL=2, TIME_STEP_PER_PIXEL=2)
	M = mr.create_map_from_file('../test_map_small.png')
	tl_tl_home = M.loc_list[0]  # top left home
	tl_home = M.loc_list[
		42]  # this is the home which is down-right of the top-left home (9th cell if counting left-right, top-bottom)
	br_shop = M.loc_list[175]  # this is the shop in the bottom right corner
	L_office = M.loc_list[119]  # this is the L-shaped office

	'''
	Use a bfs from this node to find the connected components on
		friends network (edge_type = friends)
		coworkers network (edge_type = coworkers)
		both (edge_type = union)
	'''
	def bfs_connected_component(self, start_person, edge_type, components):

		for comp in components:
			if start_person in comp:
				return components  # this one's already been found

		pq = [start_person]  # queue for bfs
		current = None  # starting from me
		seen = {start_person}

		while len(pq) > 0:
			current = pq.pop(0)

			# figure out what edge_type of neighbors we are looking for
			neighbors = set()
			if edge_type == 'coworkers':
				neighbors = current.coworkers
			elif edge_type == 'friends':
				neighbors = current.friends
			elif edge_type == 'union':
				neighbors = current.coworkers.union(current.friends)

			for n in neighbors:
				if not n in seen:  # then this node hasn't been seen yet
					seen.add(n)
					pq.append(n)  # add n to the queue

		components.append(seen)
		return components

	def find_all_connected_components(self, pop, edge_type='union'):
		components = []
		for person in pop:
			components = self.bfs_connected_component(person, edge_type, components)

		return components

	def test_network_connectedness(self):
		np.random.seed(0)
		pb = PopulationBuilder(self.M, 100)
		plist = pb.create_population()

		friends = self.find_all_connected_components(plist, 'friends')
		coworkers = self.find_all_connected_components(plist, 'coworkers')
		all = self.find_all_connected_components(plist, 'union')
		pass

