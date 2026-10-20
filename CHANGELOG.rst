Change Log
=============

[1.0.0] - 2024-07-25
-------------------------------
- [ADDED] Basic datamodel with physical/logical model, protocols and info items
- [ADDED] Network creation, safe and load as json 
- [ADDED] Basic visualisation with device/app (physical/logical) views 
- [ADDED] User error checks and network inspection
- [ADDED] Basic connection path calculation and link bandwith usage calculation
- [ADDED] Standard reference example
- [ADDED] Jupyter notebook and Sphinx documentation 


[1.1.0] - 2024-09-10
-------------------------------
- [FIXED] Load to json bug that caused wrong format for connection peers in loaded networks
- [ADDED] Reliability: calculation of MTBF, MTTR and bit error rate for ICT connections
- [ADDED] Calculation of data volume needed for a connection
- [ADDED] Connectivity check
- [ADDED] Fetching of links for a connection, sorted by adjustable item (e.g. latency)
- [ADDED] Support for IP networks, IP routing table calculation for nodes
- [ADDED] Updated docs

[1.1.1] - 2024-10-24
-------------------------------
- [FIXED] Compatibility to pp_pict_connector

[1.1.2] - 2024-10-24
-------------------------------
- [FIXED] Corrected documentation
- [ADDED] Verbose mode for diagnosis.inspect()
- [CHANGED] reliability: calc_MTBF_route, calc_MTBF_MTTR_route and calc_MTBF_MTTR_by_lup 
            renamed to calc_mtbf_route, calc_mtbf_mttr_route and calc_mtbf_mttr_by_lup
- [FIXED] Saving of nets with std_type
   

