'''
Created on 8.03.2024
@authors: brequardt, jringelstein
'''

import unittest
from codetiming import Timer
from core_test import Core_Test
from plot_test import Plot_Test
from reliability_tests.reliability_test import ReliabilityTest

class PandaICT_Test(unittest.TestCase):    
    
    # NOTE: all function names to be executed by unittest MUST START with "test" ! 
    core_tester = Core_Test()
    plot_tester = Plot_Test()
    reli_tester = ReliabilityTest()
    
    # ******* Core tests ********
    
    def test_create(self):
        self.core_tester.test_create_ict_net(self)
    
    def test_saveload(self):
        self.core_tester.test_save_load(self)
    
    def test_inspect(self):
        self.core_tester.test_inspect_ict_net(self)  
    
    def test_user_input_checks(self):
        self.core_tester.test_user_input_checks(self)
    
    def test_lup_table_calc(self):
        self.core_tester.test_lup_table_calc(self)

    def test_calc_app_vol_MB(self):
        self.core_tester.test_calc_app_vol_MB(self)
        
    def test_sorted_link_calc(self):
        self.core_tester.test_sorted_link_calc(self)
    
    def test_mtbf_mttr_ber_calc(self):    
        self.core_tester.test_mtbf_mttr_ber_calc(self)
    
    def test_custom_type_creation(self):    
        self.core_tester.test_custom_type_creation(self)
    
    def test_is_connection_possible(self):
        self.core_tester.test_is_connection_possible(self)
    
    def test_ip_support(self):
        self.core_tester.test_ip_support(self)
        
    def test_exceltools(self):
        self.core_tester.test_exceltools(self)

    # ******* Plotting tests ********
    
    def test_plot_dev(self):
        self.plot_tester.test_plot_dev(self)
    
    def test_plot_app(self):
        self.plot_tester.test_plot_app(self)
    
    def test_graph_dev(self):
        self.plot_tester.test_graph_dev(self)
    
    def test_graph_app(self):
        self.plot_tester.test_graph_app(self)
        
    
    # ******* Reliability tests ********
    
    def test_reliability(self):
        self.reli_tester.set_up_class()                        
        self.reli_tester.test_criticality_parallel_rates(self)
        self.reli_tester.test_criticality_series_rates(self)                            
        self.reli_tester.test_criticality_symmetric(self)
        self.reli_tester.test_empirical_reliability(self)
        self.reli_tester.test_mtbf_mttr(self)
        self.reli_tester.test_mtbf_mttr_serial_execution(self)      
        
        print("Test with python fallback...")
        self.reli_tester.set_test_python_fallback(True)   
        self.reli_tester.test_criticality_series_rates(self) 
        self.reli_tester.test_mtbf_mttr(self)          
        self.reli_tester.set_test_python_fallback(False)
          

if __name__ == '__main__':
    #pitest = PandaICT_Test()
    #pitest.test_reliability()
    #print("Test OK")
    unittest.main()
    