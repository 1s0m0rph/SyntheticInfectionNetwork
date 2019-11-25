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
					   'VOID':'ffffff',#this is a special type used for when you're too lazy to actually fill in all the pixels; it is ignored
				   	   'PROC_FINISHED':'f0f0f0'#this is a special type used to indicate that processing for this pixel is finished
					   }

LTC_INV = {LOC_TYPE_COLORS[k]:k for k in LOC_TYPE_COLORS}#this is just the inverse of the color map

LOC_TYPE_INDEX = {	'home':0,
					'office':1,
					'convention':2,
				   	'shop':3,
				   	'public':4,
				   	'hospital':5,
				   	'VOID':6,
					'PROC_FINISHED':7
				   }

LTI_INV = {LOC_TYPE_INDEX[k]:k for k in LOC_TYPE_INDEX}


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
	

	PUBLIC_BLOCK_SIZE = (10,10)

	CAPACITY_PER_PIXEL = 1	#how many people can sit on one pixel?

	TIME_STEP_PER_PIXEL = 1	#how many time steps does it take to traverse 1 pixel?


	def __init__(self):
		self.R_LTC_INTERNAL = {LOC_TYPE_INDEX[k]:k for k in LOC_TYPE_INDEX}#this is just the inverse of the type map
		self.img = None
		self.next_loc_idx = len(LOC_TYPE_COLORS)#basically, what's the next location index we'll assign?

		self.loc_list = []

	'''
	Convert a triplet of ints (r,g,b) to a hex
	'''
	def int3_to_hex(self,i3):
		rv,gv,bv,_ = i3#technically rgba
		rx = pad(hex(rv)[2:],2,withch='0',at_beginning=True)
		gx = pad(hex(gv)[2:],2,withch='0',at_beginning=True)
		bx = pad(hex(bv)[2:],2,withch='0',at_beginning=True)

		return rx + gx + bx

	def reformat_imgarray(self,iar):
		ref = []
		for row in iar:
			tmpl = []
			for px in row:
				hexval = self.int3_to_hex(px)
				tmpl.append(LOC_TYPE_INDEX[LTC_INV[hexval]])
			ref.append(tmpl)
		return ref

	'''
	Do a bfs starting from these start coordinates, assigning a number to each value we see with edges defined as going from a pixel to all its neighbors, corners not included
	
	endx,endy will be set for things like public spaces which can only be so big
	
	while we're at it, we'll also calculate the center of this location and add it to the list
	'''
	def assign_number_to_contiguous_block(self, startx, starty, endx=None, endy=None, llimx=None, llimy=None):
		if endx is None:
			endx = len(self.img[0])
			endy = len(self.img)
		else:
			endx = min(endx,len(self.img[0]))
			endy = min(endy,len(self.img))
		if llimx is None:
			llimx = 0
			llimy = 0
		else:
			llimx = max(llimx,0)
			llimy = max(llimy,0)

		ltype_i = self.img[starty][startx]
		if ltype_i == LOC_TYPE_INDEX['VOID']:
			return#nothing to do, since we want to just ignore void regions

		#now do a bfs starting from this pixel
		#info for calculating the centroid, capacity, and travel time
		npixels = 1#the only one we have is the start pixel
		coordsum_in_loc_x = startx
		coordsum_in_loc_y = starty

		self.img[starty][startx] = self.next_loc_idx
		travq = [(startx,starty)]
		while len(travq) > 0:
			cx,cy = travq.pop()

			neighbors_possible = [(cx,cy-1),(cx,cy+1),(cx-1,cy),(cx+1,cy)]
			for jx,jy in neighbors_possible:
				if not ((jx < llimx) or (jy < llimy) or (jx >= endx) or (jy >= endy)):
					#then this is actually a neighbor and is in the image (not off the edge)
					if self.img[jy][jx] == ltype_i:#this check basically does the seen thing for us, since we're changing their numbers around as we go
						#then this pixel is of the right type, change its number
						self.img[jy][jx] = self.next_loc_idx
						#and add it to the queue and the seen
						travq.append((jx,jy))

						#now do the centroid calculation stuff as well as capacity
						npixels += 1
						coordsum_in_loc_x += jx
						coordsum_in_loc_y += jy

		cap = int(npixels * MapReader.CAPACITY_PER_PIXEL)
		#average the coordsums to get the centroid
		avgx = float(coordsum_in_loc_x) / float(npixels)
		avgy = float(coordsum_in_loc_y) / float(npixels)
		#centroid is (avgx,avgy)
		ttime = np.sqrt(npixels)
		#travel time is assumed to be linear in the side length of a square with equivalent area

		from PersonState import Location
		l = Location(LTI_INV[ltype_i],capacity=cap)
		l.mapx_center = avgx
		l.mapy_center = avgy
		l.travel_time = ttime
		self.loc_list.append(l)

		self.next_loc_idx += 1

	def scan_to_next(self,x,y,assigned=False):
		while (x < len(self.img[0])) and (y < len(self.img)):
			if assigned:
				if (self.img[y][x] != LOC_TYPE_INDEX['VOID']) and (self.img[y][x] >= len(LOC_TYPE_COLORS)):#have to check for void here to prevent infinite looping
					#we have a winner
					return x,y
			else:
				if (self.img[y][x] != LOC_TYPE_INDEX['VOID']) and (self.img[y][x] < len(LOC_TYPE_COLORS)):#have to check for void here to prevent infinite looping
					#we have a winner
					return x,y

			x += 1
			if x == len(self.img[y]):
				x = 0
				y += 1
		return -1,-1

	'''
	Using the locs in location list, assign adjacencies based on the same edge properties

	the process is to do a bfs on the type as when assigning numbers, but look for edges out of the same number group
	'''
	def assign_loc_adjacencies(self,startx,starty):
		endx = len(self.img[0])
		endy = len(self.img)
		llimx = 0
		llimy = 0

		loc_assign = self.img[starty][startx]
		if (loc_assign == LOC_TYPE_INDEX['VOID']) or (loc_assign == LOC_TYPE_INDEX['PROC_FINISHED']):
			return#nothing to do
		assert(loc_assign not in LOC_TYPE_INDEX)#can't be an unassigned generic location type

		travq = [(startx, starty)]
		self.img[starty][startx] = LOC_TYPE_INDEX['PROC_FINISHED']#meaning processing for this one is done

		while len(travq) > 0:
			cx, cy = travq.pop()

			neighbors_possible = [(cx, cy - 1), (cx, cy + 1), (cx - 1, cy), (cx + 1, cy)]
			for jx, jy in neighbors_possible:
				if not ((jx < llimx) or (jy < llimy) or (jx >= endx) or (jy >= endy)):
					# then this is actually a neighbor and is in the image (not off the edge)
					jval = self.img[jy][jx]
					if (jval != loc_assign) and (jval != LOC_TYPE_INDEX['VOID']) and (jval != LOC_TYPE_INDEX['PROC_FINISHED']):
						# then this pixel is of the right type, assign its location to be adjacent to us

						self.loc_list[jval - len(LOC_TYPE_COLORS)].adj_locs.add(self.loc_list[loc_assign - len(LOC_TYPE_COLORS)])
						self.loc_list[loc_assign - len(LOC_TYPE_COLORS)].adj_locs.add(self.loc_list[jval - len(LOC_TYPE_COLORS)])

					elif (jval != LOC_TYPE_INDEX['VOID']) and (jval != LOC_TYPE_INDEX['PROC_FINISHED']):
						travq.append((jx, jy))
						self.img[jy][jx] = LOC_TYPE_INDEX['PROC_FINISHED']



	'''
	Do all the contiguous blocks, with the correct limits set for public ones
	
	also do the adjacencies while we're at it
	'''
	def assign_all_blocks(self,do_adjacencies=True):
		x,y = self.scan_to_next(0,0,assigned=False)
		while (x != -1) and (y != -1):
			endx = endy = None
			llimx = llimy = None
			if self.img[y][x] == LOC_TYPE_INDEX['public']:#then we need to impose limits
				endx = x + MapReader.PUBLIC_BLOCK_SIZE[0]
				endy = y + MapReader.PUBLIC_BLOCK_SIZE[1]

				llimx = x
				llimy = y
			self.assign_number_to_contiguous_block(x,y,endx=endx,endy=endy,llimx=llimx,llimy=llimy)

			x,y = self.scan_to_next(x,y,assigned=False)

		#now do the adjacencies
		if do_adjacencies:
			x, y = self.scan_to_next(0, 0, assigned=True)
			while (x != -1) and (y != -1):
				self.assign_loc_adjacencies(x,y)
				x, y = self.scan_to_next(x, y, assigned=True)


	'''
	Given an image file fname, create a map equivalent to it
	'''
	def read_from_file(self,fname):
		import imageio
		farray = imageio.imread(fname)
		self.img = self.reformat_imgarray(farray)


	def create_map_from_file(self,fname):
		self.read_from_file(fname)
		self.assign_all_blocks()
		m = Map(self.loc_list)
		return m

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

	def __init__(self,loc_list):

		self.loc_list = loc_list#list of locations, they each maintain their own adjacencies


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