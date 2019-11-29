from unittest import TestCase

from Disease import *

class TestDisease(TestCase):
	from Map import MapReader
	v = False
	# use the map reader since making one of these by hand is going to be a pain
	mr = MapReader(PUBLIC_BLOCK_SIZE=(2, 2), CAPACITY_PER_PIXEL=2, TIME_STEP_PER_PIXEL=2)
	M = mr.create_map_from_file('../test_map_small.png')
	tl_tl_home = M.loc_list[0]  # top left home
	tl_home = M.loc_list[
		42]  # this is the home which is down-right of the top-left home (9th cell if counting left-right, top-bottom)
	br_shop = M.loc_list[175]  # this is the shop in the bottom right corner
	L_office = M.loc_list[119]  # this is the L-shaped office
	
	t_disease = Disease('test disease pls ignore')
	t_disease.infectivity = {'idle': 1,
							 'sleep': 1,
							 'traveling': 1,
							 'talking': 1,
							 'intimate': 1}
	t_disease.hand_wash_coef = 0.5
	t_disease.symptom_show_rate = 1
	t_disease.symptom_infectivity_modifier = 0
	t_disease.recovery_rate = 0
	t_disease.die_probability = 1
	t_disease.vaccination_effectiveness = 0
	t_disease.vaccination_rate = 0

	def test_disease_state_transition(self):
		from PersonState import Person
		p0 = Person(self.tl_home,self.M)

		p0.disease_state.update({self.t_disease : 'II'})
		self.t_disease.disease_state_transition(p0)
		assert(p0.disease_state[self.t_disease] == 'IS')
		self.t_disease.disease_state_transition(p0)
		assert (p0.disease_state[self.t_disease] == 'D')

		p1 = Person(self.tl_home, self.M)
		p1.disease_state.update({self.t_disease: 'VII'})
		self.t_disease.disease_state_transition(p1)
		assert (p1.disease_state[self.t_disease] == 'VIS')
		self.t_disease.disease_state_transition(p1)
		assert (p1.disease_state[self.t_disease] == 'VD')


	def test_infects(self):
		from PersonState import Person
		p0 = Person(self.tl_home, self.M)
		p1 = Person(self.tl_home, self.M)

		p0.disease_state[self.t_disease] = 'II'
		p1.disease_state[self.t_disease] = 'VS'

		assert(self.t_disease.infects(p0,p1))