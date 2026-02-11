---
layout: splash
title: "pandaict"
permalink: /
header:
  overlay_image: "/images/home/background.png"
  cta_label: "<i class='fas fa-download'></i> Install Now"
  cta_label2: "<i class='fas fa-envelope'></i> Get Updates"
  cta_url: "/start/#install"
  cta_url2: "/contact/#list"
  subtitle: <a href='https://pypi.python.org/pypi/pandaict'> <img src='{{"https://img.shields.io/pypi/pyversions/pandaict.svg"}}'></a>
shields:
- icon: https://badge.fury.io/py/pandaict.svg
  url: https://pypi.python.org/pypi/pandaict
- icon: https://img.shields.io/pypi/pyversions/pandaict.svg
  url: https://pypi.python.org/pypi/pandaict
- icon: https://readthedocs.org/projects/pandaict/badge/
  url: https://pandaict.readthedocs.io/en/latest/
- icon: https://codecov.io/github/e2nIEE/pandaict/coverage.svg?branch=develop
  url: https://codecov.io/github/e2nIEE/pandaict?branch=master
- icon: https://api.codacy.com/project/badge/Grade/e2ce960935fd4f96b4be4dff9a0c76e3
  url: https://app.codacy.com/gh/e2nIEE/pandaict?branch=master
- icon: images/home/shield_bsd.svg
  url: https://github.com/e2nIEE/pandaict/blob/master/LICENSE
- icon: 'https://api.reuse.software/badge/github.com/fsfe/reuse-tool'
  url: https://api.reuse.software/info/github.com/fsfe/reuse-tool

excerpt: An easy to use open source tool for ICT system modeling and analysis compatible to power system modeling with pandapower.
feature_row:
- image_path: "/images/home/pandaict_conn.png"
  title: ICT System Modeling
  excerpt: Includes physical, end-to-end connection and information layer modeling
  url: about/#modeling
  btn_class: btn--primary
  btn_label: Learn More
- image_path: "/images/home/pandaict_smartgrid2.png"
  title: ICT Network Analysis
  excerpt: Supports Routing, Bandwidth and Data Volume calculation, and Monte-Carlo reliability simulation. 
  url: about/#analysis
  btn_class: btn--primary
  btn_label: Learn More
- image_path: "/images/home/osi_symbol.png"
  title: Free and Open
  excerpt: Published under BSD 3-clause License and therefore free to use, modify and share
    however you want.
  url: https://github.com/e2nIEE/pandaict
  btn_class: btn--primary
  btn_label: Explore on github
---

To get started with pandaict, just

1. Install pandaict through pip:
    ```
pip install pandaict
    ```

2. Create a simple network
    ```python
import pandaict as pi
net = pi.create_empty_network()
dserv, aserv = pi.create_ict_devapp(net)
dcli, acli  = pi.create_ict_devapp(net)
node = pi.create_ict_node(net, pi.NodeType.ROUTER)
pi.create_ict_link(net, from_elt=dserv, to_elt=node, link_type='Fiber')
pi.create_ict_link(net, from_elt=node, to_elt=dcli, link_type='LAN1000')
conn = pi.create_ict_connection(net, from_app=aserv, to_app=acli, protocol='TCP')
    ```
        
3. Run a route calculation:
    ```python
import pandaict.topology.routing as piroute
routes = piroute.calc_routes_for_connection(net, conn)
    ```
        
4. And check the results:
    ```python
print(str(routes))
    ```

But of course pandaict can do much more than that - find out what on this page!

{% include feature_row id="intro" type="center" %}
    
{% include feature_row %}
