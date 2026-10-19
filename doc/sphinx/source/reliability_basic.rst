.. 	@author: jringelstein	
.. reliability_basic:

###########################
Basic Reliability functions
###########################

.. note:: More details can be found in the `Jupyter Doc on Reliability in pandaict <https://recode.pages.fraunhofer.de/pandaict/jupyter/_build/html/pandaICT_reliability_metrics.html>`_

.. note:: MTTR/MTBF and Bit error rate calculation does currently **not** work for any routing algorithm which involves implicit or explicit copying of information items in the network. 
    Examples for this are FLOODING or radio networks with multicast transmission. 

MTBF and MTTR 
=============

.. _calc_MTBF_route:
.. autofunction:: pandaict.reliability.mtbf_mttr.calc_mtbf_route	

.. _calc_MTBF_MTTR_route:
.. autofunction:: pandaict.reliability.mtbf_mttr.calc_mtbf_mttr_route
	
.. _calc_MTBF_MTTR_by_lup:
.. autofunction:: pandaict.reliability.mtbf_mttr.calc_mtbf_mttr_by_lup

Bit error rate
==============

.. _calc_ber_route:
.. autofunction:: pandaict.reliability.ber.calc_ber_route

.. _calc_ber_by_lup:
.. autofunction:: pandaict.reliability.ber.calc_ber_by_lup





	
    