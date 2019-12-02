"""
This file defines all of the classes, algorithms, and data structures related to where things are, what things there are, and how it is all connected in terms of Locations

"""


from SINUtil import *
import heapq as hq

LOC_TYPE_COLORS = {'home':'7f0000',
					   'office':'ff00ff',
					   'convention':'00ff00',
					   'shop':'0000ff',
					   'public':'000000',
					   'hospital':'dc2323',
					   'VOID':'ffffff',#this is a special edge_type used for when you're too lazy to actually fill in all the pixels; it is ignored
				   	   'PROC_FINISHED':'f0f0f0'#this is a special edge_type used to indicate that processing for this pixel is finished
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


	def __init__(self,PUBLIC_BLOCK_SIZE=None,CAPACITY_PER_PIXEL=None,TIME_STEP_PER_PIXEL=None):
		self.R_LTC_INTERNAL = {LOC_TYPE_INDEX[k]:k for k in LOC_TYPE_INDEX}#this is just the inverse of the edge_type map
		self.img = None
		self.next_loc_idx = len(LOC_TYPE_COLORS)#basically, what's the next location index we'll assign?

		if PUBLIC_BLOCK_SIZE is not None:
			self.PUBLIC_BLOCK_SIZE = PUBLIC_BLOCK_SIZE
		if CAPACITY_PER_PIXEL is not None:
			self.CAPACITY_PER_PIXEL = CAPACITY_PER_PIXEL
		if TIME_STEP_PER_PIXEL is not None:
			self.TIME_STEP_PER_PIXEL = TIME_STEP_PER_PIXEL

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
						#then this pixel is of the right edge_type, change its number
						self.img[jy][jx] = self.next_loc_idx
						#and add it to the queue and the seen
						travq.append((jx,jy))

						#now do the centroid calculation stuff as well as capacity
						npixels += 1
						coordsum_in_loc_x += jx
						coordsum_in_loc_y += jy

		cap = int(npixels * self.CAPACITY_PER_PIXEL)
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
		l.mapx = startx#these are examples of pixels known to be within the location
		l.mapy = starty#having these ensures we can always reconstruct where they were on the map image to begin with
		l.travel_time = ttime * self.TIME_STEP_PER_PIXEL
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

	the process is to do a bfs on the edge_type as when assigning numbers, but look for edges out of the same number group
	'''
	def assign_loc_adjacencies(self,startx,starty):
		endx = len(self.img[0])
		endy = len(self.img)
		llimx = 0
		llimy = 0

		loc_assign = self.img[starty][startx]
		if (loc_assign == LOC_TYPE_INDEX['VOID']) or (loc_assign == LOC_TYPE_INDEX['PROC_FINISHED']):
			return#nothing to do
		assert(loc_assign not in LOC_TYPE_INDEX)#can't be an unassigned generic location edge_type

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
						# then this pixel is of the right edge_type, assign its location to be adjacent to us

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
				endx = x + self.PUBLIC_BLOCK_SIZE[0]
				endy = y + self.PUBLIC_BLOCK_SIZE[1]

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
		m = Map(self.loc_list,TIME_STEP_PER_PIXEL=self.TIME_STEP_PER_PIXEL)
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

	TIME_STEP_PER_PIXEL = 1  # how many time steps does it take to traverse 1 pixel?

	def __init__(self,loc_list,TIME_STEP_PER_PIXEL=None):

		self.loc_list = loc_list#list of locations, they each maintain their own adjacencies

		self.loc_map = {x.id:x for x in self.loc_list}

		self.avg_ages_assigned = False

		if TIME_STEP_PER_PIXEL is not None:
			self.TIME_STEP_PER_PIXEL = TIME_STEP_PER_PIXEL


	def get_location_by_loc_idx(self,lidx:int):
		return self.loc_map[lidx]

	'''
	give me a path I can use to go from a to b along the map
	
	uses dijkstra/uniform cost with A* manhattan heuristic, moving only on public spaces (the first move is to go from this location to the nearest public one
		h (parameter) is the heuristic function
	
	because the map isn't perfectly represented by such a heuristic, it's technically not admissable, so we're not guaranteed optimality. That doesn't really matter since we only really care that people get from point a to point b and not so much how fast it takes them but how much we spend doing the calculation (euclidean is at least closer to being admissable, but since it generally visits like 2x as many places, we're using manhattan)
	
	'''
	def get_path(self,a,b,h=MAP_OPTIMIZATION_FUNCTION,verbose=False):
		if a == b:
			return []#we're already there
		path = []
		current_loc = a
		pred = {a:None}#mapping of locations to their predecessors
		dist = {a:0}#mapping of locations to their distances
		if a.loc_type != 'public':#then find the/a public space adjacent to a
			for lj in a.adj_locs:
				if lj.loc_type == 'public':
					path.append(lj)
					current_loc = lj
					pred.update({current_loc:a})
					dist.update({current_loc:current_loc.travel_time})
					break
			if len(path) == 0:
				raise AttributeError("Location " + str(a) + " is not adjacent to a location of edge_type public.")


		tb = 1#tiebreaker for the heap
		nq = [(0,0,current_loc)]#priority queue (minheap) for visiting new locations
		b_heuristic_location = (b.mapx_center,b.mapy_center)
		visited = set()

		while len(nq) > 0:
			_, _, current_loc = hq.heappop(nq)
			if current_loc == b:
				#we're done here
				break
			visited.add(current_loc)

			if current_loc.loc_type == 'public':#we don't want to go *through* anything that isn't public
				for nloc in current_loc.adj_locs:
					#get its distance
					dist_n = dist[current_loc] + nloc.travel_time#simple edge distance <travel time>
					h_n = h((current_loc.mapx_center,current_loc.mapy_center),b_heuristic_location) * self.TIME_STEP_PER_PIXEL#heuristic
					cost_n = dist_n + h_n
					if ((nloc in pred) and ((dist[nloc] + h_n) > cost_n)) or (nloc not in pred):
						#add it to the heap
						hq.heappush(nq, (cost_n, tb, nloc))#put in the tiebreaker here so that if two cost_ns are the same we don't try to compare locations. priority goes, then, to earlier ones
						tb += 1
						pred.update({nloc:current_loc})
						dist.update({nloc:dist_n})

		#retrace the path
		current_loc = b
		rpath = []
		while current_loc != a:
			rpath.append(current_loc)
			current_loc = pred[current_loc]

		path = path + list(reversed(rpath))
		if verbose:
			print("calculated distance from " + str(a) + " to " + str(b) + " is " + str(dist[b]) + ", using " + str(len(path) - 2) + " public locations. visited " + str(len(visited)) + " locations to determine this.")
		return path

	'''
	returns a random nonfull location of edge_type t
	'''
	def get_random_location(self,t:str):
		for loc in self.loc_list:
			if (loc.loc_type == t) and (not loc.is_full()):
				return loc

	'''
	ok, so no school exists. we need to find one. ideally, we'll find one that already has enough capacity, 
	but if all the offices are too small, take the biggest one and make its capacity equal to the max size we 
	were given
	'''
	def create_school(self,max_size):
		office_max_idx = -1
		office_max_cap = -float('inf')
		office_min_over_spec_idx = -1  # the office which has the smallest capacity that is higher than max_size
		office_min_over_spec_cap = float('inf')
		for i, loc in enumerate(self.loc_list):
			if loc.loc_type == 'office':
				if (loc.capacity >= max_size) and (loc.capacity < office_min_over_spec_cap):  # then this one will do
					office_min_over_spec_idx = i
					office_min_over_spec_cap = loc.capacity
				if loc.capacity > office_max_cap:
					office_max_idx = i
					office_max_cap = loc.capacity

		if office_min_over_spec_idx != -1:  # then we already had a big enough one, use it
			self.loc_list[office_min_over_spec_idx].is_school = True
		else:  # use the biggest one
			assert (office_max_idx != -1)
			self.loc_list[office_max_idx].is_school = True
			self.loc_list[office_max_idx].capacity = max_size

	'''
	returns the unique school location (assigns it if it doesn't exist)
	'''
	def get_school(self):
		for loc in self.loc_list:
			if loc.is_school:
				return loc

		raise AttributeError("School was not created before having been asked for!")


	'''
	This is used when putting people on the map initially if they are homeless
	'''
	def arrive_at_random_nonfull_public_location(self,p):
		for loc in self.loc_list:
			if (loc.loc_type == 'public') and (loc.arrive(p)):
				return#side effects of loc.arrive are that the person is now at that location iff there was capacity for them

	'''
	this will return the list of workable locations as well to speed up computation
	'''
	def get_random_workable_location(self, workable = None):
		if workable is None:
			workable = list(filter(lambda x: x.loc_type in WORKABLE_LOCATION_TYPES, self.loc_list))

		return np.random.choice(workable), workable

	'''
	Given a distribution function () -> int, assign to each (relevant) location an average age
	as well as a distribution function () -> float for standard deviation
	'''
	def assign_avg_ages(self, ages_avg_distrib, ages_stdev_distrib):
		if self.avg_ages_assigned:
			return

		for loc in self.loc_list:
			if loc.loc_type in PLACABLE_LOCATION_TYPES:
				loc.avg_age = ages_avg_distrib()
				loc.age_stdev = ages_stdev_distrib()
		self.avg_ages_assigned = True

	'''
	use this person's age to find a random location relevant to them and assign it to them
	'''
	def add_random_placable_location(self,person,ages_avg_distrib,ages_stdev_distrib):
		self.assign_avg_ages(ages_avg_distrib,ages_stdev_distrib)

		np.random.shuffle(self.loc_list)#in random order
		loc_closest = self.loc_list[0]
		loc_closest_val = self.loc_list[0].age_prob(person.age)
		for loc in self.loc_list:
			if (loc.loc_type in PLACABLE_LOCATION_TYPES) and (loc not in person.places):#only considering valid values that aren't already in their places list
				if coinflip(loc.age_prob(person.age)):#with probability Norm(mu,sig), add this to the person's location
					#then this one is added
					person.add_place(loc)
					return
				else:
					this_val = loc.age_prob(person.age)
					if this_val > loc_closest_val:
						loc_closest = loc
						loc_closest_val = this_val

		person.add_place(loc_closest)#just add the one with the highest probability


	def get_random_house(self,houses=None):
		if houses is None:
			houses = list(filter(lambda x: x.loc_type == 'home', self.loc_list))

		hidx = np.random.choice(range(len(houses)))
		h = houses[hidx]
		while (h.is_full()) and (len(houses) > 1):
			del houses[hidx]
			hidx = np.random.choice(range(len(houses)))
			h = houses[hidx]

		return h,houses

	'''
	Find and return the nearest hospital to this person, given by h(x)
	'''
	def get_nearest_hospital(self,person,h = MAP_OPTIMIZATION_FUNCTION):
		person_loc = (person.currentLocation.mapx_center,person.currentLocation.mapy_center)
		min_dist = float('inf')
		min_loc = None
		for loc in self.loc_list:
			if loc.loc_type == 'hospital':
				hosp_loc = (loc.mapx_center,loc.mapy_center)
				hosp_dist = h(person_loc,hosp_loc)
				if hosp_dist < min_dist:
					min_dist = hosp_dist
					min_loc = loc
		return min_loc