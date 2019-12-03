"""
This file contains all of the relevant classes etc. for diseases, including their symptoms, method of transmission, rate of transmission, etc.

"""

from SINUtil import *

class Disease:
	import PersonState as ps

	DISEASE_ID_COUNTER = 0

	def __init__(self,name:str,calculate_R_0=False):

		self.name = name
		self.calculate_R_0 = calculate_R_0

		#defaults describe the null disease that can't actually do anything
		self.infectivity = {'idle':0.,
							'sleep':0.,
							'traveling':0.,
							'talking':0.,
							'intimate':0.}#per time step of doing this interaction with someone infected (in the case of idle, traveling, and sleep, in the same room), what is the probability they infect me, per infected person nearby?

		for action_type in self.ps.ACTIVITY_TYPES:
			assert(action_type in self.infectivity)

		self.hand_wash_coef = 0.#how much does washing hands affect this disease? lower numbers means it affects this less

		self.symptom_show_rate = 0.#per day, what is the probability a person infected with this disease goes from infectious but without symptoms to infectious but with symptoms?

		self.symptom_infectivity_modifier = 0.#given that the infected person is showing symptoms, how does the infectivity change? (usually goes up)

		self.recovery_rate = 0.#per day, what is the probability I recover (go from the IS state to the R state)?

		self.die_probability = 0.#per day, what is the probability I die (from the IS state to the D state), given that the healthiness check failed?

		self.state_infectability_modifiers = {'S':0.,#this is usually 0
											  'II':0.,
											  'VII':0.,
											  'IS':0.,
											  'VIS':0.,
											  'R':0.,
											  'VR':0.,
											  'VS':0.,
											  'VU':0,
											  'D':0.,#this is useful so we can figure out which disease killed which person
											  'VD':0.,
											  }	#given that I am, for this disease, in this state, how much more (positive) or less (negative) likely am I to be infected with something else?

		self.vaccination_effectiveness = 0.		#how effective is the vaccine? (probability it actually makes you nonsusceptible

		self.vaccination_rate = 0.				#what is the probability any given person is vaccinated against this disease?

		self.symptom_health_effect = 0.			#to what extent does this disease hurt the healthiness of the individual? (for the cold, it's not too bad, for zika, this would be debilitating (high))

		self.treatability = 0.					#how much can doctors in the hospital actually help if we're infected with this?

		for infection_state in DISEASE_STATES:
			assert(infection_state in self.state_infectability_modifiers)

		self.disease_id = Disease.DISEASE_ID_COUNTER
		Disease.DISEASE_ID_COUNTER += 1


		self.num_infected_by = {}				#how many people has a given person infected

	def __repr__(self):
		return "Disease " + str(self.disease_id) + ": " + self.name

	def recover(self,person:ps.Person):
		is_in_hopsital = person.currentLocation.loc_type == 'hospital'
		hospital_effect = 0.
		if is_in_hopsital:
			hospital_effect = HOSPITAL_TREATMENT_EFFECT * self.treatability
		return coinflip(min(self.recovery_rate + hospital_effect,1.))

	def symptom_show(self):
		return coinflip(self.symptom_show_rate)

	def die(self,person:ps.Person):
		if coinflip(1 - person.get_effective_healthiness()):#healthier means this is less likely to happen
			is_in_hopsital = person.currentLocation.loc_type == 'hospital'
			hospital_effect = 0.
			if is_in_hopsital:
				hospital_effect = HOSPITAL_TREATMENT_EFFECT * self.treatability
			return coinflip(max(0,self.die_probability - hospital_effect))#hospitals make it *less* likely that you'll die

	def decide_is_vaccinated(self,person:ps.Person):
		#TODO: antivax clustering here?
		return coinflip(self.vaccination_rate)

	def disease_state_transition(self,person:ps.Person):
		if (person.disease_state[self] == 'II') and (self.symptom_show()):
			person.disease_state[self] = 'IS'
		elif (person.disease_state[self] == 'VII') and (self.symptom_show()):
			person.disease_state[self] = 'VIS'
		elif (person.disease_state[self] == 'IS') and (self.recover(person)):
			person.disease_state[self] = 'R'
		elif (person.disease_state[self] == 'VIS') and (self.recover(person)):
			person.disease_state[self] = 'VR'
		elif (person.disease_state[self] == 'IS') and (self.die(person)):
			person.disease_state[self] = 'D'
			person.die()	#F
		elif (person.disease_state[self] == 'VIS') and (self.die(person)):
			person.disease_state[self] = 'VD'
			person.die()	#F

		#set the diseases showing symptoms variable
		for disease in person.disease_state:
			if person.disease_state[disease] in DISEASE_STATES_SYMPTOMATIC:
				person.diseasesShowingSymptoms = True
				return
		person.diseasesShowingSymptoms = False

	"""
	Does person a infect person b?
	"""
	def infects(self,a : ps.Person,b : ps.Person):
		if a.disease_state[self] not in DISEASE_STATES_INFECTIOUS:#all diseases should be accounted for in every person's disease_state map, so we don't need to check
			#a is not infectious
			return False
		if b.disease_state[self] not in DISEASE_STATES_SUSCEPTIBLE:
			#b is not susceptible
			return False

		symptom_effect = self.symptom_infectivity_modifier if (a.disease_state[self] in DISEASE_STATES_SYMPTOMATIC) else 0.
		hand_wash_effect = 0.
		effective_activity_type = a.currentActivity.activity_type	#doesn't matter if they're not talking TO b
		if (a.currentActivity.activity_type == 'talking') or (a.currentActivity.activity_type == 'intimate'):
			if a.currentActivity.to == b:
				a_washed_hands = int(coinflip(a.hygiene_coef))
				b_washed_hands = int(coinflip(b.hygiene_coef))
				hand_wash_effect = self.hand_wash_coef*HANDWASH_EFFECT_MODIFIERS[a_washed_hands][b_washed_hands]#the items in HANDWASH_EFFECT_MODIFIERS are all nonpositive, so this can only hurt the disease
			else:
				effective_activity_type = 'idle'
		intimate_effect = 0.
		if a.currentActivity.activity_type == 'intimate':
			if a.currentActivity.to == b:
				intimate_effect = INTIMATE_EFFECT_MODIFIER#this is in general, not specific to the disease
			else:
				effective_activity_type = 'idle'

		#logic for symbiotic and competitive diseases (e.g. having HIV makes it easier for you to get other diseases)d
		net_symbio_effect = 0.
		for disease in b.disease_state:
			if disease != self:
				net_symbio_effect += disease.state_infectability_modifiers[b.disease_state[disease]]

		infectivity = self.infectivity[effective_activity_type] + symptom_effect + hand_wash_effect + intimate_effect + net_symbio_effect

		res = coinflip(infectivity)
		if res:
			if self.calculate_R_0:
				# now update our R_0 measure
				if a in self.num_infected_by:
					self.num_infected_by[a] += 1
				else:
					self.num_infected_by.update({a:1})

			return True
		else:
			return False

	'''
	actually infect this person with this disease
	'''
	def infect(self,person:ps.Person):
		if person.disease_state[self] not in DISEASE_STATES_SUSCEPTIBLE:
			return#already done
		if person.disease_state[self] in DISEASE_STATES_VACCINATED:
			person.disease_state[self] = 'VII'
		else:
			person.disease_state[self] = 'II'


#this part contains some definitions for a few interesting diseases

#something of an HIV-like STD
STD_0 = Disease('STD_0')
STD_0.infectivity = {'idle':0.,
					'sleep':0.,
					'traveling':0.,
					'talking':0.00000001,
					'intimate':0.09}
STD_0.hand_wash_coef = 0.
STD_0.symptom_show_rate = 0.05
STD_0.symptom_infectivity_modifier = 0.05
STD_0.recovery_rate = 0.01
STD_0.die_probability = 0.001			#this doesn't actually kill you
STD_0.state_infectability_modifiers = {'S':0.,
									   'II':0.1,
									   'VII':0.1,
									   'IS':0.15,
									   'VIS':0.15,
									   'R':0.05,
									   'VR':0.05,
									   'VS':0.,
									   'VU':0.,
									   'D':0.,
									   'VD':0.,
									  }
STD_0.vaccination_effectiveness = 0.
STD_0.vaccination_rate = 0.#there isn't one
STD_0.symptom_health_effect = 0.05#small effect
STD_0.treatability = 0.#can't be treated

#flu-like
virus_0 = Disease('virus 0')
virus_0.infectivity = {'idle':0.0005,
						'sleep':0.0001,
						'traveling':0.0001,
						'talking':0.009,
						'intimate':0.06}
virus_0.hand_wash_coef = 0.5
virus_0.symptom_show_rate = 0.3
virus_0.recovery_rate = 0.2
virus_0.die_probability = 0.009
virus_0.vaccination_effectiveness = 0.3
virus_0.vaccination_rate = 0.2
virus_0.symptom_health_effect = 0.2#medium effect
virus_0.treatability = 0.4
virus_0.symptom_infectivity_modifier = 0.05

#measles-like, some numbers from https://en.wikipedia.org/wiki/Measles
virus_1 = Disease('virus 1')
virus_1.infectivity = { 'idle':0.005,
						'sleep':0.01,
						'traveling':0.005,
						'talking':0.1,
						'intimate':0.09}
virus_1.hand_wash_coef = 0.2
virus_1.symptom_show_rate = 1./14.
virus_1.recovery_rate = 0.09
virus_1.die_probability = 0.1
virus_1.vaccination_effectiveness = 0.99
virus_1.vaccination_rate = 0.95
virus_1.symptom_health_effect = 0.6#large effect
virus_1.treatability = 0.05
virus_1.symptom_infectivity_modifier = 0.03

#entirely made up, but potentially interesting: competitive disease
competitive_disease_0 = Disease("Competitive 0")
competitive_disease_0.infectivity = {'idle':0.,
									'sleep':0.0075,
									'traveling':0.,
									'talking':0.005,
									'intimate':0.035}
competitive_disease_0.hand_wash_coef = 0.7
competitive_disease_0.symptom_show_rate = 0.1
competitive_disease_0.symptom_infectivity_modifier = 0.09
competitive_disease_0.recovery_rate = 0.2
competitive_disease_0.die_probability = 0.001
competitive_disease_0.state_infectability_modifiers = {'S':0.,
													  'II':-0.2,
													  'VII':-0.2,
													  'IS':-0.3,
													  'VIS':-0.3,
													  'R':-0.05,
													  'VR':-0.05,
													  'VS':0.,
													  'VU':0.,
													  'D':0.,
													  'VD':0.,
													  }
competitive_disease_0.vaccination_effectiveness = 0.6
competitive_disease_0.vaccination_rate = 0.4
competitive_disease_0.symptom_health_effect = 0.35
competitive_disease_0.treatability = 0.3

#this is a test disease to make sure the logic all works as expected
t_disease = Disease('test disease')
t_disease.infectivity = {'idle':0.,
						'sleep':0.,
						'traveling':0.,
						'talking':1,
						'intimate':1}
t_disease.hand_wash_coef = 0.
t_disease.symptom_show_rate = 0.5
t_disease.recovery_rate = 0.5
t_disease.die_probability = 0.1
t_disease.vaccination_effectiveness = 0.
t_disease.vaccination_rate = 0.5
t_disease.symptom_health_effect = 1#F
t_disease.treatability = 0.#F

all_diseases = [STD_0,virus_0,virus_1,competitive_disease_0]	#all diseases yet defined
real_basis_diseases = [STD_0,virus_0,virus_1]					#just the ones that have basis in real ones
fast_diseases = [virus_0,virus_1,competitive_disease_0]			#just the ones with high recovery/death rates
test_diseases = [t_disease]