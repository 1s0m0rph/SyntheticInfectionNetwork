"""
This is where the actual simulation code will go. This is the code that tells all the other stuff when to do what.

It keeps track of all the people, all the locations (and their implicit map), and all of the diseases
It uses this information to go step-by-step and see how the infection(s) progress(es)
"""

from SINUtil import *
from PersonState import Person, Location, Activity, PopulationBuilder
from Map import Map, MapReader
from Disease import *

class Simulation:

	def __init__(self):

		self.diseases = all_diseases	#default to everything
		self.population = []
		self.map = None
		self.map_img_reference = ""	#where is the image we should map this map to?

	def read_map_from_image(self,mr:MapReader,fname:str):
		self.map = mr.read_from_file(fname)

	def set_diseases(self,to:list):
		self.diseases = to

	def create_population(self,pb: PopulationBuilder):
		pb.set_diseases_present(self.diseases)
		self.population = pb.create_population()