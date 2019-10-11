"""
This file defines the "person" class and all of the relevant information.

Each person needs all of the following:

	home
	age
	currentLocation (defaults to home)
	currentActivity (defaults to Idle [see Activity.py])
	place of work\school*
	list of preferred activities*
	family
		parent 0 (generally, mother, but we'll allow for nontraditional couples)*
		parent 1 (generally, father, but we'll allow for nontraditional couples)*
		children*
		(note with the above three that for the purpose of this simulation (not including relatedness) the only thing that actually matters is who a person interacts with, so their biological parents are irrelevant)
		partners (people who this person is likely to have sex with, there can be more than one)*
	friends*
	coworkers/schoolmates (that the person *actually* interacts with on a daily basis)*
	diseases currently inflicted with*
		symptoms shown (for each disease)
			any modifiers to behavior because of symptoms
	diseases immune to*
		possibly seperated by why (no for now)
			vaccine
			previous exposure
			etc

* - can be null or empty

___

note that the purpose of the friends/family/coworkers network is to tell the algorithm who you're *likely* to interact with.
a person is most likely to interact with their immediate friends and family, and as the network goes out in shells the probability decrases.
essentially, we're modeling the probability of interacting between two people as a decaying function of the geodesic distance between the people

"""
import Activity


class Person:


	"""
	We only require that each person has a home. If that's all they have they never actually leave except to go to the store to get food.
	"""
	def __init__(self, home, age):
		# general demo/biographical info
		self.home = home
		self.age = age
		self.currentLocation = home
		self.currentActivity = Activity.Idle()#TODO: write the activity classes
		self.workplace = None  # or school
		self.activities = []
		self.family = {'parents': [],
					   'children': [],
					   'partners': []}
		self.friends = []
		self.coworkers = []  # or schoolmates

		# infection info
		self.diseasesInfectedBy = []
		self.immunities = []
