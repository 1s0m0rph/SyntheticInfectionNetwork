from unittest import TestCase
from PersonState import *
import numpy as np

class TestPerson(TestCase):
	


	def test_affinity(self):
		test_home = Location('home',8)
		test_wp = Location('casino',300)

		p0 = Person(test_home, 0)
		p1 = Person(test_home, 1)
		p2 = Person(test_home, 2)
		p3 = Person(test_home, 3)
		p4 = Person(test_home, 4)
		p5 = Person(test_home, 5)
		p6 = Person(test_home, 6)
		p7 = Person(test_home, 7)

		p0.friends = [p1, p2, p3, p4]
		p1.friends = [p0, p2, p4, p6]
		p2.friends = [p0, p1]
		p4.friends = [p0, p1]
		p5.friends = [p6]
		p6.friends = [p1, p5, p7]
		p7.friends = [p6]

		p0.family = [p6]
		p1.family = [p6, p5]
		p2.family = [p4, p3]
		p3.family = [p2]
		p4.family = [p2]
		p5.family = [p1]
		p6.family = [p0, p1]

		p0.workplace = test_wp
		p1.workplace = test_wp
		p2.workplace = test_wp
		p3.workplace = test_wp
		p4.workplace = test_wp
		p6.workplace = test_wp
		p7.workplace = test_wp

		p0.coworkers = [p2, p3]
		p1.coworkers = [p2, p6]
		p2.coworkers = [p0, p1, p7]
		p3.coworkers = [p0, p4]
		p4.coworkers = [p3]
		p6.coworkers = [p1]
		p7.coworkers = [p2]

		p0.set_current_location(test_wp)
		# p1.set_current_location(test_wp)
		p2.set_current_location(test_wp)
		p3.set_current_location(test_wp)
		p4.set_current_location(test_wp)
		p7.set_current_location(test_wp)

		p5.partners = [p6]
		p6.partners = [p5]

		p0.work_schedule = (tconv('09'), tconv('05'))
		p1.work_schedule = (tconv('09'), tconv('05'))
		p2.work_schedule = (tconv('09'), tconv('05'))
		p3.work_schedule = (tconv('09'), tconv('05'))
		p4.work_schedule = (tconv('09'), tconv('05'))
		p6.work_schedule = (tconv('10'), tconv('05'))
		p7.work_schedule = (tconv('09'), tconv('05'))

		# activities
		tmp = Activity('talking')
		tmp.to = p2
		p0.currentActivity = tmp
		tmp = Activity('talking')
		tmp.to = p0
		p2.currentActivity = tmp
		
		# 0 and 5 are not in the same place. their affinity should be zero
		assert(p0.affinity(p5) == 0)
		assert(p0.affinity(p6) == 0)

		# what is the affinity between p0 and p7?
		zs_aff = p0.affinity(p7)
		np.testing.assert_almost_equal(zs_aff,0.1)

		#between 0 and 2?
		zt_aff = p0.affinity(p2)
		np.testing.assert_almost_equal(zt_aff,0.72)

		#more complex requires some movement
		p0.set_current_location(test_home)
		zf_aff = p0.affinity(p5)
		np.testing.assert_almost_equal(zf_aff, 0.04444444444444446)
		p0.set_current_location(test_wp)



	def test_action_transition(self):
		# use the map reader since making one of these by hand is going to be a pain
		from Map import MapReader
		mr = MapReader(PUBLIC_BLOCK_SIZE=(2, 2), CAPACITY_PER_PIXEL=2, TIME_STEP_PER_PIXEL=2)
		m = mr.create_map_from_file('../test_map_small.png')
		test_home = m.loc_list[42]  # this is the home which is down-right of the top-left home (9th cell if counting left-right, top-bottom)
		test_wp = m.loc_list[175]  # this is the shop in the bottom right corner
		test_wp1 = m.loc_list[119]  # this is the L-shaped office

		np.random.seed(0)

		p0 = Person(test_home, m)
		p1 = Person(test_home, m)
		p2 = Person(test_home, m)
		p3 = Person(test_home, m)
		p4 = Person(test_home, m)
		p5 = Person(test_home, m)
		p6 = Person(test_home, m)
		p7 = Person(test_home, m)

		p0.friends = [p1, p2, p3, p4]
		p1.friends = [p0, p2, p4, p6]
		p2.friends = [p0, p1]
		p4.friends = [p0, p1]
		p5.friends = [p6]
		p6.friends = [p1, p5, p7]
		p7.friends = [p6]

		p0.family = [p6]
		p1.family = [p6, p5]
		p2.family = [p4, p3]
		p3.family = [p2]
		p4.family = [p2]
		p5.family = [p1]
		p6.family = [p0, p1]

		p0.workplace = test_wp
		p1.workplace = test_wp
		p2.workplace = test_wp
		p3.workplace = test_wp
		p4.workplace = test_wp
		p6.workplace = test_wp
		p7.workplace = test_wp

		p0.coworkers = [p2, p3]
		p1.coworkers = [p2, p6]
		p2.coworkers = [p0, p1, p7]
		p3.coworkers = [p0, p4]
		p4.coworkers = [p3]
		p6.coworkers = [p1]
		p7.coworkers = [p2]

		p0.set_current_location(test_wp)
		# p1.set_current_location(test_wp)
		p2.set_current_location(test_wp)
		p3.set_current_location(test_wp)
		p4.set_current_location(test_wp)
		p7.set_current_location(test_wp)

		p5.partners = [p6]
		p6.partners = [p5]

		p0.work_schedule = (tconv('09'), tconv('05'))
		p1.work_schedule = (tconv('09'), tconv('05'))
		p2.work_schedule = (tconv('09'), tconv('05'))
		p3.work_schedule = (tconv('09'), tconv('05'))
		p4.work_schedule = (tconv('09'), tconv('05'))
		p6.work_schedule = (tconv('10'), tconv('05'))
		p7.work_schedule = (tconv('09'), tconv('05'))

		# activities
		tmp = Activity('talking')
		tmp.to = p2
		p0.currentActivity = tmp
		tmp = Activity('talking')
		tmp.to = p0
		p2.currentActivity = tmp

		for t in range(tconv('09'),tconv('09:06')):
			for p in [p0, p1, p2, p3, p4, p5, p6, p7]:
				p.action_transition(t)#do 5 transitions per person for 5 different values of t
		pass
