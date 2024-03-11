'''
# Copyright (c) 2016-2023 by University of Kassel and Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel. All rights reserved.

Created on 8.03.2024

@authors: brequardt, jringelstein
'''

import unittest
from basics_test import Basics_Test

class PandaICT_Test(unittest.TestCase):    
    
    # NOTE: all function names to be executed by unittest MUST START with "test" ! 
    
    def test_basic(self):
        tester = Basics_Test()
        tester.test_create_ict_net(self)
        
        
    def test_example(self):
        self.assertEqual('PandaICT', 'PandaICT')
              

if __name__ == '__main__':
    unittest.main()