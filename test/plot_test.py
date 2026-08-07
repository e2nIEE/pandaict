# -*- coding: utf-8 -*-
'''
Created on 21.03.2024
@author: gbanerjee
'''

from core_test import *
from pandaict.networks.test_networks import create_testnet1
from pandaict.plot import create_plot, __create_g__
import PIL
from PIL import Image, ImageChops
import tempfile
import os

#plot net is depending on the index of the net at "create_test_ict_net" return

class Plot_Test():    
    
    # NOTE: all function names to be executed by unittest MUST START with "test" !             
    def test_plot_dev(self, utest):
        net1 = create_testnet1()
        plt = create_plot(net1, draw_type='dev')

        
        # plt.savefig(r'C:\Users\gbanerjee\GIt_Hub_Lab\pandaict\test\plt_dev.png')
        
        # save the created figure as tempfile
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:    
            plt.savefig(tmp_file.name)
             
            image1 = Image.open(tmp_file.name)
            # load the saved figure to compare
            image2 = Image.open(os.path.dirname(os.path.abspath(__file__)) + os.sep + 'plt_dev.png') 
            # compare the size
            assert image1.size == image2.size 
            # compare the content
            diff = ImageChops.difference(image1, image2)
            utest.assertTrue(diff.getbbox() is None)
        
           
    def test_plot_app(self, utest):
        net1 = create_testnet1()
        plt = create_plot(net1, draw_type='app')

        # plt.savefig(r'C:\Users\gbanerjee\GIt_Hub_Lab\pandaict\test\plt_app.png')
        
        # save the created figure as tempfile
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:    
            plt.savefig(tmp_file.name)
             
            image1 = Image.open(tmp_file.name)
            # load the saved figure to compare
            image2 = Image.open(os.path.dirname(os.path.abspath(__file__)) + os.sep + 'plt_app.png') 
            # compare the size
            assert image1.size == image2.size 
            # compare the content
            diff = ImageChops.difference(image1, image2)
            utest.assertTrue(diff.getbbox() is None)

    
    def test_graph_dev(self, utest):
        net1 = create_testnet1()
        G, edge_labels = __create_g__(None, 'dev', net1)
        
        # Iterate through nodes
        for node_g, node_name in zip(G.nodes(), ['Node1', 'Node2', 'Conv1', 'Conv2', 'Conv3', 'CC', 'PQ1', 'PQ2', 'SC', 'PC1', 'PC2']):
            assert node_g  == node_name

        # Iterate through edges
        for edge, edge_compare in zip(G.edges(), [('Node1', 'CC'), ('Node1', 'Node2'), ('Node2', 'Conv1'),
                                    ('Node2', 'Conv2'), ('Node2', 'Conv3'), ('Node2', 'PQ1'), 
                                    ('Node2', 'PQ2'), ('Conv1', 'PC1'), ('Conv2', 'PC2'), ('Conv3', 'SC')]):
           utest.assertTrue(edge == edge_compare)        
    
    def test_graph_app(self, utest):
        net1 = create_testnet1()
        G, edge_labels = __create_g__(None, 'app', net1)
        
        # Iterate through nodes
        for node_g, node_name in zip(G.nodes(), ['Conv1', 'Conv2', 'Conv3', 'CC', 'PQ1', 'PQ2', 'SC', 'PC1', 'PC2']):
            assert node_g  == node_name

        # Iterate through edges
        for edge, edge_compare in zip(G.edges(), [('Conv1', 'CC'), ('Conv1', 'PC1'), ('Conv2', 'CC'), ('Conv2', 'PC2'), 
                                                  ('Conv3', 'CC'), ('Conv3', 'SC'), ('CC', 'PQ1'), ('CC', 'PQ2')]):
           utest.assertTrue(edge == edge_compare)
           
             


