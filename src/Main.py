from Simulation import *

SIM_CONFIG = 'small'
pop_size = 150
time_step_per_dump = 60
# SIM_CONFIG = '750 full'

dump_file_infection = 'small_test_all_diseases_inf_pop150.psv'
dump_file_map = 'small_test_all_diseases_map_pop150.psv'
dump_files = [dump_file_map,dump_file_infection]
dis = [virus_0,virus_1,STD_0,competitive_disease_0]

dump_type = ['map','infection']

s = Simulation(infodump_file=dump_files, ensure_non_immune_patient_zero=True, infodump_type=dump_type, time_steps_per_infodump=time_step_per_dump)

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
s.create_population(pb)

#YEET
s.full_simulation(verbose=True)
print('SUMMARY\n')
for disease in s.diseases:
	print('for ' + disease.name + ':')
	disease_state_counts = {state:0 for state in DISEASE_STATES_LIST}
	for person in s.population:
		disease_state_counts[person.disease_state[disease]] += 1

	for state in DISEASE_STATES_LIST:
		print(state + ': ' + str(disease_state_counts[state]) + ' total')

	print()