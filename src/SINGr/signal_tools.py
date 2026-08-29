'''
General utility functions for processing time series signals.
'''

from numpy import isclose, floor, ceil, linspace
from typing import List, Optional, Dict
from scipy.interpolate import make_interp_spline, BSpline
import pandas as pd 

def walk_forward_to_logic_level(
        df:pd.DataFrame, t_transition_detected: float, 
        logic_level_v:float, v_tol: float, key: str
        ) -> float:
    '''
    Walks from transition being detected to the next logic level.
    '''

    df_walk = df.where(df['time']>=t_transition_detected).dropna()
    for row, data in df_walk.iterrows():
        if isclose(data[key], logic_level_v, atol=v_tol):
            return data['time']
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

    Distinguishes between rise/fall and high/low based on if the mean slope is sufficient to 
    have achieved a full transition within the period and where the end voltage sits for the period. 

    '''

    window_length = 10
    derivative_threshold = min_transition_slope*window_length
    mean_diff_df = df.diff(window_length).mean()
    dxdt = mean_diff_df[key]
    end_state_voltage = df.iloc[-1-window_length:-1][key].mean()
    if dxdt > derivative_threshold and end_state_voltage >= v_high_th:
        df['event'] = 'rise'
        return df
    elif dxdt < -derivative_threshold and end_state_voltage <= v_low_th:
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
    samples at 1000 samples per period. 

    Triggering is done as follows:
        - by detecting a logic transition with a sufficient slope to suggest that it is not simply common mode drift
        - once a transition is detected, it is observed if a valid logic level is maintained for at least a full clock period
        - the first detected transition is then excluded from the first captured period and all subsequent periods are classified
    
    TODO: If a datastream is provided,
    the data will be classified by matching with the datastream. 

    TODO: Implement parallel option as this is completely parallelisable after triggering 
    has occurred. 

    TODO: Implement fallback triggering if no triggering is achieved.
    '''

    v_high_th = v_low+(v_high-v_low)*threshold_pct
    v_low_th = v_high-(v_high-v_low)*threshold_pct
    clock_period = 1/clock_frequency
    min_transition_slope = (v_high_th-v_low_th)/1000/2
    resolving_sample_period = clock_period/1000
    min_delay = clock_period
    hold = False
    t_transition = 0
    triggered = False
    first_edge_rising = False
    # Use smoothed signal to find a transition 
    resample_time = linspace(min_delay, df['time'].max(), num=int(ceil((df['time'].max()-min_delay)/resolving_sample_period)))
    df_trim = df.where(df['time']>=min_delay).dropna()
    interp_data: BSpline = make_interp_spline(y=df_trim[key], x=df_trim['time'])
    df_resampled = pd.DataFrame({key: interp_data(resample_time), 'time': resample_time})
    df_smoothed = df_resampled.rolling(window=10).median().dropna(ignore_index=True)
    for i in range(1, len(df_smoothed.index)):
        if triggered:
            break
        elif not hold:
            # Check to see if signal deviates outside of logic level
            if df_smoothed[key][i] - df_smoothed[key][i-1] < -min_transition_slope and df_smoothed[key][i] < v_high_th:
                hold = True
                t_transition = df['time'][i]
                first_edge_rising = False
            elif df_smoothed[key][i] - df_smoothed[key][i-1] > min_transition_slope and df_smoothed[key][i] > v_low_th:
                hold = True
                t_transition = df_smoothed['time'][i]
                first_edge_rising = True
            else:
                continue
        else:
            # Check to see if signal has completed a transition from one level to the next
            is_high_to_low = first_edge_rising and df_resampled[key][i] < df_resampled[key][i-1] and df_resampled[key][i] < v_low_th
            is_low_to_high = not first_edge_rising and df_resampled[key][i] > df_resampled[key][i-1] and df_resampled[key][i] > v_high_th
            if is_high_to_low or is_low_to_high:
                if t_transition + df_resampled['time'][i] >= clock_period:
                    triggered = True
                    try:
                        t_transition = walk_forward_to_logic_level(
                            df_resampled, t_transition, 
                            v_low if is_high_to_low else v_high, 
                            v_high*0.01, key
                            )
                        break
                    except:
                        triggered = False
                        continue
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

def characterise_transitions(
        transitions_df: pd.DataFrame, key:str, 
        v_high:float, v_low:float, 
        threshold_pct:float
        ) -> Dict:
    '''
    Takes all transitions and measures transition features including rise/fall time
    slew rates, settling time, overshoot and undershoot. Mean values across the whole
    dataset are given.

    Measurement Definitions:

        - Rise/Fall Times: Time between 90%/10% of the specified voltage range
        - Slew Rates: Linearised Slew of Rise and Fall time segments
        - Overshoot: Mean amplitude across all captured transitions of overshoot above logic high level
        - Undershoot: Mean amplitude across all captured transitions of overshoot below logic low level
        - Settling Time: Mean across all captured transitions where voltage settles to within the specified logic level +/- threshold

    TODO: Potentially add preshoot analysis and ringing analysis. 
    '''
    
    v_tol = (v_high-v_low)*(1-threshold_pct)
    v_low_th = v_low+v_tol
    v_high_th = v_high-v_tol
    measurements_dict = {}
    edge_v = v_high_th-v_low_th
    mid_v = edge_v/2+v_low_th
    edge_df = transitions_df.where((transitions_df['event'] == 'rise')|(transitions_df['event'] == 'fall')).dropna()
    for edge, data in edge_df.where(abs(edge_df[key]-mid_v)<=mid_v).dropna().groupby('event'):
        edge_sign = 1 if edge=='rise' else -1
        measurements_dict.update({f'{edge.capitalize()} Time': data.groupby('period_index').apply(lambda period: period['time'].max()-period['time'].min()).mean()})
        measurements_dict.update({f'Slew Rate {edge.capitalize()}': edge_v/measurements_dict[f'{edge.capitalize()} Time']*edge_sign})
    
    measurements_dict.update({
        'Overshoot': edge_df.where(edge_df['event']=='rise').dropna().groupby('period_index').max(numeric_only=True).mean()[key]-v_high,
        'Undershoot': edge_df.where(edge_df['event']=='fall').dropna().groupby('period_index').min(numeric_only=True).mean()[key]-v_low,
        'Settling Time': edge_df.groupby('period_index').apply(lambda period: period['period_time'].where(abs(period[key]-mid_v)<=mid_v).max()).mean()
    })

    return measurements_dict