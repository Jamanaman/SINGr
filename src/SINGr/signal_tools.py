'''
General utility functions for processing time series signals.
'''

from numpy import isclose, floor, ceil, linspace
from typing import List, Optional, Dict
from scipy.interpolate import make_interp_spline, BSpline
import pandas as pd 

def walk_forward_to_logic_level(
        df:pd.DataFrame, t_transition_detected: float, 
        logic_level_v:float, v_tol: float
        ) -> float:
    '''
    Walks back from transition being detected to the previous logic level.
    '''

    df_walk = df.where(df['time']>t_transition_detected).dropna()
    for row in df_walk.itertuples():
        if isclose(row[1], logic_level_v, atol=v_tol):
            return row[2]
    else:
        raise Exception()
        
def classify_period(
        df:pd.DataFrame, key:str, 
        v_high_th:float, v_low_th:float, 
        min_transition_slope:float
        ) -> pd.DataFrame:
    '''
    Classifies time series in single clock period as one of 'high', 'low',
    'rise', 'fall' or None if no valid event can be classified due to the signal
    staying mostly in between the logic thresholds.
    '''

    median_diff_df = df.rolling(10).median().diff().median()
    dxdt = median_diff_df[key]/median_diff_df['time']
    if dxdt > min_transition_slope:
        df['event'] = 'rise'
        return df
    elif dxdt < -min_transition_slope:
        df['event'] = 'fall'
        return df
    else:
        if df[key].median()>v_high_th:
            df['event'] = 'high'
            return df
        elif df[key].median()<v_low_th:
            df['event'] = 'low'
            return df
        else:
            df['event'] = None
            return df

def capture_transitions(
        df: pd.DataFrame, key:str, 
        clock_frequency:float, v_high:float, 
        v_low:float, threshold_pct:float, 
        datastream:Optional[List] = None
        ) -> pd.DataFrame:
    '''
    Reads a datastream and triggers on valid logic transition, before classifying every
    clock period thereafter. Classifies into simple binary logic events of 'high', 'low',
    'rising', 'falling' or None if no valid event can be classified due to the signal
    staying mostly in between the logic thresholds. 

    Returns a resampled and fully classified time series dataframe with equidistant time
    samples at 5000 samples per period. 
    
    TODO: If a datastream is provided,
    the data will be classified by matching with the datastream. 

    TODO: Implement parallel option as this is completely parallelisable after triggering 
    has occurred. 
    '''

    v_low_th = v_low+(v_high-v_low)*threshold_pct
    v_high_th = v_high-(v_high-v_low)*threshold_pct
    clock_period = 1/clock_frequency
    min_transition_slope = (v_high-v_low)/clock_period/2
    resolving_sample_period = clock_period/5000
    min_edge_rate_v_per_sample = min_transition_slope*resolving_sample_period

    hold = False
    t_transition = 0
    triggered = False
    first_edge_rising = False
    # Use smoothed signal to find a transition 
    resample_time = linspace(0, df['time'].max(), num=int(ceil(df['time'].max()/resolving_sample_period)))
    interp_data: BSpline = make_interp_spline(y=df[key], x=df['time'])
    df_resampled = pd.DataFrame({key: interp_data(resample_time), 'time': resample_time})
    df_smoothed = df_resampled.rolling(window=10).median().dropna(ignore_index=True)
    for i in range(1, len(df_smoothed.index)):
        if triggered:
            break
        if not hold:
            # Check to see if signal deviates outside of logic level
            if df_smoothed[key][i] - df_smoothed[key][i-1] < -min_edge_rate_v_per_sample and df_smoothed[key][i] < v_high_th:
                hold = True
                t_transition = df['time'][i]
                first_edge_rising = False
            elif df_smoothed[key][i] - df_smoothed[key][i-1] > min_edge_rate_v_per_sample and df_smoothed[key][i] > v_low_th:
                hold = True
                t_transition = df_smoothed['time'][i]
                first_edge_rising = True
            else:
                continue
        else:
            # Check to see if signal has completed a transition from one level to the next
            is_high_to_low = first_edge_rising and df[key][i] < df[key][i-1] and df[key][i] < v_low_th
            is_low_to_high = not first_edge_rising and df[key][i] > df[key] [i-1] and df[key][i] > v_high_th
            if is_high_to_low or is_low_to_high:
                if t_transition + df['time'][i] >= clock_period:
                    triggered = True
                    t_transition = walk_forward_to_logic_level(
                        df, key, 
                        t_transition, 
                        v_low if is_high_to_low else v_high, 
                        v_high*0.01
                        )
                    break
                else:
                    hold = False
    if not triggered:
        raise Exception()

    # take signal from half a clock period before the transition
    df_trig = df_resampled.where(df_resampled['time']>=t_transition-clock_period).dropna(ignore_index=True)
    # rezero the time of the data signal from the triggered point
    df_trig['time'] = df_trig['time']-df_trig['time'][0]
    df_classified = pd.DataFrame()
    for _, data in df_trig.groupby(df_trig.index // 1000):
        period_df = classify_period(data, key, v_high_th, v_low_th, min_edge_rate_v_per_sample)
        period_df['period_index'] = floor(period_df['time'].min()/clock_period)
        period_df['period_time'] = period_df['time']-period_df['time'].min()
        df_classified = pd.concat(
            [
                df_classified,
                period_df
            ]
        )
    return df_classified

def characterise_transitions(
        transitions_df: pd.DataFrame, key:str, 
        v_high:float, v_low:float, 
        threshold_pct:float
        ) -> Dict:
    '''
    Takes all transitions and measures transition features including rise/fall time
    slew rates, settling time, overshoot and undershoot. Mean values across the whole
    dataset are given.

    TODO: Potentially add preshoot analysis and ringing analysis. 
    '''
    
    v_tol = (v_high-v_low)*threshold_pct
    v_low_th = v_low+v_tol
    v_high_th = v_high-v_tol
    measurements_dict = {}
    edge_v = v_high_th-v_low_th
    mid_v = edge_v/2+v_low_th
    edge_df = transitions_df.where((transitions_df['event'] == 'rise') or (transitions_df['event'] == 'fall'))
    for edge, data in edge_df.where(abs(edge_df[key]-mid_v)<=mid_v).groupby('event'):
        
        measurements_dict.update({f'{edge}_time': data.groupby('period_index').apply(lambda period: period['time'].max()-period['time'].min()).mean()})
        measurements_dict.update({f'slew_rate_{edge}': measurements_dict[f'{edge}_time']/edge_v})
    
    measurements_dict.update({
        'overshoot': edge_df[key].where(edge_df['event']=='rise').groupby('period_index').max().mean()-v_high,
        'undershoot': edge_df[key].where(edge_df['event']=='fall').groupby('period_index').min().mean()-v_low,
        'settling_time': edge_df.groupby('period_index').apply(lambda period: period['time'].where(abs(period[key]-mid_v)<=mid_v).max()).mean()
    })

    return measurements_dict