'''
Module containing all analysis workflows implemented in SINGr.
Implemented analyses include:
- Eye Analysis (only NRZ/PAM2 signalling are supported)
- Waveform Analysis
'''

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
from typing import List, Optional, Literal

from .signal_tools import capture_transitions, characterise_transitions
from .eye_tools import generate_eye_histogram

_ANALYSES = Literal['EYE', 'WAVEFORM']
sns.set_theme("paper", "whitegrid","tab20")
_SI_MAG_PREFIXES = {
    0: '', 3: 'k', 6: 'M',
    9: 'G', 12: 'T', -3: 'm', 
    -6: '\u00B5', -9: 'n', -12: 'p',
    -15: 'f'
    }

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
        # find distance from logic level to threshold value
        threshold_dist = (v_high-v_low)*(1-threshold_pct)
        
        # Find logical SI unit prefix for timescale and scale appropriately 
        tspan = chunk_df.chunk_time.max()-chunk_df.chunk_time.min()
        tspan_mag = int(f'{tspan:.0E}'.split('E')[1])
        prefix = _SI_MAG_PREFIXES[tspan_mag]
        chunk_df['chunk_time_scaled'] = chunk_df['chunk_time']/10**tspan_mag

        # plot results
        ax = sns.lineplot(chunk_df, x='chunk_time_scaled', y=key, units='sequence', estimator=None, alpha=0.2, label=None, color="tab:orange")
        ax.set_title(f'Eye Diagram {key.capitalize()}')
        ax.set_ylabel('Volts (V)')
        ax.set_xlabel(f'Time ({prefix}s)')
        ax.hlines([v_low, v_high], xmin=0, xmax=chunk_df['chunk_time_scaled'].max(), linestyles='dashed', label='Expected Voltage Levels', colors='r')
        ax.fill_between([chunk_df['chunk_time_scaled'].min(), chunk_df['chunk_time_scaled'].max()], v_low+threshold_dist, v_low-threshold_dist, alpha=0.2, color='r')
        ax.fill_between([chunk_df['chunk_time_scaled'].min(), chunk_df['chunk_time_scaled'].max()], v_high+threshold_dist, v_high-threshold_dist, alpha=0.2, color='r')
        ax.set_xlim(chunk_df['chunk_time_scaled'].min(), chunk_df['chunk_time_scaled'].max())

        # annotate plot with measurements TODO
        for key, value in hist_measurements.items():
            if 'Level' in key:
                lab = f'{key}: {value:.3f} V'
                ax.axhline(y=value, label=lab, color='b')
            elif 'Height' in key:
                lab = f'{key}: {value:.3f} V'
                eye_idx = key.split(' ')[-1]
                x = hist_measurements['Time Eye Center']/10**tspan_mag
                ax.add_patch(FancyArrowPatch(
                    posA=(x, hist_measurements[f'Eye Bottom {eye_idx}']), 
                    posB=(x, hist_measurements[f'Eye Top {eye_idx}']), 
                    shrinkA=0, shrinkB=0, arrowstyle='|-|',
                    alpha=0.75, ls='--', label=lab,
                    color='seagreen', lw=2, mutation_scale=3
                    ))
            elif 'Width' in key:
                lab = f'{key}: {value/10**tspan_mag:.3f} {prefix}s'
                eye_idx = key.split(' ')[-1]
                left = hist_measurements[f'Eye Left {eye_idx}']/10**tspan_mag
                right = hist_measurements[f'Eye Right {eye_idx}']/10**tspan_mag
                bottom = hist_measurements[f'Eye Bottom {eye_idx}']
                top = hist_measurements[f'Eye Top {eye_idx}']
                mid = bottom + (top-bottom)/2
                ax.add_patch(FancyArrowPatch(
                    posA=(left, mid), posB=(right, mid), 
                    shrinkA=0, shrinkB=0, arrowstyle='|-|', 
                    alpha=0.75, ls='--', label=lab,
                    color='seagreen', lw=2, mutation_scale=3
                    ))
        ax.legend()
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

        # Find logical SI unit prefix for timescale and scale appropriately 
        tspan = transitions_df['period_time'].max()-transitions_df['period_time'].min()
        tspan_mag = int(f'{tspan:.0E}'.split('E')[1])
        prefix = _SI_MAG_PREFIXES[tspan_mag]
        transitions_df['period_time_scaled'] = transitions_df['period_time']/10**tspan_mag
        
        grid = sns.relplot(
            transitions_df, y=key, x='period_time_scaled', col='event', 
            kind='line', estimator=None, units='period_index', 
            alpha=0.33, col_wrap=2, col_order=['rise', 'fall', 'high', 'low']
            )
        grid.figure.suptitle(f'Waveform Analysis {key.capitalize()}')
        grid.set_axis_labels(f'Time ({prefix}s)', 'Voltage (V)')
        transition_features = {key: f'{val:.3E}' for key, val in transition_features.items()}
        # TODO annotate with transition features
        if visualise:
            plt.show()
        print('\n'.join([f'|{key}: {val}|' for key, val in transition_features.items()]))