from PersonState import *


test_home = Location(8,'home')
test_wp = Location(300,'casino')

p0 = Person(test_home,0)
p1 = Person(test_home,1)
p2 = Person(test_home,2)
p3 = Person(test_home,3)
p4 = Person(test_home,4)
p5 = Person(test_home,5)
p6 = Person(test_home,6)
p7 = Person(test_home,7)

p0.friends = [p1,p2,p3,p4]
p1.friends = [p0,p2,p4,p6]
p2.friends = [p0,p1]
p4.friends = [p0,p1]
p5.friends = [p6]
p6.friends = [p1,p5,p7]
p7.friends = [p6]

p0.workplace = test_wp
p1.workplace = test_wp
p2.workplace = test_wp
p3.workplace = test_wp
p4.workplace = test_wp
p6.workplace = test_wp
p7.workplace = test_wp

p0.coworkers = [p2,p3]
p1.coworkers = [p2,p6]
p2.coworkers = [p0,p1,p7]
p3.coworkers = [p0,p4]
p4.coworkers = [p3]
p6.coworkers = [p1]
p7.coworkers = [p2]

p0.set_current_location(test_wp)
# p1.set_current_location(test_wp)
p2.set_current_location(test_wp)
p3.set_current_location(test_wp)
p4.set_current_location(test_wp)
p7.set_current_location(test_wp)

#0 and 5 are not in the same place. their affinity should be zero
assert(p0.affinity(p5) == 0)

#what is the affinity between p0 and p7?
zs_aff = p0.affinity(p7)
print(zs_aff)