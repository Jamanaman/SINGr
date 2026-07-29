'''
Module containing all analysis workflows implemented in SINGr.
Implemented analyses include:
- Eye Analysis (only RZ and NRZ signalling are supported)
'''

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from typing import List, Optional, Literal

from .signal_tools import capture_transitions, characterise_transitions
from .eye_tools import generate_eye_histogram

_ANALYSES = Literal['EYE', 'WAVEFORM']
sns.set_theme("paper", "whitegrid","tab20")

def perform_eye_analysis(
        df: pd.DataFrame, key:str, 
        clock_frequency:float, v_high:float, 
        v_low:float, threshold_pct:float, 
        statistical_jitter_s: float, datastream: Optional[List[int]]=None, 
        visualise:bool=True
        ):

    transitions_df = capture_transitions(df, key, clock_frequency, v_high, v_low, threshold_pct, datastream)

    chunk_df, hist_measurements = generate_eye_histogram(transitions_df, key, statistical_jitter_s)
    if visualise:
        threshold_dist = (v_high-v_low)*(1-threshold_pct)
        ax = sns.lineplot(chunk_df, x='chunk_time', y=key, units='sequence', estimator=None, alpha=0.2, label=None, color="tab:orange")
        ax.set_title(f'Eye Diagram {key.capitalize()}')
        ax.set_xlabel('Volts (V)')
        # TODO time prefix for key for easier legibility
        ax.set_ylabel('Time (s)')
        ax.hlines([v_low, v_high], xmin=0, xmax=chunk_df['chunk_time'].max(), linestyles='dashed', label='Expected Voltage Levels', colors='r')
        ax.fill_between([chunk_df['chunk_time'].min(), chunk_df['chunk_time'].max()], v_low+threshold_dist, v_low-threshold_dist, alpha=0.2, color='r')
        ax.fill_between([chunk_df['chunk_time'].min(), chunk_df['chunk_time'].max()], v_high+threshold_dist, v_high-threshold_dist, alpha=0.2, color='r')
        ax.legend()
        ax.set_xlim(chunk_df['chunk_time'].min(), chunk_df['chunk_time'].max())
        hist_measurements = {key: f'{val:.3E}' for key, val in hist_measurements.items()}
        plt.show()

def perform_waveform_analysis(
        df: pd.DataFrame, key:str,
        clock_frequency:float, v_high:float, 
        v_low:float, threshold_pct:float, 
        datastream: Optional[List[int]]=None, visualise:bool=True 
    ):
    
    transitions_df = capture_transitions(df, key, clock_frequency, v_high, v_low, threshold_pct, datastream)
    transition_features = characterise_transitions(transitions_df, key, v_high, v_low, threshold_pct)

    if visualise:
        
        grid = sns.relplot(
            transitions_df, y=key, x='period_time', col='event', 
            kind='line', estimator=None, units='period_index', 
            alpha=0.33, col_wrap=2, col_order=['rise', 'fall', 'high', 'low']
            )
        grid.figure.suptitle(f'Waveform Analysis {key.capitalize()}')
        transition_features = {key: f'{val:.3E}' for key, val in transition_features.items()}
        print(transition_features)
        plt.show()