import unittest
import numpy as np
from SMU_CS606_Wildlife_Protection.PSO.multi_agent_search import PSODroneSearch

class TestPSODroneSearch(unittest.TestCase):
    def setUp(self):
        self.search = PSODroneSearch()
    
    def test_initialization(self):
        """Test if initialization creates valid state"""
        self.assertEqual(self.search.particles.shape, (self.search.NUM_PARTICLES, 2))
        self.assertTrue(np.all(self.search.particles >= 0))
        self.assertTrue(np.all(self.search.particles < self.search.AREA_SIZE))
    
    def test_fitness_function(self):
        """Test if fitness function returns expected values"""
        # Test particle at animal location
        test_particle = self.search.animal_location
        score = self.search.fitness_function(test_particle, self.search.MAX 