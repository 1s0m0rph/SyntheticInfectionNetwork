"""
This file contains all of the relevant classes etc. for diseases, including their symptoms, method of transmission, rate of transmission, etc.

"""

from SINUtil import *

class Disease:
	import PersonState as ps

	def __init__(self,disease_id):

		self.infectivity = {'idle':0.,
							'sleep':0.,
							'traveling':0.,
							'talking':0.,
							'intimate':0.}#per time step of doing this interaction with someone infected (in the case of idle, traveling, and sleep, in the same room), what is the probability they infect me, per infected person nearby?

		self.hand_wash_coef = 0.#how much does washing hands affect this disease? lower numbers means it affects this less

		self.symptom_show_rate = 0.#per time step, what is the probability a person infected with this disease goes from infectious but without symptoms to infectious but with symptoms?

		self.symptom_infectivity_modifier = 0.#given that the infected person is showing symptoms, how does the infectivity change? (usually goes up)

		self.recovery_rate = 0.#per day, what is the probability I recover?

		self.disease_id = disease_id

	def recover(self):
		return coinflip(self.recovery_rate)

	def symptom_show(self):
		return coinflip(self.symptom_show_rate)

	"""
	Does person a infect person b?
	"""
	def infects(self,a : ps.Person,b : ps.Person):
		if self.disease_id not in a.disease_state:
			# a is not infected
			return False
		if (a.disease_state[self.disease_id] != 'II') and (a.disease_state[self.disease_id] != 'IS'):
			#a is not infectious
			return False
		if self.disease_id in b.disease_state:
			if b.disease_state[self.disease_id] != 'S':
				#b is not susceptible
				return False

		symptom_effect = self.symptom_infectivity_modifier if (a.disease_state[self.disease_id] == 'IS') else 0.
		hand_wash_effect = 0.
		if (a.currentActivity.activity_type == 'talking') or (a.currentActivity.activity_type == 'intimate'):
			a_washed_hands = int(coinflip(a.hygiene_coef))
			b_washed_hands = int(coinflip(b.hygiene_coef))
			hand_wash_effect = self.hand_wash_coef*HANDWASH_EFFECT_MODIFIERS[a_washed_hands][b_washed_hands]#the items in HANDWASH_EFFECT_MODIFIERS are all nonpositive, so this can only hurt the disease
		intimate_effect = 0.
		if a.currentActivity.activity_type == 'intimate':
			intimate_effect = INTIMATE_EFFECT_MODIFIER#this is in general, not specific to the disease

		infectivity = self.infectivity[a.currentActivity.activity_type] + symptom_effect + hand_wash_effect + intimate_effect

		return coinflip(infectivity)
