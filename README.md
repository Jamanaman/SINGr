# SINGr: An ngSPICE SI Simulation and Analysis Tool for Automated Simulation and Optimisation Workflows

**S**ignal **I**ntegrity **ng**SPICE Analyser or SINGr (like singer) for short

This package is designed for the purpose of allowing one to specify arbitrary net topologies with modular structural components such as transmission line models, terminations, and behavioural models of components and then simulate them with a range of different workflows. 

## Features
Currently, only the base configuration structure is implemented, which uses a recursive tree structure with arbitrary node connections to allow for more complex structures. There are, however, two automated simulation and analysis workflows that have been implemented:

- **Waveform Analysis**
  - This assesses all valid transitions and logic states (currently limited to NRZ/PAM2 waveforms) and provides, *rise/fall time* (at 10% and 90%), *settling time* (within 10% margin of stable value), *slew rate*, *overshoot*, and *undershoot*. 
- **Eye Analysis**
  - This segments a time series of logic transitions into chunks of 3 and then overlays them to assess eye width, eye height, eye amplitude, and logic levels.  

For full API docs go here: https://singr.readthedocs.io/en/latest/index.html

## Installation
This package can be installed simply using pip install via:

``pip install SINGr``

Alternatively it can be built by cloning the repository either by using `uv build --wheel` and pip installed or one can use `uv pip install .`. `uv` is not essential but is especially useful for developers as that is what has been used to develop the package as a whole.

## Contribution
Developers can contribute to the tool by forking the repository and submitting pull requests.

## Issues and Feature Requests
* Please record any bugs, issues and feature requests here: https://github.com/Jamanaman/SINGr/issues
* Detailed information on how any issue can be reproduced should be provided including any IBIS files used and version number of the program. Screenshots would also help.

## References
This tool is built off of pyBIS2PICE (https://github.com/Jamanaman/pybis2spice) to translate IBIS Models that are used in SI simulations, ecdtools which allows one to parse and process ibis files, and InSpice as the interface into ngSPICE. 

Eye Diagram analysis was implemented using a PAM4 Eye-Diagram Analysis algorithm [1] using Least Mean of Squares mode estimation instead of shorth mode estimation [2].

[1] Jargon, J. and Cheron, J. (2021), A Robust Algorithm for PAM4 Eye-Diagram Analysis, Proceedings of the Asia Pacific Microwave Conference, Brisbane, AU, [online], https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=932331 (Accessed June 29, 2026) 

[2] Jargon, Jeffrey & Wang, Chih-Ming Jack & Hale, Paul. (2008). A Robust Algorithm for Eye-Diagram Analysis. Journal of Lightwave Technology. 26. 3592-3600. [online], https://ieeexplore.ieee.org/document/4758639 (Accessed June 29, 2026)

![uv](https://img.shields.io/badge/uv-%23DE5FE9.svg?style=for-the-badge&logo=uv&logoColor=white)
![Pydantic](https://img.shields.io/badge/pydantic-%23E92063.svg?style=for-the-badge&logo=pydantic&logoColor=)
![NumPy](https://img.shields.io/badge/NumPy-%23013243.svg?style=for-the-badge&logo=numpy&logoColor=yellow)
![Pandas](https://img.shields.io/badge/Pandas-%23150458.svg?style=for-the-badge&logo=pandas&logoColor=cyan)
![SciPy](https://img.shields.io/badge/SciPy-%230C55A5.svg?style=for-the-badge&logo=scipy&logoColor=%white)
![Python](https://img.shields.io/badge/python-%233670A0.svg?style=for-the-badge&logo=python&logoColor=ffdd54)