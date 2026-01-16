.. 	@author: jringelstein

===================
Element Identifiers
===================


There are two ways to identify elements of a pandaict net: the pandaict element notation and uuid's. Depending on user selection and function, 
pandaict functions may accept either notation, and return element identifiers using that same notation.   

pandaict element notation
=========================

This way of identification uses a (str, int) tuple, where the string indicates the element type and the int the index in the ict net element table.
Allowed values for the element types are: 'node', 'link', 'device', 'conn' and 'app'. In case a mapping to a pandapower element is done, 
possible additional allowed values include pandapower element types like 'bus', 'line', 'switch', 'trafo' and 'sgen'.  

This notation is the standard way of identifying elements in pandaict. In particular, it is used in the internal element tables and for saving networks 
in json format. 

UUIDs
=====

UUID identification is possible on user request. On element creation, the user may specify a self-selected UUID. If none is provided, a UUID is generated 
using the uuid.uuid4() function. Predefined standard element types (stored in std_types) are also equipped with UUIDs which are hard coded. 


Identifier Conversion 
=====================

There are several functions to convert between identifier formats: 

.. _identifier_conversion:
.. autofunction:: pandaict.uuid2elt
.. autofunction:: pandaict.elt2uuid
  
