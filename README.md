# SINGr: An ngSPICE SI Simulation and Analysis Tool for Agentic and Optimisation Workflows

## Contribution
Developers can contribute to the tool by forking the repository and submitting pull requests.

## Issues and Feature Requests
* Please record any bugs, issues and feature requests here: https://github.com/Jamanaman/SINGr/issues
* Detailed information on how any issue can be reproduced should be provided including any IBIS files used and version number of the program. Screenshots would also help.

## References
This tool is built off of pyBIS2PICE (https://github.com/Jamanaman/pybis2spice) to translate IBIS Models that are used in SI simulations, ecdtools which allows one to parse and process ibis files, and InSpice as the interface into ngSPICE. 

Eye Diagram analysis was implemented using algorithm detailed in this paper,
Jargon, J. and Cheron, J. (2021), A Robust Algorithm for PAM4 Eye-Diagram Analysis, Proceedings of the Asia Pacific Microwave Conference, Brisbane, AU, [online], https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=932331 (Accessed June 29, 2026) 

, as well as the LMS mode estimation from this paper,

J. A. Jargon, C. M. J. Wang and P. D. Hale, "A Robust Algorithm for Eye-Diagram Analysis," in Journal of Lightwave Technology, vol. 26, no. 21, pp. 3592-3600, Nov.1, 2008, doi: 10.1109/JLT.2008.917313. keywords: {Robustness;Algorithm design and analysis;Least squares approximation;Histograms;Uncertainty;Signal analysis;Measurement;Extinction ratio;Jitter;Oscilloscopes;Extinction ratio;eye diagram;least-median-of-squares (LMS) location estimator;robust statistics}