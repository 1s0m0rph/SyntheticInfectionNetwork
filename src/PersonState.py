"""
this file contains all of the information relevant to the states people can be in (activity, location, etc.) as well as the person objects etc.
"""
"""
This part defines the "person" class and all of the relevant information.

Each person needs all of the following:

	home
	age
	currentLocation (defaults to home)
	currentActivity (defaults to Idle [see Activity.py])
	place of work\school* (from this we can infer distance to work/school and therefore travel time)
	work/school schedule*
	list of preferred activities (preferred in the sense that this person will do them; everyone who is either employed or at school will have Work in this list)*
	family
	partners (people who this person is likely to have sex with, there can be more than one)*
	friends*
	coworkers/schoolmates (that the person *actually* interacts with on a daily basis)*
	diseases currently inflicted with*
		symptoms shown (for each disease)
			any modifiers to behavior because of symptoms
	diseases immune to*
		possibly seperated by why (no for now)
			vaccine
			previous exposure
			etc

* - can be null or empty

___

note that the purpose of the friends/family/coworkers network is to tell the algorithm who you're *likely* to interact with.
a person is most likely to interact with their immediate friends and family, and as the network goes out in shells the probability decrases.
essentially, we're modeling the probability of interacting between two people as a decaying function of the geodesic distance between the people

"""
import numpy as np
import re

#TODO: move these constants to the simulation util
TIME_STEPS_PER_DAY = 1440#for minutes

"""
Given a "time string" (HH:MM:SS, HH:MM, or just HH), convert that string into the equivalent number of time steps after midnight
"""
def tconv(tst: str):
	hhmmss = re.match(r'([0-9]{1,2}):([0-9]{1,2}):([0-9]{1,2})',tst)
	hhmm = re.match(r'([0-9]{1,2}):([0-9]{1,2})', tst)
	hh = re.match(r'([0-9]{1,2})', tst)
	h = 0.
	m = 0.
	s = 0.
	if hhmmss:
		h = float(hhmmss.group(1))
		m = float(hhmmss.group(2))
		s = float(hhmmss.group(3))
	elif hhmm:
		h = float(hhmm.group(1))
		m = float(hhmm.group(2))
	elif hh:
		h = float(hh.group(1))
	else:
		raise AttributeError('time string ' + tst + ' is not of the format HH:MM:SS, HH:MM, or HH')

	return int((TIME_STEPS_PER_DAY / 24.)*h + (TIME_STEPS_PER_DAY / 1440.)*m + (TIME_STEPS_PER_DAY / 86400.)*s)

class Person:
	PERSON_ID_COUNTER = 0  # used for comparisons of equality between person objects

	"""
	We only require that each person has a home. If that's all they have they never actually leave except to go to the store to get food.
	"""
	def __init__(self, home, age: int):
		# general demo/biographical info
		self.id = Person.PERSON_ID_COUNTER
		Person.PERSON_ID_COUNTER += 1
		self.home = home
		self.age = age
		self.currentLocation = None
		self.set_current_location(home)
		if self.currentLocation is None:
			self.set_current_location(public)
		self.currentActivity = Activity('idle')
		self.workplace = None  # or school
		self.work_schedule = None #2-tuple of time -- when I'm at "work"
		self.sleep_schedule = (tconv('22'),tconv('8'))# we assume, in general, everyone is asleep between 10pm and 8am
		self.activities = []
		self.family = [] #immediate family only -- parents and children
		self.partners = [] #people this person might interact with sexually
		self.friends = []
		self.coworkers = []  # or schoolmates

		# infection info
		self.diseasesInfectedBy = []
		self.immunities = []

		#behavior info
		self.hand_wash_coef = 0#given that I'm interacting with someone, what's the probability I've washed my hands first?
		self.disease_affinity_mod = 0#how much less likely am I to interact with someone given that I'm infected by *some* disease

	def __repr__(self):
		return "Person " + str(self.id)

	"""
	set our location to this and notify that location that we have arrived (also notify our current one that we are leaving), do not change location if the new location is full
	"""
	def set_current_location(self,loc):
		loc.arrive(self)

	"""
	Assign an affinity score between me and this person
	essentially, it's how likely we are to interact, assuming we're in the same place
	"""
	def affinity(self,person):
		if self.currentLocation != person.currentLocation:
			return 0#no affinity if we can't interact
		is_partner = person in self.partners
		if is_partner:
			return max(0,0.9 - (self.disease_affinity_mod if len(self.diseasesInfectedBy) > 0 else 0))#we like to interact with our partners

		rolling_prob = 0.
		cw_dist = calc_bfs_dist(self,'work', person)#distance on the coworker network
		fr_dist = calc_bfs_dist(self,'friend',person)#distance on the friend network
		fam_dist = calc_bfs_dist(self,'family',person)#distance on the family network
		is_friend_first = fr_dist <= cw_dist#I see this person more as a friend than as a coworker
		is_family_first = fam_dist <= fr_dist#I see this person more as family than as a friend (family-to-coworker relations are irrelevant)

		if self.currentLocation == self.workplace:
			#figure out how far apart these two are in the coworker network using bfs

			cw_aff = aff_decay(0.7,0.1)(cw_dist)#70% chance to interact with a direct coworker, 10% chance with a coworker-of-a-coworker. exp decay from there
			rolling_prob += cw_aff
			if is_family_first:
				fam_aff = -aff_decay(0.3,0.05)(fam_dist)
				rolling_prob = weighted_prob_combination(rolling_prob,0.75,fam_aff,0.25)
			if is_friend_first:
				fr_aff = aff_decay(0.75,0.2)(fr_dist)
				rolling_prob = weighted_prob_combination(rolling_prob,0.6,fr_aff,0.4)
		else:
			fr_aff = aff_decay(0.9,0.2)(fr_dist)
			rolling_prob += fr_aff
			if not is_friend_first:
				#we don't actually want to interact with them -- this is a negative
				cw_aff = -aff_decay(0.6,0.1)(cw_dist)
				to_add = max(0, weighted_prob_combination(rolling_prob,0.8,cw_aff,0.2))
				rolling_prob = to_add
			elif is_family_first:
				fam_aff = aff_decay(0.75,0.25)(fam_dist)
				rolling_prob = weighted_prob_combination(rolling_prob,0.5,fam_aff,0.5)

		return max(0,rolling_prob - (self.disease_affinity_mod if len(self.diseasesInfectedBy) > 0 else 0))

	"""
	"perform" the current action, if that requires anything
	
	if we're interacting with someone, diseases might be transferred
	if we're going somewhere, we need to actually move
	"""
	def do_current_action(self):
		if self.currentActivity.activity_type == 'traveling':#then we need to update our coords in the right direction
			self.currentLocation = self.currentActivity.path.pop()#get the next location we travel through to get where we're going


	"""
	Knowing what time it is, what are the states I could transition to, and with what probability? Pick one from those with those probabilites and do it
	"""
	def action_transition(self,time):
		#social info
		people_here = self.currentLocation.people #who is actually here right now that I might go talk to?
		affinities = [self.affinity(x) for x in people_here if x != self]


		#temporal info
		if self.work_schedule is not None:
			during_work_time = time_within_tuple(time,self.work_schedule)
		else:
			during_work_time = False

		during_sleep_time = time_within_tuple(time,self.sleep_schedule)

		if during_sleep_time:
			if self.currentActivity.activity_type == 'sleep':
				return#don't do anything

			if self.currentLocation == self.home:
				self.currentActivity = Activity('sleep')#go to sleep
				return

			#we're not at home and we're not asleep, but we should be
			if (self.currentActivity.activity_type == 'traveling') and (self.currentActivity.to == self.home):
				return#we're already doing it
			#go home
			if self.currentLocation.loc_type != 'public':
				self.set_current_location(public)
				#TODO: set our coordinates to be the nearest "public" ones
			self.currentActivity = Activity('traveling')
			#TODO: precalculate travel path
			self.currentActivity.to = self.home



"""
e^(-rate * (x - 1)) * level_one

level_one is the probability if x = 1
level_two is the probability if x = 2
from these we deduce a decay rate rate such that this equation goes through those points.

rate = -ln(level_two / level_one)

simplified, we get that f(x) = ((level_one^2) * (level_two / level_one)^x) / level_two
"""
def aff_decay(level_one, level_two):
	return lambda x: ((level_one ** 2) * (level_two / level_one) ** x) / level_two


"""
Combine these probabilities into a unified one depending on given weights which should sum to 1 in general
"""
def weighted_prob_combination(p1,w1,p2,w2):
	return p1*w1 + p2*w2


"""
do a social network bfs either on the coworkers network, the family network, or the friends network

all we care about is how far apart we and the target are in this network
"""
def calc_bfs_dist(start, type, target_person):
	if start == target_person:
		return 0#why did this even get called?

	pq = []  # queue for bfs
	current = start  # starting from me
	contflag = True
	dist_map = {start:0}
	retdist = -1# standin for infinity -- they're not in this connected component

	while contflag:

		# figure out what type of neighbors we are looking for
		if type == 'work':
			neighbors = current.coworkers
		elif type == 'friend':
			neighbors = current.friends
		elif type == 'family':
			neighbors = current.family#problematic due to the different types of fam
		else:
			raise AttributeError("Illegal argument to calc_bfs_dist, type should be work, family, or friend, not " + str(type))

		for n in neighbors:
			if not n in dist_map:  # then this node hasn't been seen yet
				if n.id == target_person.id:
					retdist = dist_map[current]+1#ladies and gentlemen, we got 'em
					break
				dist_map.update({n:dist_map[current]+1})
				pq.append(n)  # add n to the queue

		if (len(pq) == 0) or (retdist != -1):
			contflag = False
		else:
			current = pq.pop(0)

	return float('inf') if retdist == -1 else retdist


"""
Tests whether the given time lies between the given times

times are all in minutes past midnight, with a max value of 23*60 + 59 =  1439
"""
def time_within_tuple(time,tup):
	assert(time < TIME_STEPS_PER_DAY)
	assert(tup[0] < TIME_STEPS_PER_DAY)
	assert(tup[1] < TIME_STEPS_PER_DAY)
	assert(time >= 0)
	assert(tup[0] >= 0)
	assert(tup[1] >= 0)
	#preconditions ^^

	if tup[0] > tup[1]:#then this tuple spans the midnight hour
		return (time >= tup[0]) or (time <= tup[1])

	return (time >= tup[0]) and (time <= tup[1])


"""
This part contains all of the information on different locations -- homes, workplaces, entertainment centers, stores, schools, etc.

At any given time t a location has a list of people currently at the location, which can of course be empty.
"""

LOCATION_TYPES = [
	'home',#where people live, generally (exceptions exist) [brown on map]
	'office',#a place that can only be visited by employees (includes schools) [pink on map]
	'convention',#a large gathering area (stadium convention center, etc.) for many people *some of whom may be outside of this city*  --> introduction vector (activity, not location) [lime green on map]
	'shop',#any kind of place that can be entered by both employees and general people (includes restaurants etc.) [blue on map]
	'public',#streets, plazas, parks -- anything that anyone can visit and no one can work at [black on map]
	'hospital',#where the sick people be (technically a type of shop, but it's important enough to exist on its own) [red on map]
]

class Location:

	"""
	capacity indicates how many people the location can contain at most
	type is mostly for convenience so we know what kind of location it is:
		'spectator' (theater/sports event/concert/movie theater), 'convention', 'restaurant', 'shop', 'public' (park, town square; this will be used to move people between other locations), 'casino' ,
		'home', 'school', 'vehicle'
	"""
	def __init__(self,capacity,loc_type):
		self.people = []
		self.capacity = capacity
		self.loc_type = loc_type


		#TODO: potential additions?
		#map (x,y) coordinates (list of points that define a polygon describing its edges)
		#these points should define a walk that starts from the first one and implicitly ends back at the first one
		#e.g. [(0,0),(0,1),(1,1),(1,0)] describes the unit square
		self.mapcoords = []
		self.mapcenterx = -1#center of this object on the map
		self.mapcentery = -1

	def arrive(self,p: Person):
		if len(self.people) >= self.capacity:#we can't take this person on, reject them
			return

		if p.currentLocation is not None:
			p.currentLocation.people.remove(p)
		self.people.append(p)
		p.currentLocation = self


"""
This part contains all of the information relevant to activities that people can do.

Exactly what activity a certain person is doing will be modeled as a markov chain with transition probabilities from activity a1 to a2 dependent on
	a1, a2
	the person (+ personal variables like work schedule etc.)
	where the person is
	who else is there
	current time

possible activities are somewhat dependent on location (eg you can work anywhere (since anywhere can be a workplace) but you can only sleep at your "home")

activities:
	Idle
	Sleep
	Working
	Walking
	Commuting (via public transport or car)
	abstract, not really existent: InteractingWith (another person)
		SocialTalking (reasonable distance)
		PersonalTalking (somewhat closeish)
		IntimateTalking (very personal conversation)
		Touching (catch-all for any situation where you might touch someone -- dancing, shaking hands, etc.)
		IntimateTouching (catch-all for any intimate behaviors such as intercourse -- especially relevant for STDs)



"""

ACTIVITY_TYPES = [
	'idle',
	'sleep',
	'working',
	'traveling',#everyone walks, we assume
	'talking',
	'touching',
	'intimateTouching'#very important for certain diseases like stds
]

VALID_LOCATIONS = {
	'idle':LOCATION_TYPES,
	'sleep':['home'],
	'working':LOCATION_TYPES.copy().remove('public'),#anything can be a workplace except public
	'traveling':['public'],
	'talking':LOCATION_TYPES,
	'touching':LOCATION_TYPES,
	'intimateTouching':'home'
}

class Activity:

	def __init__(self,atype):
		self.valid_locations = VALID_LOCATIONS[atype]#where can this activity happen?
		# self.timeDoing = 0#how long have I been doing this?
		#what is the probability, in general, that someone goes from this activity to any of the others; mapping from activity str to double in [0,1]
		#this is the probability if we consider ONLY the activity and not the location or the person etc.
		# self.transition_probabilities = dict(zip(self.ACTIVITY_TYPES,[0 for _ in range(len(self.ACTIVITY_TYPES))]))
		self.activity_type = atype

		#if this is an action like walking, we need to know where we're going
		#similarly, if we're talking to someone, we need to know who (these take up the same variable because they're mutually exclusive)
		self.to = None#type = Location or Person
		self.path = []#travel path should be precalculated; consists of locations that we will visit on the way (this means public locations need to be split up into a network of small public locations)

	def __repr__(self):
		return self.activity_type

#static "public" location
public = Location(float('inf'),'public')#TODO: make this inherited from the general simulation/utils