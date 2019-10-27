from unittest import TestCase
from PersonState import *
import numpy as np

class TestPerson(TestCase):
	test_home = Location(8, 'home')
	test_wp = Location(300, 'casino')

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
	p1.family = [p6,p5]
	p2.family = [p4,p3]
	p3.family = [p2]
	p4.family = [p2]
	p5.family = [p1]
	p6.family = [p0,p1]

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

	def test_affinity(self):
		# 0 and 5 are not in the same place. their affinity should be zero
		assert(TestPerson.p0.affinity(TestPerson.p5) == 0)
		assert(TestPerson.p0.affinity(TestPerson.p6) == 0)

		# what is the affinity between p0 and p7?
		zs_aff = TestPerson.p0.affinity(TestPerson.p7)
		np.testing.assert_almost_equal(zs_aff,0.1)

		#between 0 and 2?
		zt_aff = TestPerson.p0.affinity(TestPerson.p2)
		np.testing.assert_almost_equal(zt_aff,0.72)

		#more complex requires some movement
		TestPerson.p0.set_current_location(TestPerson.test_home)
		zf_aff = TestPerson.p0.affinity(TestPerson.p5)
		np.testing.assert_almost_equal(zf_aff, 0.06388888888888888)
		TestPerson.p0.set_current_location(TestPerson.test_wp)



	def test_action_transition(self):
		TestPerson.p0.action_transition(0)
		pass
