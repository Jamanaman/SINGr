
from numpy import histogram2d, zeros, floor, ceil, linspace
from scipy.signal import fftconvolve
from scipy.stats import norm
import pandas as pd 
from .signal_tools import walk_back_to_logic_level, classify_period
from .hist_tools import count_contiguous_cells
from typing import List, Optional


def capture_transitions(
        df: pd.DataFrame, key:str, 
        clock_frequency:float, v_high_th:float, 
        v_low_th:float, v_high:float,
        v_low: float, data:Optional[List] = None
        ) -> pd.DataFrame:
    '''
    Reads a datastream and triggers on valid logic transition, before classifying every
    clock period thereafter. Classifies into simple binary logic events of 'high', 'low',
    'rising', 'falling' or None if no valid event can be classified due to the signal
    staying mostly in between the logic thresholds. 
    
    ## TODO If a datastream is provided,
    the data will be classified by matching with the datastream. 

    ## TODO: Implement parallel option as this is completely parallelisable after triggering 
    has occurred. 
    '''
    clock_period = 1/clock_frequency
    min_transition_slope = (v_high-v_low)/clock_period
    resolving_sample_period = clock_period/10

    hold = False
    t_transition = 0
    triggered = False
    first_edge_rising = False
    # Use smoothed signal to find a transition 
    df_smoothed = df.rolling(window=f'{resolving_sample_period}s').median()
    for i in range(1, len(df_smoothed.index)):
        if triggered:
            break
        if not hold:
            # Check to see if signal deviates outside of logic level
            if df_smoothed[key][i] - df_smoothed[key] [i-1] < -min_transition_slope and df_smoothed[key][i] < v_high_th:
                hold = True
                t_transition = df['time'][i]
                first_edge_rising = False
            elif df_smoothed[key][i] - df_smoothed[key] [i-1] > min_transition_slope and df_smoothed[key][i] > v_low_th:
                hold = True
                t_transition = df_smoothed['time'][i]
                first_edge_rising = True
            else:
                continue
        else:
            # Check to see if signal has completed a transition from one level to the next
            is_high_to_low = first_edge_rising and df[key][i] < df[key] [i-1] and df[key][i] < v_low_th
            is_low_to_high = not first_edge_rising and df[key][i] > df[key] [i-1] and df[key][i] > v_high_th
            if is_high_to_low or is_low_to_high:
                if t_transition + df['time'][i] >= clock_period:
                    triggered = True
                    if is_high_to_low:
                        t_transition = walk_back_to_logic_level(df, key, t_transition, v_high, v_high*0.01)
                    else:
                        t_transition = walk_back_to_logic_level(df, key, t_transition, v_low, v_high*0.01)
                    break
                else:
                    hold = False
    if not triggered:
        raise Exception()

    # take signal from half a clock period before the transition
    df_trig = df.where(df['time']>=t_transition-clock_period/2)
    # rezero the time of the data signal from the triggered point
    df_trig['time'] = df_trig['time']-df_trig['time'][0]
    df_classified = pd.DataFrame()
    min_transition_slope = (v_high-v_low)/clock_period
    for _, data in df_trig.groupby(pd.Grouper(key='time', freq=f'{clock_period}s', label='left')):        
        period_df = classify_period(data, key, v_high_th, v_low_th, min_transition_slope)
        period_df['period_index'] = floor(period_df['time'].min()/clock_period)
        period_df['period_time'] = period_df['time']-period_df['time'].min()
        df_classified = pd.concat(
            [
                df_classified, 
                period_df
            ]
        )
    return df_classified

def chunk_data_for_eye(transitions_df: pd.DataFrame, chunk_periods:int=3):
    '''
    This feature chunks the available data into consecutive sequences which can be identified as valid events.
    '''
    transitions_df['sequence'] = transitions_df.rolling(window=chunk_periods, on='period_index').apply(lambda chunk: chunk['period_index'].min() if not None in chunk['event'].unique() else None)
    return transitions_df.dropna()

def generate_eye_histogram(transitions_df: pd.DataFrame, key:str, statistical_jitter_s:float):
    '''
    Generate 2d histogram to be visualised as the eye diagram and apply any statistical jitter to it.
    Eye features will also be measured.

    Note: Statistical Jitter must be given in terms of the standard deviation of jitter to be applied
    to the distribution. If a maximum jitter is known, treat it as a 3 sigma value and divide it by
    3 to use as the `statistical_jitter_s` argument.
    '''
    
    chunk_df = chunk_data_for_eye(transitions_df)

    hist, x_edges, y_edges = histogram2d(
        chunk_df['period_time'], 
        chunk_df[key], 
        bins=[1500, 500],
        density=True
        )
    
    if statistical_jitter_s > 0:
        # create filter kernel 6 sigma wide in each direction 
        # the number of samples per standard deviation is the period divided by the statistical jitter 
        six_sig = linspace(-6, 6, ceil(chunk_df['period_time'].max()/statistical_jitter_s)*6*2)
        kernel = norm.pdf(six_sig)
        # apply the kernel as a time spread by convolving the pdf (total sum of 1 to conserve total power)
        # with the histogram (overlay of all signal periods)
        for row_idx in range(500):
            hist[row_idx,:] = fftconvolve(hist[row_idx,:], kernel, 'same')

    bw_hist = hist > 0
    hist_counted = zeros(bw_hist.shape, int)
    opening_idx = 1
    idx_hist = zeros(bw_hist.shape, int)

    # scan histogram and count contiguous cells 
    for i, row in enumerate(bw_hist):
        for j, cell in enumerate(row):
            if cell and not hist_counted[i, j]:
                group_coords = [(i, j)]
                group_count = count_contiguous_cells(i, j, bw_hist, hist_counted, group_coords=group_coords)
                hist_counted[group_coords[:, 0], group_coords[:, 1]] = group_count
                idx_hist[group_coords[:, 0], group_coords[:, 1]] = opening_idx
                opening_idx += 1
            
def apply_mask(mask, eye):
    pass