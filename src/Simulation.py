"""
This is where the actual simulation code will go. This is the code that tells all the other stuff when to do what.

It keeps track of all the people, all the locations (and their implicit map), and all of the diseases
It uses this information to go step-by-step and see how the infection(s) progress(es)
"""

from SINUtil import *
from PersonState import Person, Location, Activity, PopulationBuilder
from Map import Map, MapReader
from Disease import *

class Simulation:

	DUMP_FILE_DELIMITER = '|'

	'''
	infodump type should be a list of strings in {infection,network,map}, with the file to dump them to in the same order in infodump_file
	file should be a list -- one for each
	'''
	def __init__(self,infodump_file=None,time_steps_per_infodump=100,ensure_non_immune_patient_zero=False,infodump_type=None):

		self.diseases = all_diseases	#default to everything
		self.population = []
		self.map = None
		self.map_img_reference = ""	#where is the image we should map this map to?

		self.current_time = 0
		self.total_direct_infections_today = 0
		self.total_idle_infections_today = 0

		self.prev_infection_counts = []

		self.infodump_file = infodump_file
		self.infodump_type = infodump_type
		self.time_steps_per_infodump = time_steps_per_infodump
		self.ensure_non_immune_patient_zero = ensure_non_immune_patient_zero#TODO: add functionality for more than one patient zero?

		if self.infodump_file is not None:
			self.initial_infodump_done = [False for _ in self.infodump_file]

	def read_map_from_image(self,mr:MapReader,fname:str):
		self.map = mr.create_map_from_file(fname)

	def set_diseases(self,to:list):
		self.diseases = to

	def create_population(self,pb: PopulationBuilder):
		pb.set_diseases_present(self.diseases)
		self.population = pb.create_population()

	def inc_time_step(self):
		if self.infodump_file is not None:
			if self.current_time % self.time_steps_per_infodump == 0:
				self.dump_info()
		self.current_time += 1

	def infection_info_format(self):
		retstr = 'TIME STEP' + self.DUMP_FILE_DELIMITER
		for disease in self.diseases:
			for stype in DISEASE_STATES_LIST:
				retstr += disease.name + ' '
				retstr += stype + self.DUMP_FILE_DELIMITER

		retstr += 'TOTAL'
		return retstr
	'''
	just the info on how many people were infected:
	
	time step | (for each disease: disease name | (for each state: count of people in that state))
	'''
	def dump_infection_info(self) -> str:
		retstr = str(self.current_time) + self.DUMP_FILE_DELIMITER
		for disease in self.diseases:
			disease_state_counts = {state: 0 for state in DISEASE_STATES_LIST}
			for person in self.population:
				disease_state_counts[person.disease_state[disease]] += 1

			for state in DISEASE_STATES_LIST:
				retstr += str(disease_state_counts[state]) + self.DUMP_FILE_DELIMITER

		retstr += str(len(self.population))
		return retstr

	def network_info_format(self) -> str:
		return ''#TODO: implement infection network dump format

	'''
	this is just the info on networks of who infected who
	
	(for each person that was infected): person's name (id) | who infected them (id)
	'''
	def dump_network_info(self) -> str:
		return ''#TODO: implement infection network dump


	'''
	format
	
	time step | (for each person: person id | location | (for each disease: disease name | disease state))
	'''
	def map_info_format(self) -> str:
		retstr = 'TIME STEP' + self.DUMP_FILE_DELIMITER
		for person in self.population:
			retstr += str(person.id) + self.DUMP_FILE_DELIMITER + 'CURRENT LOCATION' + self.DUMP_FILE_DELIMITER
			for disease in self.diseases:
				retstr += disease.name + self.DUMP_FILE_DELIMITER
				retstr += person.disease_state[disease] + self.DUMP_FILE_DELIMITER

		retstr = retstr[:-1]#drop the last delimiter
		return retstr

	'''
	this is the info on who was at what location at what time and what state they were in
	
	in reality it just gives, for each person, their location (given as (mapx,mapy) and their state at the given time)
	'''
	def dump_map_info(self) -> str:
		retstr = str(self.current_time) + self.DUMP_FILE_DELIMITER
		for person in self.population:
			retstr += str(person.id) + self.DUMP_FILE_DELIMITER + str((person.currentLocation.mapx,person.currentLocation.mapy)) + self.DUMP_FILE_DELIMITER
			for disease in self.diseases:
				retstr += disease.name + self.DUMP_FILE_DELIMITER
				retstr += person.disease_state[disease] + self.DUMP_FILE_DELIMITER

		return retstr[:-1]

	def dump_info(self):
		assert(self.infodump_file is not None)
		#now we want to print all of the fun stuff to this file so we can visualize it
		for i,(file,ftype) in enumerate(zip(self.infodump_file,self.infodump_type)):
			write_str = ''
			if ftype == 'infection':
				if not self.initial_infodump_done[i]:
					with open(file,'w') as f:
						f.write(self.infection_info_format() + '\n')
					self.initial_infodump_done[i] = True
				write_str = self.dump_infection_info()
			elif ftype == 'network':
				if not self.initial_infodump_done[i]:
					with open(file, 'w') as f:
						f.write(self.network_info_format() + '\n')
					self.initial_infodump_done[i] = True
				write_str = self.dump_network_info()
			elif ftype == 'map':
				if not self.initial_infodump_done[i]:
					with open(file, 'w') as f:
						f.write(self.map_info_format() + '\n')
					self.initial_infodump_done[i] = True
				write_str = self.dump_map_info()

			if len(write_str) > 0:
				write_str = write_str + '\n'
				with open(file, 'a') as f:
					f.write(write_str)

	def simulate_day(self):
		self.total_direct_infections_today = 0
		self.total_idle_infections_today = 0
		#first call all the day begin things
		for person in self.population:
			person.day_begin()

		#now start going through the day
		for day_time in range(TIME_STEPS_PER_DAY):
			#get action transitions and do them
			for person in self.population:
				self.total_direct_infections_today += person.do_current_action()#infection processing happens here
				person.action_transition(day_time)#idle infections here
				self.total_idle_infections_today += person.idle_infection_count

			# #now do infection processing
			# for location in self.map.loc_list:
			# 	lir_ret = location.infection_round()
			# 	self.infection_networks = self.infection_networks.union(lir_ret)

			self.inc_time_step()#may have information dumping side effects

	'''
	`strict` convergence -- all diseases in final states (dead, nonsusceptible, etc.)
	takes about 1m 17s on the small map with 100 population to do 10 days
	'''
	def converged_strict(self):
		for person in self.population:
			for disease in person.disease_state:
				if person.disease_state[disease] not in DISEASE_STATES_FINAL:
					return False
		return True

	'''
	Much like the strict convergence, but will return false only if *all* of the diseases we're running have someone in a nonfinal state
	that is, we stop when any of the diseases die
	
	takes about 1m 22s on the small map with 100 population to do 10 days
	'''
	def converged_strict_single_dead(self):
		diseases_dead = set(self.diseases)
		for person in self.population:
			dd_iterate = diseases_dead.copy()
			for disease in dd_iterate:
				if person.disease_state[disease] not in DISEASE_STATES_FINAL:
					#this disease is still alive
					diseases_dead.remove(disease)

			if len(diseases_dead) == 0:
				# then all of them are still alive, so we can keep going
				return False

		return True#one of them must never have found a person in the final disease state, so at least one is dead

	'''
	much 'looser' type of convergence that only requires no new infections in a while
	
	checks the last few to see if anyone was infected, if not then we're done
	
	takes about 1m 15s on the small map with 100 population to do 10 days
	'''
	def converged_no_new_infections(self,window=5):
		self.prev_infection_counts.append(self.total_idle_infections_today + self.total_direct_infections_today)
		if len(self.prev_infection_counts) > window:
			self.prev_infection_counts.pop(0)
			for ct in self.prev_infection_counts:
				if ct != 0:
					return False
			return True
		else:
			return False

	def full_simulation(self,converged=converged_strict_single_dead,verbose = False,time_limit=0):
		#pick a patient zero for each disease
		diseases_running = 0	#how many diseases actually have anyone infected?
		diseases_not_running = []#which diseases of the ones requested aren't actually running due to immunity?
		for d in self.diseases:
			choices = []
			if self.ensure_non_immune_patient_zero:
				for person in self.population:
					if person.disease_state[d] not in DISEASE_STATES_VACCINATED:
						choices.append(person)
				if len(choices) <= 0:
					print('WARNING: disease ' + d.name + ' had no non-immune in the population, choosing a random person to make non-immune.')
					zero = np.random.choice(self.population)
					zero.disease_state[d] = 'S'
					choices.append(zero)
			else:
				choices = self.population
			zero = np.random.choice(choices)
			d.infect(zero)
			if zero.disease_state[d] in DISEASE_STATES_INFECTIOUS:
				diseases_running += 1
				if verbose:
					print(str(d) + ', patient zero: ' + str(zero))
			else:
				diseases_not_running.append(d)
		for dnr in diseases_not_running:
			self.diseases.remove(dnr)
		dayct = 0
		if verbose:
			print()
		while (not converged(self)) and ((time_limit <= 0) or (dayct < time_limit)):
			self.simulate_day()
			if verbose:
				print('day ' + str(dayct) + ' summary: ')
				print('total infections today:\t\t' + str(self.total_idle_infections_today + self.total_direct_infections_today))
				print('direct:\t\t\t\t\t\t' + str(self.total_direct_infections_today))
				print('idle:\t\t\t\t\t\t' + str(self.total_idle_infections_today))
				n_infected = {disease : 0 for disease in self.diseases}	#map diseases to number infected
				total_infected = 0
				for person in self.population:
					for disease in self.diseases:
						if person.disease_state[disease] in DISEASE_STATES_INFECTIOUS:
							n_infected[disease] += 1
							total_infected += 1

				print('current infected for each disease:')
				for disease in self.diseases:
					print(str(disease) + ': ' + str(n_infected[disease]))
				print('current infections: ' + str(total_infected))	#will be off by however many diseases are actually going
				print()
			dayct += 1