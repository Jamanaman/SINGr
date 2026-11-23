Signal Integrity Analysis Techniques
====================================
Waveform Triggering and Segmentation
------------------------------------
Triggering and segmentation is performed by the module to be able to isolate individual unit intervals. This is done currently with a 
known clock frequency and does not account for different types of clocking or implement any form of clock recovery. Triggering and 
segmentation are performed as follows:

1. A possible edge transition is detected based on a minimum slope and based on voltage thresholds from high to low or low to high.
2. From the trigger sample, walk forward a full clock period and assess if the transition is completed. If not search for next edge transition.
3. Once a valid transition period is detected, walk back to the last logic level as the assumed clock edge. 
4. Center the clock edge in the unit interval and segment the signal going forward periodically with the clock frequency. 

Event Classification
--------------------
After segmentation, each unit interval is classified. This is done based on mean slope of the signal and end voltage state as follows:

1. A threshold slope is calculated such that a full transition could have occurred during half of the clock period.
2. The mean slope of the signal is calculated by calculating the rolling mean derivative with a window size of 10 and then taking the mean of all of the rolling derivatives.
3. If the magnitude of the mean slope greater than the threshold slope, the end state voltage is taken to be the mean voltage after the magnitude of the rolling mean slope of the signal has decreased to less than the threshold slope. (Note 1)
4. The event is then classified as rising or falling based on the sign of the mean slope and the end state voltage if the mean slope is greater than the slope threshold or as high or low based on the median voltage if the mean slope is too low.
5. Finally, each event is classified as "good" or "bad" based on whether a transition was successfully completed or if the high or low levels were stable during the period.

Waveform Analysis
-----------------
Waveform analysis currently involves taking single unit intervals which are classified only as Rise, Fall, High and Low events. 
Rising and falling waveforms are then for the following features: 

* Rise/Fall Times: Time between 90%/10% of the specified voltage range
* Slew Rates: Linearised Slew of Rise and Fall time segments
* Overshoot: Mean amplitude across all captured transitions of overshoot above logic high level
* Undershoot: Mean amplitude across all captured transitions of overshoot below logic low level
* Settling Time: Mean across all captured transitions where voltage settles to within the specified logic level +/- threshold

Eye Analysis
------------
To this point Eye Diagram analysis in SINGr involves a procedure of chunking the available waveform data into pairs of unit intervals
which are offset by a half period such that 2 events can occur per chunk. This allows one to see all combinations of binary states
for 3 clock periods. The eye features are then measured across this 2 UI wide eye diagram using an algorithm which will be described later
in this section. This yields the mean levels for each logic state and the eye amplitude, height, and width. 

These are then displayed to the user when required in the form of an annotated eye diagram.

Eye Diagram Measurement Algorithm
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The Eye Diagram Measurement Algorithm is based on a combination of the methods layed out in [1] and the least mean of squares estimation method to 
find the logic levels detailed in [2]. The algorithm functions as follows:

* k-Means clustering is performed to find initial estimates for each logic level.
* The mode of each cluster is estimated using the least mean of squares method to improve the estimate of each logic level.
* The midpoints between each logic level are used as values to estimate crossing voltages.
* Voltages within 5% of the midpoints are clustered in time using k-Means clustering to find the inner edges of the eye at its widest point.
* Use inner eye edges to estimate the eye centre.
* Using k-Means clustering, isolate the voltages at each voltage level at the eye centre where they are most likely to be stable to improve logic level estimates.
* Take the minimum and maximum distances between these clusters to measure the eye height and amplitude respectively.
* Use improved voltage level estimates to find the crossing voltages again and redo clustering at the crossing voltage to measure the width of the eye.

References
----------

[1] Jargon, J. and Cheron, J. (2021), A Robust Algorithm for PAM4 Eye-Diagram Analysis, Proceedings of the Asia Pacific Microwave Conference, Brisbane, AU, [online], https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=932331 (Accessed June 29, 2026) 

[2] Jargon, Jeffrey & Wang, Chih-Ming Jack & Hale, Paul. (2008). A Robust Algorithm for Eye-Diagram Analysis. Journal of Lightwave Technology. 26. 3592-3600. [online], https://ieeexplore.ieee.org/document/4758639 (Accessed June 29, 2026)