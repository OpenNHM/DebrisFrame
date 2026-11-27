c1TIF: Thickness integrated flow module
=======================================

:py:mod:`c1TIF` is a module for debris flow computations using thickness integration.
c1TIF executes  `AvaFrame::com1DFA <https://docs.avaframe.org/en/latest/moduleCom1DFA.html>`_ with
overwriting various parameters and adding debris-flow related features.
Calculations are based on the thickness integrated governing equations and
solved numerically using the smoothed particle hydrodynamics (sph) method. Please note
the use of *thickness averaged/integrated* instead of *depth averaged/integrated* for clarity and consistency.

Thickness integrated flow simulations can be performed for different release scenarios, with or without
entrainment and/or resistance areas, and is controlled via a configuration file.
The configuration can be modified in order to change any of the default settings and also allows
to perform simulations for varying parameters all at once.

.. Note::
   We provide the documentation of the most important debris flow related features here,
   for the entire documentation we refer to the
   `AvaFrame documentation <https://docs.avaframe.org/en/latest/moduleCom1DFA.html>`_.


.. Note::
   The configuration parameters are still under development.

Theory
--------
The theory and numerics of the thickness integrated flow model can be found in the
`AvaFrame documentation: com1DFA Theory <https://docs.avaframe.org/en/latest/theoryCom1DFA.html>`_.

Input
---------

The data required to execute the module are described in
:doc:`workflowC1TIF`.
Regarding the release- and entrainment thickness settings we refer to the
`respective AvaFrame section <https://docs.avaframe.org/en/latest/moduleCom1DFA.html#release-entrainment-thickness-settings>`_.
Note that option 3 (thickness set via time dependent release file) is the default setting in c1TIF.
This option is used for hydrographs as input.


Friction parameters
^^^^^^^^^^^^^^^^^^^
The available friction models are described
`here <https://docs.avaframe.org/en/latest/theoryCom1DFA.html#friction-model>`_.


Erosion, Deposition, adaptive topography
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
When `entrainment <https://docs.avaframe.org/en/latest/theoryCom1DFA.html#entrainment>`_,
`detrainment <https://docs.avaframe.org/en/latest/theoryCom1DFA.html#detrainment>`_
or stopping (flow velocity is zero) occurs and the respective flags ``adaptSfcEntrainment``,
``adaptSfcDetrainment`` and ``adaptSfcStopped`` are switched on, the surface is adapted accordingly
(see the `AvaFrame adaptive topography documentation <https://docs.avaframe.org/en/latest/theoryCom1DFA.html#adaptive-surface>`_).
Additionally, the deposition can be erodible if ``entrainableDeposition`` is switched on.

Output
---------

The description of the default and optional results are in the
`AvaFrame documentation <https://docs.avaframe.org/en/latest/moduleCom1DFA.html#output>`_.

To run
--------

For the complete execution sequence see :doc:`workflowC1TIF`.
See also :doc:`scriptBasedUsage` and :doc:`qgisUsage`.
