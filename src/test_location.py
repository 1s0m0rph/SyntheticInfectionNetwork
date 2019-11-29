from unittest import TestCase


class TestLocation(TestCase):
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

	from Disease import Disease
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

	def test_infection_round(self):
		from PersonState import Person
		p0 = Person(self.tl_home, self.M)
		p1 = Person(self.tl_home, self.M)
		p2 = Person(self.tl_home, self.M)
		p3 = Person(self.tl_home, self.M)
		p4 = Person(self.tl_home, self.M)

		p0.disease_state[self.t_disease] = 'II'
		p1.disease_state[self.t_disease] = 'VS'
		p2.disease_state[self.t_disease] = 'S'
		p3.disease_state[self.t_disease] = 'VU'
		p4.disease_state[self.t_disease] = 'R'

		self.tl_home.infection_round()

		assert(p0.disease_state[self.t_disease] == 'II')
		assert(p1.disease_state[self.t_disease] == 'VII')
		assert(p2.disease_state[self.t_disease] == 'II')
		assert(p3.disease_state[self.t_disease] == 'VU')
		assert(p4.disease_state[self.t_disease] == 'R')