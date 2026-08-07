.. 	@author: jringelstein	
.. _std_types:

########################
Standard Types and Enums
########################


Basic standard types
====================


.. _add_basic_std_types:

.. autofunction:: pandaict.std_types.add_basic_std_types


Link types
----------

.. note:: Link types currently do not have an extra flag for bidirectionality. A link is considered bidirectional if its bandwith_Mbps is a tuple, otherwise unidirectional.  

.. tabularcolumns:: |l|l|l|l|l|l|l|l|
.. csv-table:: 
   :file: linktypes.csv
   :delim: ;
   :widths: 60, 15, 15, 15, 15, 15, 15, 15
   
Protocol types
--------------

.. tabularcolumns:: |l|l|l|l|
.. csv-table::
   :file: protocoltypes.csv
   :delim: ;
   :widths: 60, 15, 50, 50 
	

Adding and creating standard types
==================================

.. note:: Link types currently do not have an extra flag for bidrectionality. A link is considered bidirectional if its bandwith_Mbps is a tuple, otherwise unidirectional. 

.. _create_std_type:

.. autofunction:: pandaict.std_types.create_std_type

.. _create_std_types:

.. autofunction:: pandaict.std_types.create_std_types

Adding custom enums 
===================

.. _add_custom_enum:

.. autofunction:: pandaict.enums.add_custom_enum