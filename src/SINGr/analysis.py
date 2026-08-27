'''
Module containing all analysis workflows implemented in SINGr.
Implemented analyses include:
- Eye Analysis (only NRZ/PAM2 signalling are supported)
- Waveform Analysis
'''

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from typing import List, Optional, Literal

from .signal_tools import capture_transitions, characterise_transitions
from .eye_tools import generate_eye_histogram

_ANALYSES = Literal['EYE', 'WAVEFORM']
sns.set_theme("paper", "whitegrid","tab20")

def generate_report():
    '''
    [WIP] Target v0.0.2
    '''
    pass

def perform_eye_analysis(
        df: pd.DataFrame, key:str, 
        clock_frequency:float, v_high:float, 
        v_low:float, threshold_pct:float, 
        statistical_jitter_s: float=0, datastream: Optional[List[int]]=None, 
        visualise:bool=False, output_report:bool=True
        ):
    '''
    The eye analysis assesses groups all transitions into overlapping sets of 3
    and then overlays all groups to measure eye height, width, amplitude and logic levels.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing all InSPICE simulation data
    key : str
        column of df containing the data to analyse
    clock_frequency : float
        frequency in Hz at which the transitions are supposed to be occurring
    v_high : float
        logic HIGH voltage
    v_low : float
        logic LOW voltage
    threshold_pct : float
        threshold percent of high-low voltage range about each logic level at which point the logic level is reached
    statistical_jitter_s : float
        any statistical jitter to apply !! Experimental !!
    datastream : Optional[List[int]]
        a series of data values (currently only 0,1 supported) to check for a match
    visualise : bool, optional
        generate plots if true
    output_report : bool, optional
        generate html output report if true
    '''
    transitions_df = capture_transitions(df, key, clock_frequency, v_high, v_low, threshold_pct, datastream)

    chunk_df, hist_measurements = generate_eye_histogram(transitions_df, key, statistical_jitter_s)
    if visualise or output_report:
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
        if visualise:
            plt.show()
        print('\n'.join([f'|{key}: {val}|' for key, val in hist_measurements.items()]))

def perform_waveform_analysis(
        df: pd.DataFrame, key:str,
        clock_frequency:float, v_high:float, 
        v_low:float, threshold_pct:float, 
        datastream: Optional[List[int]]=None, visualise:bool=True,
        output_report:bool=True
    ):
    '''
    The waveform analysis categorises all clock periods into RISE, FALL, HIGH and LOW
    and uses these categories to assess rise/fall time (90%-10%), slew rate, settling time
    overshoot and undershoot.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing all InSPICE simulation data
    key : str
        column of df containing the data to analyse
    clock_frequency : float
        frequency in Hz at which the transitions are supposed to be occurring
    v_high : float
        logic HIGH voltage
    v_low : float
        logic LOW voltage
    threshold_pct : float
        threshold percent of high-low voltage range about each logic level at which point the logic level is reached
    statistical_jitter_s : float
        any statistical jitter to apply !! Experimental !!
    datastream : Optional[List[int]]
        a series of data values (currently only 0,1 supported) to check for a match
    visualise : bool, optional
        generate plots if true
    output_report : bool, optional
        generate html output report if true
    '''
    transitions_df = capture_transitions(df, key, clock_frequency, v_high, v_low, threshold_pct, datastream)
    transition_features = characterise_transitions(transitions_df, key, v_high, v_low, threshold_pct)

    if visualise or output_report:
        
        grid = sns.relplot(
            transitions_df, y=key, x='period_time', col='event', 
            kind='line', estimator=None, units='period_index', 
            alpha=0.33, col_wrap=2, col_order=['rise', 'fall', 'high', 'low']
            )
        grid.figure.suptitle(f'Waveform Analysis {key.capitalize()}')
        grid.set_axis_labels('Time (s)', 'Voltage (V)')
        transition_features = {key: f'{val:.3E}' for key, val in transition_features.items()}
        if visualise:
            plt.show()
        print('\n'.join([f'|{key}: {val}|' for key, val in transition_features.items()]))