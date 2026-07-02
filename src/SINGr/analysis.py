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

from .signal_tools import capture_transitions, characterise_transitions
from .eye_tools import generate_eye_histogram

_ANALYSES = Literal['EYE', 'WAVEFORM']

def perform_eye_analysis(
        df: pd.DataFrame, key:str, 
        clock_frequency:float, v_high:float, 
        v_low:float, threshold_pct:float, 
        statistical_jitter_s: float, datastream: Optional[List[int]]=None, 
        visualise:bool=True
        ):

    transitions_df = capture_transitions(df, key, clock_frequency, v_high, v_low, threshold_pct, datastream)

    hist, hist_measurements = generate_eye_histogram(transitions_df, key, statistical_jitter_s)

    if visualise:
        sns.heatmap(hist, robust=True)
        print(hist_measurements)
        plt.show()

def perform_waveform_analysis(
        df: pd.DataFrame, key:str,
        clock_frequency:float, v_high:float, 
        v_low:float, threshold_pct:float, 
        datastream: Optional[List[int]]=None, visualise:bool=True 
    ):
    
    transitions_df = capture_transitions(df, key, clock_frequency, v_high, v_low, threshold_pct, datastream)
    transition_features = characterise_transitions(df, key, v_high, v_low, threshold_pct)
    