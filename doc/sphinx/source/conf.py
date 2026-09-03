'''
 @author: jringelstein
'''   

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'pandaICT'
copyright = '2024-2026 by Fraunhofer IEE, Kassel. All rights reserved'
author = 'Fraunhofer IEE'
release = '1.2.1preview'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [   
    'sphinx_rtd_theme','sphinx.ext.autodoc', 'sphinx.ext.napoleon'
]
templates_path = ['_templates']
exclude_patterns = []

# The master toctree document.
master_doc = 'index'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_theme_options = {
    'navigation_depth': 2,
    'includehidden': True,
    'titles_only': False,
    'collapse_navigation': True,
    'sticky_navigation': True,
}
html_logo = "../pics/pict_small.jpg"

import sys
import os
sys.path.insert(0, os.path.abspath('..\\..\\..\\src\\pandaict\\'))
sys.path.insert(0, os.path.abspath('..\\..\\..\\src\\'))
sys.path.insert(0, os.path.abspath('..\\..\\..\\'))
print("***** CWD: "+str(os.getcwd()))
print("***** sys.path: "+str(sys.path))