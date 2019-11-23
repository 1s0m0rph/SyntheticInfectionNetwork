"""
This file defines all of the classes, algorithms, and data structures related to where things are, what things there are, and how it is all connected in terms of Locations

"""

from SINUtil import *

LOC_TYPE_COLORS = {'home':'7f0000',
					   'office':'ff00ff',
					   'convention':'00ff00',
					   'shop':'0000ff',
					   'public':'000000',
					   'hospital':'dc2323',
					   'VOID':'ffffff'#this is a special type used for when you're too lazy to actually fill in all the pixels; it is ignored
					   }
"""
We will use this class to read maps from image files

some semantics for map files:
	all the colors are defined by the class static variable LOC_TYPE_COLORS
	all locations except public are assumed to be contiguous up to borders with other location types
	public locations are blocked according to a grid defined on the image 2d-array with granularity given by PUBLIC_BLOCK_SIZE
		this means that, if you have a 500x500 map file and set PUBLIC_BLOCK_SIZE to (10,10) (10x10), there will be a new grid induced on that one of 50x50 10x10 blocks.
		each of those blocks will define AT MOST one CONTIGUOUS public space, so if your public space is massive, it'll be broken up into smaller pieces
	for non-public locations, capacity is assumed to be correlated with size -- more area = more people (at a rate of CAPACITY_PER_PIXEL)
	in general, the time taken to go across a certain location is proportional to its area (at a rate of TIME_STEP_PER_PIXEL)
	
"""
class MapReader:
	LTC_INV = {LOC_TYPE_COLORS[k]:k for k in LOC_TYPE_COLORS}#this is just the inverse of the color map

	PUBLIC_BLOCK_SIZE = (10,10)

	CAPACITY_PER_PIXEL = 1	#how many people can sit on one pixel?

	TIME_STEP_PER_PIXEL = 1	#how many time steps does it take to traverse 1 pixel?

	from PersonState import Location


	'''
	Given an image file fname, create a map equivalent to it
	'''
	def read_from_file(self,fname):
		import imageio
		farray = imageio.imread(fname)
		#TODO: implement the 'read map from file' functionality
		pass

"""
This consists essentially of a network of locations that we can travel between where locations are, as defined in PersonState (Location class):

	home
	office
	convention
	shop
	public
	hospital
"""
class Map:

	from PersonState import Location

	def __init__(self):

		self.loclist = []#list of locations, they each maintain their own adjacencies


	'''
	give me a path I can use to go from a to b along the map
	
	uses dijkstra/uniform cost with A* manhattan heuristic, moving only on public spaces (the first move is to go from this location to the nearest public one
		h (parameter) is the heuristic function
	'''
	def get_path(self,a:Location,b:Location,h=manhattan_distance):
		if a == b:
			return []#we're already there
		path = []
		current_loc = a
		if a.loc_type != 'public':#then find the/a public space adjacent to a
			for lj in a.adj_locs:
				if lj.loc_type == 'public':
					path.append(lj)
					break
			if len(path) == 0:
				raise AttributeError("Location " + str(a) + " is not adjacent to a location of type public.")

		#TODO: implement dijkstra/ucs/A* here

		return path