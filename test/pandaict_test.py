'''
# Copyright (c) 2016-2023 by University of Kassel and Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel. All rights reserved.

Created on 8.03.2024

@authors: brequardt, jringelstein
'''

import unittest
from core_test import Core_Test

class PandaICT_Test(unittest.TestCase):    
    
    # NOTE: all function names to be executed by unittest MUST START with "test" ! 
    tester = Core_Test()
    
    def test_create(self):        
        self.tester.test_create_ict_net(self)
    
    def test_saveload(self):
        self.tester.test_save_load(self)
    
    def test_inspect(self):
        self.tester.test_inspect_ict_net(self)  
    
    def test_user_input_checks(self):
        self.tester.test_user_input_checks(self)
    
    def test_lup_table_calc(self):
        self.tester.test_lup_table_calc(self)            
          

if __name__ == '__main__':
    unittest.main()