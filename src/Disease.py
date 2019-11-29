"""
This file contains all of the relevant classes etc. for diseases, including their symptoms, method of transmission, rate of transmission, etc.

"""

from SINUtil import *

class Disease:
	import PersonState as ps

	DISEASE_ID_COUNTER = 0

	def __init__(self,name:str):

		self.name = name

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

		for infection_state in DISEASE_STATES:
			assert(infection_state in self.state_infectability_modifiers)

		self.disease_id = Disease.DISEASE_ID_COUNTER
		Disease.DISEASE_ID_COUNTER += 1

	def __repr__(self):
		return "Disease " + str(self.disease_id) + ": " + self.name

	def recover(self):
		return coinflip(self.recovery_rate)

	def symptom_show(self):
		return coinflip(self.symptom_show_rate)

	def die(self,person:ps.Person):
		if coinflip(1 - person.healthiness):#healthier means this is less likely to happen
			return coinflip(self.die_probability)

	def decide_is_vaccinated(self,person:ps.Person):
		#TODO: antivax clustering here?
		return coinflip(self.vaccination_rate)

	def disease_state_transition(self,person:ps.Person):
		if (person.disease_state[self] == 'II') and (self.symptom_show()):
			person.disease_state[self] = 'IS'
		elif (person.disease_state[self] == 'VII') and (self.symptom_show()):
			person.disease_state[self] = 'VIS'
		elif (person.disease_state[self] == 'IS') and (self.recover()):
			person.disease_state[self] = 'R'
		elif (person.disease_state[self] == 'VIS') and (self.recover()):
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

		return coinflip(infectivity)

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
					'sleep':0.001,
					'traveling':0.,
					'talking':0.001,
					'intimate':0.3}
STD_0.hand_wash_coef = 0.
STD_0.symptom_show_rate = 0.05
STD_0.symptom_infectivity_modifier = 0.
STD_0.recovery_rate = 0.01
STD_0.die_probability = 0.001			#this doesn't actually kill you
STD_0.state_infectability_modifiers = {'S':0.,
									   'II':0.2,
									   'VII':0.2,
									   'IS':0.3,
									   'VIS':0.3,
									   'R':0.,
									   'VR':0.,
									   'VS':0.,
									   'VU':0.,
									   'D':0.,
									   'VD':0.,
									  }
STD_0.vaccination_effectiveness = 0.
STD_0.vaccination_rate = 0.#there isn't one

#flu-like
virus_0 = Disease('virus 0')
virus_0.infectivity = {'idle':0.05,
						'sleep':0.001,
						'traveling':0.001,
						'talking':0.1,
						'intimate':0.3}
virus_0.hand_wash_coef = 0.5
virus_0.symptom_show_rate = 0.3
virus_0.recovery_rate = 0.2
virus_0.die_probability = 0.009
virus_0.vaccination_effectiveness = 0.3
virus_0.vaccination_rate = 0.2

#measles-like, some numbers from https://en.wikipedia.org/wiki/Measles
virus_1 = Disease('virus 1')
virus_1.infectivity = { 'idle':0.05,
						'sleep':0.1,
						'traveling':0.05,
						'talking':0.7,
						'intimate':0.9}
virus_1.hand_wash_coef = 0.2
virus_1.symptom_show_rate = 1./14.
virus_1.recovery_rate = 0.09
virus_1.die_probability = 0.1
virus_1.vaccination_effectiveness = 0.99
virus_1.vaccination_rate = 0.95

#entirely made up, but potentially interesting: competitive disease
competitive_disease_0 = Disease("Competitive 0")
competitive_disease_0.infectivity = {'idle':0.,
									'sleep':0.075,
									'traveling':0.,
									'talking':0.1,
									'intimate':0.35}
competitive_disease_0.hand_wash_coef = 0.7
competitive_disease_0.symptom_show_rate = 0.1
competitive_disease_0.symptom_infectivity_modifier = 0.3
competitive_disease_0.recovery_rate = 0.2
competitive_disease_0.die_probability = 0.001
competitive_disease_0.state_infectability_modifiers = {'S':0.,
													  'II':-0.4,
													  'VII':-0.4,
													  'IS':-0.6,
													  'VIS':-0.6,
													  'R':-0.1,
													  'VR':-0.1,
													  'VS':0.,
													  'VU':0.,
													  'D':0.,
													  'VD':0.,
													  }
competitive_disease_0.vaccination_effectiveness = 0.6
competitive_disease_0.vaccination_rate = 0.4

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

all_diseases = [STD_0,virus_0,virus_1,competitive_disease_0]	#all diseases yet defined
real_basis_diseases = [STD_0,virus_0,virus_1]					#just the ones that have basis in real ones
fast_diseases = [virus_0,virus_1,competitive_disease_0]			#just the ones with high recovery/death rates
test_diseases = [t_disease]