# -*- coding: utf-8 -*-
"""
Created on Tue May 21 15:21:35 2024

@author: gbanerjee
"""

from basics_test import *
from plot import create_plot, __create_g__
import PIL
from PIL import Image

 #plot net is depending on the index of the net at "create_test_ict_net" return
B = Basics_Test()
net1 = B.create_testnet1()
net2 = B.create_testnet2()
# create_plot(net1, draw_type='dev')
# create_plot(net1, draw_type='app')

class TestPlotScaling(unittest.TestCase):    
    
    # NOTE: all function names to be executed by unittest MUST START with "test" !     
        
    def test_plot_dev(self):
        plt = create_plot(net1, draw_type='dev')

        # Get the current figure from plt
        fig = plt.gcf()  # gcf - Get Current Figure
        
        # Retrieve the size of the rendered figure
        width, height = fig.get_size_inches()
        
        # Check if the size is as expected
        self.assertEqual(width, 6.4)
        self.assertEqual(height, 4.8)  
        
        #ToDo: memory size compare, 
        #Save figure as .PNG or .SVG and compare the saved file (by importing) and compare the new generated files
            
    def test_plot_app(self):
        plt = create_plot(net1, draw_type='app')

        # Get the current figure from plt
        fig = plt.gcf()  # gcf - Get Current Figure
        
        # Retrieve the size of the figure
        width, height = fig.get_size_inches()
    
        
        # Check if the size is as expected
        self.assertEqual(width, 6.4)
        self.assertEqual(height, 4.8)
        
        #ToDo: memory size compare, 
        #Save figure as .PNG or .SVG and compare the saved file (by importing) and compare the new generated files
    
    def test_graph_dev(self):
        G, edge_labels = __create_g__(None, 'dev', net1)
        
        # Iterate through nodes
        for node_g, node_name in zip(G.nodes(), ['Node1', 'Node2', 'Conv1', 'Conv2', 'Conv3', 'CC', 'PQ1', 'PQ2', 'SC', 'PC1', 'PC2']):
            assert node_g  == node_name

        # Iterate through edges
        for edge, edge_compare in zip(G.edges(), [('Node1', 'CC'), ('Node1', 'Node2'), ('Node2', 'Conv1'),
                                    ('Node2', 'Conv2'), ('Node2', 'Conv3'), ('Node2', 'PQ1'), 
                                    ('Node2', 'PQ2'), ('Conv1', 'PC1'), ('Conv2', 'PC2'), ('Conv3', 'SC')]):
           assert edge == edge_compare
           
    #ToDo: for APP
    
    # #idea
    # def test_create_g(self):
    #     G = #call G create function
    #     iterate the G ; compare node number and names, same for edges test
              

if __name__ == '__main__':
    unittest.main()

