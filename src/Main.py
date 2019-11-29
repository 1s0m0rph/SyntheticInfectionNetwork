from Simulation import *
np.random.seed(0)

s = Simulation()

#setup map reader
v = False
mr = MapReader(PUBLIC_BLOCK_SIZE=(2, 2), CAPACITY_PER_PIXEL=2, TIME_STEP_PER_PIXEL=2)
map_fname = '../test_map_small.png'
s.read_map_from_image(mr,map_fname)

#setup diseases
dis = fast_diseases
s.set_diseases(dis)

#setup pop builder
pb = PopulationBuilder(s.map,100)
pb.set_num_friends_distribution(lambda possible_friends: min(max(int(np.random.normal(7,5)),0),possible_friends))
pb.set_num_coworkers_distribution(lambda possible: min(max(int(np.random.normal(7,5)),0),possible))
s.create_population(pb)

#YEET
s.full_simulation(verbose=True)
print('SUMMARY\n')
for person in s.population:
	for disease in person.disease_state:
		if person.disease_state[disease] not in DISEASE_STATES_INITIAL:
			print(str(person) + ('(DECEASED)' if person.is_dead else '') + ':')
			print('final location: ' + str(person.currentLocation))
			print('final activity: ' + str(person.currentActivity))
			print('disease states: ' + str(person.disease_state))
			print('friends: ' + str(person.friends))
			print('coworkers: ' + str(person.coworkers))