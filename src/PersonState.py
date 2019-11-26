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
import random as rnd
import re
from SINUtil import *


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

	from Map import Map

	"""
	We only require that each person has a home. If that's all they have they never actually leave except to go to the store to get food.
	"""
	def __init__(self, home, M:Map):
		# general demo/biographical info
		self.id = Person.PERSON_ID_COUNTER
		Person.PERSON_ID_COUNTER += 1
		self.home = home
		if home is not None:
			self.currentLocation = None
			self.set_current_location(home)
			if self.currentLocation is None:
				raise AttributeError(str(self) + "'s home does not have enough capacity for all its inhabitants.")
		else:
			#this person is homeless, so plonk them down some random public place
			self.currentLocation = M.arrive_at_random_nonfull_public_location(self)

		self.currentActivity = Activity('idle')
		self.age = -1
		self.workplace = None  # or school
		self.work_schedule = None #2-tuple of time -- when I'm at "work"
		self.sleep_schedule = (tconv('22'),tconv('8'))# we assume, in general, everyone is asleep between 10pm and 8am
		self.places = []#where do I like to go in my free time
		self.family = [] #immediate family only -- parents and children
		self.partners = [] #people this person might interact with sexually
		self.friends = []
		self.coworkers = []  # or schoolmates

		# infection info
		self.disease_state = {}	#mapping of disease ids onto disease states
		self.diseasesShowingSymptoms = False

		#behavior info
		self.hand_wash_coef = 0#given that I'm interacting with someone, what's the probability I've washed my hands first?
		self.disease_affinity_mod = 0#how much less likely am I to interact with someone given that I'm infected by *some* disease
		self.diseasesVaccinatable = {}#set of diseases for which I can (or am willing to) be vaccinated for

		#map info
		self.M = M

	def __repr__(self):
		return "Person " + str(self.id)

	def set_workplace(self,wp):
		if self.home is not None:#assumption is that homeless people do not have jobs
			self.workplace = wp

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
			return max(0.,0.9 - (self.disease_affinity_mod if self.diseasesShowingSymptoms else 0.))#we like to interact with our partners

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

		return max(0,rolling_prob - (self.disease_affinity_mod if self.diseasesShowingSymptoms else 0))

	"""
	"perform" the current action, if that requires anything
	
	if we're interacting with someone, diseases might be transferred
	if we're going somewhere, we need to actually move
	"""
	def do_current_action(self):
		if self.currentActivity.activity_type == 'traveling':#then we need to update our coords in the right direction
			self.currentLocation = self.currentActivity.path.pop()#get the next location we travel through to get where we're going

		elif self.currentActivity.activity_type == 'talking':
			pass#TODO: infection logic here?

		self.currentActivity.time_doing += 1  # we have now been doing this for one time step


	"""
	figure out, based on affinity, who (if anyone) I should talk to
	"""
	def talk_to(self):
		people_here = [x for x in self.currentLocation.people if x != self]  # who is actually here right now that I might go talk to? (not including myself, then)
		affinities = [self.affinity(x) for x in people_here]

		ph_sort = list(zip(people_here.copy(),affinities.copy()))
		#TODO: figure out if stochastic sorting this makes sense
		ph_sort = stoch_sort(ph_sort,SSORT_LEVELS,lambda x,y: x[1] > y[1])#descending stochastic sort the affinities list

		#now go down that list and flip a biased coin for everyone. if heads, return them, otherwise return nothing
		for p,aff in ph_sort:
			if rnd.random() < aff:
				#we have a winner
				#just go ahead and create the activity object
				act = Activity('talking')
				act.to = p
				#also set the other participant
				act2 = Activity('talking')
				act2.to = self
				p.currentActivity = act2
				return act#we have a winner

		return Activity('idle')#no one here to talk to

	"""
	do the activity given by the transition
	"""
	def action_transition(self,time):
		self.currentActivity = self.get_action_transition(time)


	def go_to(self,place):
		assert(place is not None)

		if self.currentLocation == place:
			return Activity('idle')#we're already there

		if (self.currentActivity.activity_type == 'traveling') and (self.currentActivity.to == place):
			return self.currentActivity  # we're already going there

		act = Activity('traveling')
		#get the path from the map
		path = self.M.get_path(self.currentLocation,place)

		act.to = place
		act.path = path
		return act


	"""
	Pick a random place to travel to
	
	done according to the mdp rules -- i.e. to the place in our list with the higest average affinity for its current clientele
	"""
	def pick_rtravel_loc(self):
		#with probability dependent on if we're currently showing symptoms and our disease modifier, go home instead
		hyg_prob = self.disease_affinity_mod if self.diseasesShowingSymptoms else 0
		if np.random.choice([True,False],[hyg_prob,1-hyg_prob]):
			return self.home

		#otherwise, carry on
		locs = self.places
		best_loc = None
		best_aff = -float('inf')
		for loc in locs:
			#get this place's average affinity
			avg_aff = np.mean([self.affinity(p) for p in loc.people])
			if avg_aff > best_aff:
				best_aff = avg_aff
				best_loc = loc
		return best_loc

	def continue_interaction(self):
		# stop with probability (1 - affinity with this person)
		aff = self.affinity(self.currentActivity.to)
		if rnd.random() < aff:  # continue with probability aff
			return self.currentActivity
		else:  # stop with prob 1 - aff
			#reset the other person's activity too
			self.currentActivity.to.currentActivity = Activity('idle')
			return Activity('idle')

	"""
	Knowing what time it is, what are the states I could transition to, and with what probability? Pick one from those with those probabilites and return it
	"""
	def get_action_transition(self,time):
		#temporal info
		if self.work_schedule is not None:
			during_work_time = time_within_tuple(time,self.work_schedule)
		else:
			during_work_time = False

		during_sleep_time = time_within_tuple(time,self.sleep_schedule)

		#going to bed logic
		if during_sleep_time:
			if self.currentActivity.activity_type == 'sleep':
				return self.currentActivity#don't do anything

			if self.currentLocation == self.home:
				return Activity('sleep')#go to sleep

			#we're not at home and we're not asleep, but we should be
			#go home
			return self.go_to(self.home)


		#going to work logic
		if during_work_time and (self.workplace is not None):
			if self.currentLocation != self.workplace:
				if not ((self.currentActivity.activity_type == 'traveling') and (self.currentActivity.to == self.workplace)):
					# go there
					return self.go_to(self.workplace)

		#so we're where we're supposed to be and doing what we ought to be doing
		#should we change what we're doing?


		#part 1: at work
		if self.currentLocation == self.workplace:
			#traveling at the end of the work day
			if not during_work_time:
				# go home
				return self.go_to(self.home)

			#are we talking to someone?
			if self.currentActivity.activity_type == 'talking':
				return self.continue_interaction()

			#otherwise, should we talk to someone?
			talk = rnd.random() < 0.5
			if talk:
				return self.talk_to()
			else:
				return Activity('idle')

		#part 2: at home
		if self.currentLocation == self.home:
			if self.currentActivity.activity_type == 'idle':
				#we can do: traveling, talking, intimate, (idle), in general, but those have particular conditions
				#which can we actually do?
				possible_actions = ['idle','talking','intimate','traveling']

				#pick one at random and try to do it, if we can't remove it from the set and try another
				act_do = np.random.choice(possible_actions)
				while len(possible_actions) > 0:#idle and talking never get removed, so it won't ever reach zero but safety
					#do the action
					if act_do == 'idle':
						return Activity('idle')
					elif act_do == 'talking':
						return self.talk_to()
					elif act_do == 'intimate':
						people_here = self.currentLocation.people
						parts_here = list(set(self.partners).intersection(set(people_here)))
						if len(parts_here) != 0:
							#just assume we boink a random one
							b = np.random.choice(parts_here)
							act = Activity('intimate')
							act.to = b
							act2 = Activity('intimate')
							act2.to = self
							b.currentActivity = act2
							return act
						possible_actions.remove('intimate')#nevermind then
						act_do = np.random.choice(possible_actions)
					elif act_do == 'traveling':
						if len(self.places) != 0:
							return self.go_to(self.pick_rtravel_loc())
						possible_actions.remove('traveling')#nevermind then
						act_do = np.random.choice(possible_actions)
			else:
				#action stops
				if (self.currentActivity.activity_type == 'talking') or (self.currentActivity.activity_type == 'intimate'):
					return self.continue_interaction()
				else:
					raise AttributeError("massive wat -- we can't be traveling and be at home, this should never happen")

		#part 3: at a hospital
		if self.currentLocation.loc_type == 'hospital':
			#we know we don't work here since the workplace logic comes before this, but do a sanity check anyway
			if self.currentLocation != self.workplace:
				if not self.diseasesShowingSymptoms:
					#go home
					return self.go_to(self.home)
				else:
					# are we talking to someone?
					if self.currentActivity.activity_type == 'talking':
						return self.continue_interaction()#doesn't always happen

					# otherwise, should we talk to someone?
					talk = rnd.random() < 0.5
					if talk:
						return self.talk_to()
					else:
						return Activity('idle')
			else:
				raise AttributeError('This should never happen: ' + str(self) + ' works at a hospital')

		#part 4: in public
		if self.currentLocation.loc_type == 'public':
			#sanity check
			if self.currentActivity.activity_type == 'traveling':
				#keep on truckin
				return self.currentActivity
			#else we just act like a normal location

		#part 5: everything else
		if self.currentActivity.activity_type == 'idle':
			# we can do: traveling, talking, (idle), in general, but those have particular conditions
			# which can we actually do?
			possible_actions = ['idle', 'talking', 'traveling']

			# pick one at random and try to do it, if we can't remove it from the set and try another
			act_do = np.random.choice(possible_actions)
			while len(possible_actions) >= 0:
				# do the action
				if act_do == 'idle':
					return Activity('idle')
				elif act_do == 'talking':
					return self.talk_to()
				elif act_do == 'traveling':
					if len(self.places) != 0:
						return self.go_to(self.pick_rtravel_loc())
					possible_actions.remove('traveling')
					act_do = np.random.choice(possible_actions)
		else:
			# action stops
			if self.currentActivity.activity_type == 'talking':
				return self.continue_interaction()
			else:
				raise AttributeError("massive wat -- we can't be traveling and be not in public, this should never happen")

		raise AttributeError("Somehow we didn't pick a transition... this should never happen, but " + str(self) + " has nothing to do!")



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
A class which allows for the creation of populations of people, along with all of their parameters, including the social networks

In order to do this, we need:
	a map
	the number of people to generate
	the average number of friends f_hat
	average number of coworkers c_hat
	age distribution
	average number of preferred locations (Person.places)
	probability of homelessness
	hygiene distribution
	proportion of population with partners (probability that a given person has a partner)
	the maximum number of people to generate that are in school
"""
class PopulationBuilder:

	from Map import Map

	def __init__(self):
		#defined by the user
		self.M = None
		self.N = -1
		self.fh = -1
		self.ch = -1
		self.age_dist = None			#function from () -> int
		self.school_range = None		#tuple of ages, between which people are in school (e.g. (0,18) means everyone from age 0 to age 18 is in school)
		self.avg_places = -1
		self.homeless_prob = -1
		self.hygiene_dist = None 		#this should be a function that, when queried gives a hygiene
		self.prob_has_partner = -1
		self.max_school_size = 0


		#logical variables
		self.current_school_people = 0	#how many people are currently in school


	def set_map(self,M:Map):
		self.M = M

	def set_N(self,N:int):
		self.N = N

	def set_avg_friends(self,fh:float):
		self.fh = fh

	def set_avg_coworkers(self,ch:float):
		self.ch = ch

	def set_age_distribution(self,ad):
		self.age_dist = ad

	def set_average_preferred_locations(self,avg_places:float):
		self.avg_places = avg_places

	def set_homeless_probability(self,hp:float):
		self.homeless_prob = hp

	def set_hygiene_distribution(self,hd):
		self.hygiene_dist = hd

	def set_has_partner_probability(self,hpp:float):
		self.prob_has_partner = hpp

	def set_school_age_range(self,sar:tuple):
		self.school_range = sar

	def set_max_people_in_school(self,s:int):
		self.max_school_size = s


	"""
	Assign all of the primitive details randomly to this person (they already need to have a home)
		age
		workplace
		places
	"""
	def assign_primitive_details(self,p:Person):
		p.age = self.age_dist()
		if (p.age >= self.school_range[0]) and (p.age <= self.school_range[1]):
			if self.current_school_people >= self.max_school_size:
				#then we already have enough school people, add the oldest school age to this to make sure this person isn't in school
				p.age += self.school_range[1]
			else:
				#age is valid now
				#then this person is in school
				p.workplace = self.M.get_school(self.max_school_size)


		#TODO: finish the assign primitive details function


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

	LOCATION_ID_COUNTER = 0#for giving unique IDs to locations

	"""
	capacity indicates how many people the location can contain at most
	type is mostly for convenience so we know what kind of location it is
	"""
	def __init__(self,loc_type,capacity=-1):
		self.people = []
		self.capacity = capacity
		self.loc_type = loc_type
		self.id = Location.LOCATION_ID_COUNTER
		Location.LOCATION_ID_COUNTER += 1
		self.is_school = False

		self.adj_locs = set()#what locations are adjacent to me?
		self.travel_time = -1#how long does it take to travel through me? this will be proportional to size

		#these are only used for heuristics, and refer to the center of the object on the map
		self.mapx_center = -1
		self.mapy_center = -1


	def arrive(self,p: Person):
		if len(self.people) >= self.capacity:#we can't take this person on, reject them
			return False

		if p.currentLocation is not None:
			p.currentLocation.people.remove(p)
		self.people.append(p)
		p.currentLocation = self
		return True

	"""
	Do a round of infections with the people here now
	
	for each pair of people (a,b):
		for each disease d a is infected by:
			ask d if a infects b
			if yes, add (a,d,b) to the infections set
		for each disease d b is infected by:
			ask d if b infects a
			if yes, add (b,d,a) to the infections set
	
	return infections set (logic above this will actually do the infections so it's entirely synchronous per time step)
	
	"""
	def infection_round(self):
		# TODO: insert logic for infections in the general simulation code to wrap this
		rset = set()
		for a in self.people:
			for b in self.people:
				if a != b:
					for d_id in a.disease_state:
						if diseases_active[d_id].infects(a,b):
							rset.add((a,d_id,b))
					for d_id in b.disease_state:
						if diseases_active[d_id].infects(b,a):
							rset.add((b,d_id,a))
		return rset

	def __repr__(self):
		return 'Location of type ' + self.loc_type + ' with id ' + str(self.id)


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
	'idle',#anything that isn't described below, eg. working, doing homework, playing a game, whatever
	'sleep',#we can't interact with anyone, we can't be infected
	'traveling',#everyone walks, we assume
	'talking',#we are interacting with someone in a non-intimate way
	'intimate'#very important for certain diseases like stds
]

VALID_LOCATIONS = {
	'idle':LOCATION_TYPES,
	'sleep':['home'],
	'traveling':['public'],
	'talking':LOCATION_TYPES,
	'intimate':'home'
}

class Activity:

	def __init__(self,atype):
		self.valid_locations = VALID_LOCATIONS[atype]#where can this activity happen?
		# self.timeDoing = 0#how long have I been doing this?
		#what is the probability, in general, that someone goes from this activity to any of the others; mapping from activity str to double in [0,1]
		#this is the probability if we consider ONLY the activity and not the location or the person etc.
		# self.transition_probabilities = dict(zip(self.ACTIVITY_TYPES,[0 for _ in range(len(self.ACTIVITY_TYPES))]))
		self.activity_type = atype
		self.time_doing = 0#how long has the person been doing this?

		#if this is an action like walking, we need to know where we're going
		#similarly, if we're talking to someone, we need to know who (these take up the same variable because they're mutually exclusive)
		self.to = None#type = Location or Person
		self.path = []#travel path should be precalculated; consists of locations that we will visit on the way (this means public locations need to be split up into a network of small public locations)

	def __repr__(self):
		return 'Activity of type ' + self.activity_type + ('' if self.to is None else ' (to ' + str(self.to) + ')')
