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
from SINUtil import *


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
		self.home = None
		self.set_home(home)
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
		self.places = set()#where do I like to go in my free time
		self.partners = set() #people this person might interact with sexually
		self.friends = set()
		self.coworkers = set()  # or schoolmates
		self.is_dead = False
		self.healthiness = 0.

		# infection info
		self.disease_state = {}	#mapping of diseases onto what state I'm in for them (all need to be present in this list)
		self.infected_by = {}	#mapping of diseases onto the people that infected me for them
		self.diseasesShowingSymptoms = False
		self.idle_infection_count = 0

		#behavior info
		self.hygiene_coef = 0#given that I'm interacting with someone, what's the probability I've washed my hands first?

		#map info
		self.M = M

		#movement info
		self.travel_counter = 0	#how many time steps have we spent in the current location on our way to the destination?

	def __repr__(self):
		return "Person " + str(self.id)

	def get_effective_healthiness(self) -> float:
		disease_mod = 0.
		if self.diseasesShowingSymptoms:
			#then take the worst one and subtract its health modifier from our healthiness
			disease_mod = max(map(lambda x: x.symptom_health_effect,self.disease_state.keys()))

		return max(0.,self.healthiness - disease_mod)

	def any_infection_present(self):
		for disease in self.disease_state:
			if self.disease_state[disease] in DISEASE_STATES_INFECTIOUS:
				return True
		return False

	def set_workplace(self,wp):
		if self.workplace is not None:
			#unset it
			self.workplace.employees_residents.remove(self)
		if (self.home is not None) and (wp is not None):#assumption is that homeless people do not have jobs
			self.workplace = wp
			self.workplace.employees_residents.add(self)

	def add_place(self,place):
		if place is not None:
			self.places.add(place)
			place.clientele.add(self)

	def set_home(self,loc):
		if self.home is not None:
			#unset it
			self.home.employees_residents.remove(self)
			self.home.clientele.remove(self)
		if loc is not None:
			self.home = loc
			self.home.employees_residents.add(self)
			self.home.clientele.add(self)

	def die(self):
		self.is_dead = True
		self.set_home(None)
		self.set_workplace(None)
		for loc in self.places:
			loc.clientele.remove(self)
		# self.currentLocation = None	#leave this for now, since we want to know where people are when they die

	"""
	set our location to this and notify that location that we have arrived (also notify our current one that we are leaving), do not change location if the new location is full
	"""
	def set_current_location(self,loc):
		loc.arrive(self)

	"""
	do the general cleanup things at the beginning of the day (check for recovery/death/etc)
	"""
	def day_begin(self):
		if self.is_dead:
			return

		for disease in self.disease_state:
			disease.disease_state_transition(self)

	"""
	Assign an affinity score between me and this person
	essentially, it's how likely we are to interact, assuming we're in the same place
	"""
	def affinity(self,person):
		if self.currentLocation != person.currentLocation:
			return 0#no affinity if we can't interact
		is_partner = person in self.partners
		if is_partner:
			return max(0., 0.8 - (self.hygiene_coef if self.diseasesShowingSymptoms else 0.))#we like to interact with our partners

		rolling_prob = 0.
		cw_dist = calc_bfs_dist(self,'work', person)#distance on the coworker network
		fr_dist = calc_bfs_dist(self,'friend',person)#distance on the friend network
		is_friend_first = fr_dist <= cw_dist#I see this person more as a friend than as a coworker

		if self.currentLocation == self.workplace:
			#figure out how far apart these two are in the coworker network using bfs

			cw_aff = aff_decay(0.7,0.1)(cw_dist)#70% chance to interact with a direct coworker, 10% chance with a coworker-of-a-coworker. exp decay from there
			rolling_prob += cw_aff
			if is_friend_first:
				fr_aff = aff_decay(0.75,0.2)(fr_dist)
				rolling_prob = weighted_prob_combination(rolling_prob,0.6,fr_aff,0.4)
		else:
			fr_aff = aff_decay(0.8,0.2)(fr_dist)
			rolling_prob += fr_aff
			if not is_friend_first:
				#we don't actually want to interact with them -- this is a negative
				cw_aff = -aff_decay(0.6,0.1)(cw_dist)
				to_add = max(0, weighted_prob_combination(rolling_prob,0.8,cw_aff,0.2))
				rolling_prob = to_add

		semifinal = max(0, rolling_prob - (self.hygiene_coef if self.diseasesShowingSymptoms else 0))
		return min(semifinal + INTERACTION_EXPLORATION_REWARD,1)

	"""
	"perform" the current action, if that requires anything
	
	if we're interacting with someone, diseases might be transferred
	if we're going somewhere, we need to actually move
	"""
	def do_current_action(self):
		if self.is_dead:
			return 0	#dead people don't do anything
		if self.currentActivity.activity_type == 'traveling':#then we need to update our coords in the right direction
			if self.travel_counter >= self.currentLocation.travel_time:
				self.set_current_location(self.currentActivity.path.pop())#get the next location we travel through to get where we're going
				#^^^ really important we *set* the location here so that it registers us as being there
				if self.currentLocation == self.currentActivity.to:#then we've arrived, go idle
					self.currentActivity = Activity('idle')
					return 0
			else:
				self.travel_counter += 1

		elif (self.currentActivity.activity_type == 'talking') or (self.currentActivity.activity_type == 'intimate'):
			#since we're interacting with someone, we should check for infections here
			infections = 0
			for disease in self.disease_state:
				if disease.infects(self, self.currentActivity.to):
					self.currentActivity.to.infected_by.update({disease:self})#let this person know who infected them with this disease
					disease.infect(self.currentActivity.to)
					infections += 1
				#this will be called on everyone, so there's no need to check if the other person infects me now
			return infections

		return 0


	"""
	figure out, based on affinity, who (if anyone) I should talk to
	"""
	def talk_to(self):
		if self.is_dead:
			return None
		#using this opportunity to check for idle infections
		if DISABLE_IDLE_INFECTION:
			people_here = [x for x in self.currentLocation.people if x != self]
		else:
			people_here = []
			for x in self.currentLocation.people:
				if x != self:
					people_here.append(x)
					#now check for idle infections
					self.idle_infection_count = 0
					for disease in self.disease_state:
						if disease.infects(self,x):
							x.infected_by.update({disease:self})
							disease.infect(x)
							self.idle_infection_count += 1
						if disease.infects(x,self):
							self.infected_by.update({disease: x})
							disease.infect(self)
							self.idle_infection_count += 1
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
		if self.is_dead:
			return
		self.currentActivity = self.get_action_transition(time)


	def go_to(self,place):
		if self.is_dead:
			return None
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
		if self.is_dead:
			return None
		#with probability dependent on if we're currently showing symptoms and our disease modifier, go home instead
		hyg_prob = self.hygiene_coef if self.diseasesShowingSymptoms else 0
		if coinflip(hyg_prob):
			return self.home

		#otherwise, carry on
		locs = self.places
		best_loc = self.currentLocation
		best_aff = np.mean([self.affinity(p) for p in self.currentLocation.people])
		for loc in locs:
			if (not loc.is_empty) and (loc != best_loc):
				#get this place's average affinity
				avg_aff = np.mean([self.affinity(p) for p in loc.people])
				if avg_aff > best_aff:
					best_aff = avg_aff
					best_loc = loc
		return best_loc

	def continue_interaction(self):
		if self.is_dead:
			return None
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
		if self.is_dead:
			return None
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

		#part 0: sickness -> go to hospital?
		#this should take precedence over going to work, but not over going to bed

		if self.diseasesShowingSymptoms:
			go_to_hospital = coinflip(weighted_prob_combination(self.hygiene_coef, 0.5, 1 - self.get_effective_healthiness(), 0.5))
			#we go to the hospital with a probability averaged on my hygiene coefficient (more hygeneous == more likely to go to the hospital) and my effective healthiness (worse disease make me feel worse and so I'm more likely to go to the hospital)
			if go_to_hospital:
				#then go to the closest hospital
				hosp = self.M.get_nearest_hospital(self)
				return self.go_to(hosp)
		#otherwise, it's fine, we'll keep on keepin on


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
			talk = coinflip(GENERAL_TALK_PROBABILITY)
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
					return self.currentActivity	#still traveling

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
					talk = coinflip(GENERAL_TALK_PROBABILITY)
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
def calc_bfs_dist(start, edge_type, target_person, depth=4):
	if start == target_person:
		return 0#why did this even get called?

	pq = []  # queue for bfs
	current = start  # starting from me
	contflag = True
	dist_map = {start:0}

	while contflag:

		# figure out what edge_type of neighbors we are looking for
		if edge_type == 'work':
			neighbors = current.coworkers
		elif edge_type == 'friend':
			neighbors = current.friends
		else:
			raise AttributeError("Illegal argument to calc_bfs_dist, edge_type should be work, family, or friend, not " + str(edge_type))

		for n in neighbors:
			if not n in dist_map:  # then this node hasn't been seen yet
				if n.id == target_person.id:
					return dist_map[current] + 1
				dist_map.update({n:dist_map[current]+1})
				if dist_map[n] < depth:
					pq.append(n)  # add n to the queue

		if len(pq) == 0:
			contflag = False
		else:
			current = pq.pop(0)

	return float('inf')


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

	def __init__(self, M:Map, N: int):
		#defined by the user
		self.M = M
		self.N = N

		#optionally defined by the user (defaults defined here)
		self.age_dist = lambda: int(max(np.random.normal(38.2,22.7549),0))											#numbers from https://www.kff.org/other/state-indicator/distribution-by-age/ and https://www.cia.gov/library/publications/resources/the-world-factbook/geos/us.html
		self.hygiene_dist = lambda age: np.random.uniform(0,1)													#simple model assumes perfectly uniform hygiene, but more complex ones should take age into account
		self.location_ages_avg_dist = lambda: max(np.random.normal(20,15),0)									#normal distribution, mean 20 stdev 15 (years)
		self.location_ages_stdev_dist = lambda: 5																#5 years stdev every time
		self.coworkers_dist = lambda num_employees: min(max(int(np.random.normal(5,3)),0),num_employees)		#normal distribution, mean 5 stdev 3, >= 0
		self.friends_dist = lambda possible_friends: min(max(int(np.random.normal(5,3)),0),possible_friends)	#normal distribution, mean 5 stdev 3, >= 0
		self.partners_dist = lambda num_people_in_house: min(int(coinflip(0.05)),num_people_in_house)			#5% chance of having one partner, 95% of not having any
		self.num_places_dist = lambda: max(int(np.random.normal(3,2)),0)										#normal distribution, mean = 3, stdev = 2
		self.school_range = (0,0)																				#tuple of ages, between which people are in school (e.g. (0,18) means everyone from age 0 to age 18 is in school)
		self.max_school_size = 0
		self.avg_places = 0
		self.homeless_prob = 0.
		self.jobless_prob = 0.
		self.work_begin_avg_dist = lambda: tconv(str(np.random.choice(range(0,24))))										#uniform distribution, starting on the hour
		self.work_duration_avg_dist = lambda: tconv(str(np.random.choice(range(2,12))))										#uniform from 2 hours to 12 hours
		self.work_begin_stdev_dist = lambda: tconv("05")																	#always 5 hours
		self.work_duration_stdev_dist = lambda: tconv("01")																	#always 1 hour
		self.sleep_begin_dist = lambda work_time_tuple: int(np.random.normal(work_time_tuple[1] + tconv("03"),tconv("00:30")))	#3 hours after work ends on average
		self.sleep_duration_dist = lambda: int(np.random.normal(tconv("07"),tconv("01")))
		self.disease_list = []																								#list of disease objects, the builder will attempt to initialize the population with them
		self.healthiness_dist = lambda age: np.random.uniform(0,1)															#function from age of person -> person's healthiness coefficient


		#logical variables
		self.current_school_people = 0		#how many people are currently in school
		self.workable_locations = None	#locations that are not public (i.e. workable)
		self.houses = None


	def set_num_friends_distribution(self,dist):
		self.friends_dist = dist

	def set_num_coworkers_distribution(self,dist):
		self.coworkers_dist = dist

	def set_age_distribution(self,ad):
		self.age_dist = ad

	def set_average_preferred_locations(self,avg_places:float):
		self.avg_places = avg_places

	def set_homeless_probability(self,hp:float):
		self.homeless_prob = hp

	def set_hygiene_distribution(self,hd):
		self.hygiene_dist = hd

	def set_school_age_range(self,sar:tuple):
		self.school_range = sar

	def set_max_people_in_school(self,s:int):
		self.max_school_size = s

	def set_location_avg_distribution(self,lad):
		self.location_ages_avg_dist = lad

	def set_location_stdev_distribution(self,lsd):
		self.location_ages_stdev_dist = lsd

	def set_num_places_distribution(self,nlocd):
		self.num_places_dist = nlocd

	def set_jobless_probability(self,jp:float):
		self.jobless_prob = jp

	def set_partners_distribution(self,dist):
		self.partners_dist = dist

	def set_work_start_time_average_distribution(self,dist):
		self.work_begin_avg_dist = dist

	def set_work_duration_average_distribution(self,dist):
		self.work_duration_avg_dist = dist

	def set_work_start_time_stdev_distribution(self,dist):
		self.work_begin_stdev_dist = dist

	def set_work_duration_stdev_distribution(self,dist):
		self.work_duration_stdev_dist = dist

	def set_sleep_begin_time_distribution(self,dist):
		self.sleep_begin_dist = dist

	def set_sleep_duration_distribution(self,dist):
		self.sleep_duration_dist = dist

	def set_diseases_present(self,dis:list):
		self.disease_list = dis

	def set_healithiness_coefficient_distribution(self,dist):
		self.healthiness_dist = dist

	"""
	Assign all of the primitive details randomly to this person (they already need to have a home)
		age
		workplace
		places
	"""
	def assign_primitive_details(self, person:Person):
		person.age = self.age_dist()
		if (person.age >= self.school_range[0]) and (person.age <= self.school_range[1]):
			if self.current_school_people >= self.max_school_size:
				#then we already have enough school people, add the oldest school age to this to make sure this person isn't in school
				person.age += self.school_range[1]
			else:
				#age is valid now
				#then this person is in school
				person.set_workplace(self.M.get_school())

		if (not ((person.age >= self.school_range[0]) and (person.age <= self.school_range[1]))) and (person.home is not None):
			if not coinflip(self.jobless_prob):
				#this person is not in school and is not homeless and is not jobless, find a workplace
				wp,self.workable_locations = self.M.get_random_workable_location(workable=self.workable_locations)
				person.set_workplace(wp)

		#now the person has a workplace (if relevant) and an age, assign their locations
		nlocs = self.num_places_dist()
		for _ in range(nlocs):
			self.M.add_random_placable_location(person, self.location_ages_avg_dist, self.location_ages_stdev_dist)


		#hygiene
		person.hygiene_coef = self.hygiene_dist(person.age)

		#work schedule
		if person.workplace is not None:
			if person.workplace.avg_work_begin_time == -1:
				#assign this as needed
				person.workplace.avg_work_begin_time = self.work_begin_avg_dist()
				person.workplace.work_begin_stdev = self.work_begin_stdev_dist()
				person.workplace.avg_work_duration = self.work_duration_avg_dist()
				person.workplace.work_duration_stdev = self.work_duration_stdev_dist()
			work_begin_time = negsafe_mod(int(np.random.normal(person.workplace.avg_work_begin_time, person.workplace.work_begin_stdev)), TIME_STEPS_PER_DAY)
			work_duration = max(int(np.random.normal(person.workplace.avg_work_duration, person.workplace.work_duration_stdev)), 0)
			work_end_time = negsafe_mod((work_begin_time + work_duration), TIME_STEPS_PER_DAY)
			person.work_schedule = (work_begin_time, work_end_time)
		else:
			person.work_schedule = (0, 0)

		sleep_begin_time = negsafe_mod(self.sleep_begin_dist(person.work_schedule),TIME_STEPS_PER_DAY)
		sleep_duration = self.sleep_duration_dist()
		sleep_end_time = negsafe_mod((sleep_begin_time + sleep_duration) ,TIME_STEPS_PER_DAY)
		person.sleep_schedule = (sleep_begin_time, sleep_end_time)

		#set the disease state modifiers
		for disease in self.disease_list:
			is_vaccinated = disease.decide_is_vaccinated(person)
			if is_vaccinated:
				vaccine_works = coinflip(disease.vaccination_effectiveness)
				if vaccine_works:
					person.disease_state.update({disease: 'VU'})	#vaccinated, unsusceptible
				else:
					person.disease_state.update({disease:'VS'})		#vacinated, susceptible
			else:
				person.disease_state.update({disease:'S'})

		person.healthiness = self.healthiness_dist(person.age)


	'''
	The process for this is generally to make a random graph as defined in the PNAS paper (2566) on the people who work at this location, with the degree distribution
	
	general process:
		for each node/person:
			take k from the coworkers distribution
			assign k coworkers to this person, pointed at random within the workplace's employees
	
	this function just does that for one person, so no loop 
	'''
	def assign_coworkers(self,p:Person):
		if p.workplace is None:
			#this person doesn't have work, so don't bother
			return

		k = self.coworkers_dist(len(p.workplace.employees_residents))
		assign_to = np.random.choice(list(p.workplace.employees_residents),size=k)
		for emp in assign_to:
			if emp != p:
				p.coworkers.add(emp)
				if BIDIRECTIONAL_COWORKERS:
					emp.coworkers.add(p)

		return p

	'''
	Among all of the people who live at this place, assign k of them to be partners of person, where k is from the partners distribution
	'''
	def assign_partners(self,p:Person):
		if p.home is None:
			#assumption is that homeless do not have partners
			return

		k = self.partners_dist(len(p.home.employees_residents))
		assign_to = np.random.choice(list(p.home.employees_residents),size=k)
		for oth in assign_to:
			if oth != p:
				p.partners.add(oth)
				oth.partners.add(p)

		return p

	'''
	first pick a number of friends k for this person to have, k from the friends dist
	then pick a random location from the union of my places and {my home} to choose from and pick a random person that is of that place's clientele to add to my list
	repeat ^^ until we have enough (if a location has exhausted its clientele, scratch it off the list to ensure we'll halt)
	'''
	def assign_friends(self,p:Person):
		if (p.home is None) and (len(p.places) == 0):
			#no home and no places means no friends :(
			return

		#first figure out how many possible friends we could have
		possible = p.home.employees_residents.copy()
		possible.remove(p)#not myself
		for place in p.places:
			possible = possible.union(place.clientele)
		k = self.friends_dist(len(possible))
		assigned = 0
		pick_from = {p.home}.union(p.places)
		while (assigned < k) and (len(pick_from) > 0):
			#pick a random location in our places
			loc = np.random.choice(list(pick_from))
			possible_friends = loc.clientele - p.friends - {p}
			if len(possible_friends) > 0:
				assign = np.random.choice(list(possible_friends))
				p.friends.add(assign)
				if BIDIRECTIONAL_FRIENDS:
					assign.friends.add(p)
				assigned += 1
			else:
				#there's no one here we can be friends with, so we need to not pick this location again
				pick_from.remove(loc)

		return p


	def create_population(self):
		#initialization
		#make sure there's a school if we need one
		if self.max_school_size > 0:
			self.M.create_school(self.max_school_size)

		#create all the people and assign them to houses
		plist = []
		for _ in range(self.N):
			if coinflip(self.homeless_prob):
				h = None
			else:
				h,self.houses = self.M.get_random_house()

			p = Person(h,self.M)

			#person person now has a home and has been instantiated, assign their primitive details
			self.assign_primitive_details(p)

			#add them to the person list
			plist.append(p)
			#nothing else can be done in this loop since we need everyone's primitives to be defined before they can be assigned friends etc.

		for i,p in enumerate(plist):
			#now that all the primitive details are in, we can assign the network details
			plist[i] = self.assign_coworkers(p)
			plist[i] = self.assign_friends(p)
			plist[i] = self.assign_partners(p)

		return plist



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
	'hospital',#where the sick people be (technically a edge_type of shop, but it's important enough to exist on its own) [red on map]
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

		#these are used for reconstructing where people were at what time
		self.mapx_origin = -1
		self.mapy_origin = -1

		#this is used for determining the kinds of people that show up at this kind of place -- it's only relevant when creating people and assigning their places/friends
		#the assumption with it is that age is normally distributed with mean avg_age and stdev age_stdev
		self.avg_age = -1
		self.age_stdev = -1.

		#information on people habitually here
		self.employees_residents = set()#if relevant
		self.clientele = set()#who has this location listed as a `place`

		#work info
		self.avg_work_begin_time = -1
		self.avg_work_duration = -1
		self.work_begin_stdev = -1
		self.work_duration_stdev = -1

	'''
	Given an age, what is the probability this location would be one of their places?
	'''
	def age_prob(self,age):
		if self.loc_type not in PLACABLE_LOCATION_TYPES:
			return 0.

		assert(self.avg_age != -1)
		assert(self.age_stdev != -1.)

		from scipy import stats
		return stats.norm.pdf(age,self.avg_age,self.age_stdev)

	def is_full(self):
		return len(self.people) >= self.capacity

	def is_empty(self):
		return len(self.people) <= 0


	def arrive(self,p: Person):
		if self.is_full():#we can't take this person on, reject them
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
		rset = set()
		for i,a in enumerate(self.people):
			for j in range(i,len(self.people)):
				b = self.people[j]
				if a != b:
					for disease in a.disease_state:
						if disease.infects(a,b):
							rset.add((a,disease,b))
							disease.infect(b)
					for disease in b.disease_state:
						if disease.infects(b,a):
							rset.add((b,disease,a))
							disease.infect(a)

		return rset

	def __repr__(self):
		return self.loc_type + ' ' + str(self.id)


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

		#if this is an action like walking, we need to know where we're going
		#similarly, if we're talking to someone, we need to know who (these take up the same variable because they're mutually exclusive)
		self.to = None#edge_type = Location or Person
		self.path = []#travel path should be precalculated; consists of locations that we will visit on the way (this means public locations need to be split up into a network of small public locations)

	def __repr__(self):
		return self.activity_type + ('' if self.to is None else ' to ' + str(self.to))
