"""
This will calculate the R_0 values empirically for the given diseases
"""

from Simulation import *

diseases_to_measure = [virus_1]
max_days = 30
with_vaccination = False												#should we allow these diseases to have any of the population vaccinated in our measurement
SIM_CONFIG = 'small'
pop_size = 150


if not with_vaccination:
	for disease in diseases_to_measure:
		disease.vaccination_rate = 0.#no one's vaccinated in this case

for disease in diseases_to_measure:
	dis = [disease]
	s = Simulation()

	if SIM_CONFIG == 'full':
		#setup map reader
		mr = MapReader()
		map_fname = 'test_map_0.png'
		s.read_map_from_image(mr,map_fname)

	elif SIM_CONFIG == 'small':
		# setup map reader
		mr = MapReader(PUBLIC_BLOCK_SIZE=(2, 2), CAPACITY_PER_PIXEL=2, TIME_STEP_PER_PIXEL=2)
		map_fname = 'test_map_small.png'
		s.read_map_from_image(mr, map_fname)

	# setup diseases
	s.set_diseases(dis)

	# setup pop builder
	pb = PopulationBuilder(s.map, pop_size)
	pb.set_num_friends_distribution(lambda possible_friends: min(max(int(np.random.normal(6, 3)), 0), possible_friends))
	pb.set_num_coworkers_distribution(lambda possible: min(max(int(np.random.normal(6, 5)), 0), possible))
	pb.set_partners_distribution(lambda num_people_in_house: min(int(coinflip(0.15)),num_people_in_house))
	s.create_population(pb)

	#YEET
	r0 = s.full_simulation(verbose=True,time_limit=max_days,store_R_0s=True)[disease]

	print('Measured R_0 for ' + disease.name + ': ' + str(r0))