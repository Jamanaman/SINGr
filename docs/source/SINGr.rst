SINGr package
=============

Module contents
---------------

SINGr is structured with the following submodules:

* ``SINGr.runner``

  * main high level submodule for users to run the fully automated features of the package after they have composed the simulation structures to be run through the workflows

* ``SINGr.composition``

  * provides the ``Composition`` data structure for composing simulations as well as the recursive tree unit ``CommunicationNet`` which is used to allow recursive construction of netlists

* ``SINGr.model``

  * implements the objects which allow the user to relatively naively construct models of specific subcircuit units direct from files or configuration parameters including IBIS models and RLCG distributed transmission lines

* ``SINGr.net_builder``

  * implements the netlist building functionality of the package built around input, output, terminations and transmission lines.

* ``SINGr.analysis``

  * wrapper functions which orchestrate the various analyses and also allows a user to provide provide their own data for analysis, provided that it is in a long DataFrame format with a time series 

* ``SINGr.eye_tools``

  * implements eye analysis and eye diagram generation functionality

* ``SINGr.signal_tools``

  * implements waveform analysis and general signal processing functionality 

* ``SINGr.sim_tools``

  * implements utility functions to abstract simulation construction and configuration processes 

.. automodule:: SINGr
   :members:
   :show-inheritance:
   :undoc-members:

Submodules
----------

SINGr.analysis module
---------------------

.. automodule:: SINGr.analysis
   :members:
   :show-inheritance:
   :undoc-members:

SINGr.composition module
------------------------

.. automodule:: SINGr.composition
   :members:
   :show-inheritance:
   :undoc-members:

SINGr.eye\_tools module
-----------------------

.. automodule:: SINGr.eye_tools
   :members:
   :show-inheritance:
   :undoc-members:

SINGr.model module
------------------

.. automodule:: SINGr.model
   :members:
   :show-inheritance:
   :undoc-members:

SINGr.net\_builder module
-------------------------

.. automodule:: SINGr.net_builder
   :members:
   :show-inheritance:
   :undoc-members:

SINGr.signal\_tools module
--------------------------

.. automodule:: SINGr.signal_tools
   :members:
   :show-inheritance:
   :undoc-members:

SINGr.sim\_tools module
-----------------------

.. automodule:: SINGr.sim_tools
   :members:
   :show-inheritance:
   :undoc-members:

SINGr.runner module
-------------------

.. automodule:: SINGr.runner
   :members:
   :show-inheritance:
   :undoc-members:


