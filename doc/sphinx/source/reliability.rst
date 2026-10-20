.. _reliability:

#####################
Reliability functions
#####################

.. note:: More details can be found in the `Jupyter Doc on Reliability in pandaICT <https://recode.pages.fraunhofer.de/pandaict/jupyter/_build/html/pandaICT_reliability_metrics.html>`_

.. note:: MTTR/MTBF and Bit error rate calculation does currently **not** work for any routing algorithm which involves implicit or explicit copying of information items in the network. 
    Examples for this are FLOODING or radio networks with multicast transmission. 

MTBF and MTTR 
=============

.. _calc_MTBF_route:
.. autofunction:: pandaict.reliability.mtbr_mttf.calc_MTBF_route	

.. _calc_MTBF_MTTR_route:
.. autofunction:: pandaict.reliability.mtbr_mttf.calc_MTBF_MTTR_route
	
.. _calc_MTBF_MTTR_by_lup:
.. autofunction:: pandaict.reliability.mtbr_mttf.calc_MTBF_MTTR_by_lup

Bit error rate
==============

.. _calc_ber_route:
.. autofunction:: pandaict.reliability.ber.calc_ber_route

.. _calc_ber_by_lup:
.. autofunction:: pandaict.reliability.ber.calc_ber_by_lup





	
    