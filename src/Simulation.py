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

	def __init__(self):

		self.diseases = all_diseases	#default to everything
		self.population = []
		self.map = None
		self.map_img_reference = ""	#where is the image we should map this map to?

		self.current_time = 0
		self.infection_networks = set()
		self.total_infections_prev_day = 0

	def read_map_from_image(self,mr:MapReader,fname:str):
		self.map = mr.create_map_from_file(fname)

	def set_diseases(self,to:list):
		self.diseases = to

	def create_population(self,pb: PopulationBuilder):
		pb.set_diseases_present(self.diseases)
		self.population = pb.create_population()

	def simulate_day(self):
		self.total_infections_prev_day = len(self.infection_networks)
		#first call all the day begin things
		for person in self.population:
			person.day_begin()

		#now start going through the day
		for day_time in range(TIME_STEPS_PER_DAY):
			#get action transitions and do them
			for person in self.population:
				person.do_current_action()
				person.action_transition(day_time)

			#now do infection processing
			for location in self.map.loc_list:
				lir_ret = location.infection_round()
				self.infection_networks = self.infection_networks.union(lir_ret)

			self.current_time += 1

	'''
	`strict` convergence -- all diseases in final states (dead, nonsusceptible, etc.)
	'''
	def converged_strict(self):
		for person in self.population:
			for disease in person.disease_state:
				if person.disease_state[disease] not in DISEASE_STATES_FINAL:
					return False
		return True

	'''
	much simpler check that is normally equivalent, but may cause problems with small infected populations
	'''
	def converged_no_infections(self):
		return len(self.infection_networks) != self.total_infections_prev_day

	def full_simulation(self,converged=converged_strict,verbose = False):
		#pick a patient zero for each disease
		diseases_running = 0	#how many diseases actually have anyone infected?
		for d in self.diseases:
			person = np.random.choice(self.population)
			d.infect(person)#TODO: make sure this person isn't vaccinated?
			if person.disease_state[d] in DISEASE_STATES_INFECTIOUS:
				diseases_running += 1
				if verbose:
					print(str(d) + ' patient zero: ' + str(person))
		dayct = 0
		if verbose:
			print()
		while not converged(self):
			self.simulate_day()
			if verbose:
				print('day ' + str(dayct) + ' summary: ')
				print(str(len(self.infection_networks)) + ' total infections (' + str(len(self.infection_networks) - self.total_infections_prev_day) + ' today)')
				n_infected = {disease : 0 for disease in self.diseases}	#map diseases to number infected
				total_infected = 0
				infectable_time = 0
				infectable_people = 0
				for person in self.population:
					for disease in self.diseases:
						if person.disease_state[disease] in DISEASE_STATES_INFECTIOUS:
							n_infected[disease] += 1
							total_infected += 1

					if person.interaction_time_infectable != 0:
						infectable_time += person.interaction_time_infectable
						infectable_people += 1
				print('current infected for each disease:')
				for disease in self.diseases:
					print(str(disease) + ': ' + str(n_infected[disease]))
				print('current infections: ' + str(total_infected))	#will be off by however many diseases are actually going
				print('total time infectable (interaction based): ' + str(infectable_time))
				print('total people infectable (interaction based): ' + str(infectable_people))
				print()
			dayct += 1