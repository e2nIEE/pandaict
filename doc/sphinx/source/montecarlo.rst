.. 	@author: fnuetz	


Monte Carlo based reliability
=============================

Reliability analysis
--------------------

.. autofunction:: pandaict.reliability.reliability.estimate_mtbf_mttr_for_conn

.. autofunction:: pandaict.reliability.reliability.analyze_critical_components_for_conn

.. autofunction:: pandaict.reliability.reliability.empirical_reliability_function


.. _mc_kwargs:

Shared Keyword Arguments
------------------------

All three functions above accept the following optional keyword arguments:

.. list-table::
   :header-rows: 1
   :widths: auto

   * - Argument
     - Description
   * - **min_connected**
       *(int, default* ``-1`` *)*
     - Minimum number of source–target pairs that must be connected for the
       system to be considered *up*. ``-1`` requires all pairs.
   * - **N**
       *(int, default* ``100_000`` *)*
     - Number of Monte-Carlo sample paths.
   * - **depth**
       *(int, default* ``200`` *)*
     - Depth in which each Monte-Carlo sample path is traversed.
       Not available in :func:`empirical_reliability_function` (forced to ``1``).
   * - **max_time**
       *(float, default* ``numpy.inf`` *)*
     - Simulation horizon per sample path in hours. In
       :func:`empirical_reliability_function`, automatically set to ``T``
       when ``T`` is scalar.
   * - **max_events**
       *(int, default* ``-1`` *)*
     - Maximum number of system-level transitions to record per path.
       ``-1`` means unlimited.
   * - **laziness**
       *(float, default* ``0`` *)*
     - Uniformisation laziness parameter. ``0`` disables uniformisation.
   * - **use_numba**
       *(bool, default* ``True`` *)*
     - Use the Numba-JIT compiled simulation kernel.
   * - **parallel**
       *(bool, default* ``True`` *)*
     - Run Monte-Carlo batches in parallel. Requires Numba.

.. note::
   The following keywords are **forced internally** and cannot be overridden:

   - :func:`estimate_mtbf_mttr_for_conn` — ``analyze_crit = False``
   - :func:`analyze_critical_components_for_conn` — ``analyze_crit = True``, ``return_samples = False``
   - :func:`empirical_reliability_function` — ``return_samples = True``, ``analyze_crit = False``, ``depth = 1``