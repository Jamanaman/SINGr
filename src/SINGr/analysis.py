'''
Module containing all analysis workflows implemented in SINGr.
Implemented analyses include:
- Eye Analysis (only RZ and NRZ signalling are supported)
'''

import pandas as pd
import seaborn as sns
import tabulate as tab
import matplotlib.pyplot as plt
from typing import List, Optional, Literal

from .eye_tools import capture_transitions, generate_eye_histogram

_ANALYSES = Literal['EYE']

def perform_eye_analysis(
        df: pd.DataFrame, key:str, 
        clock_frequency:float, v_high:float, 
        v_low:float, threshold_pct:float, 
        statistical_jitter_s: float, data: Optional[List[int]]=None, 
        visualise:bool=True):

    v_high_th = v_low+(v_high-v_low)*threshold_pct
    v_low_th = v_high-(v_high-v_low)*threshold_pct
    transitions_df = capture_transitions(df, key, clock_frequency, v_high, v_low, v_high_th, v_low_th, data)

    hist, hist_measurements = generate_eye_histogram(transitions_df, key, statistical_jitter_s)

    if visualise:
        sns.heatmap(hist, robust=True)
        print(hist_measurements)
        plt.show()