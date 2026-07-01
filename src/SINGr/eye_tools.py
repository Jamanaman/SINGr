'''
Module containing all functions which enable one to build, visualise and characterise 
signal eye diagrams.
'''

from numpy import histogram2d, floor, ceil, linspace, mean, diff, argmin
from scipy.signal import fftconvolve
from scipy.interpolate import make_interp_spline, BSpline
from scipy.stats import norm
import kmeans1d
import pandas as pd 
from typing import List, Optional

from .signal_tools import walk_forward_to_logic_level, classify_period

def capture_transitions(
        df: pd.DataFrame, key:str, 
        clock_frequency:float, v_high:float, 
        v_low:float, v_high_th:float,
        v_low_th: float, datastream:Optional[List] = None
        ) -> pd.DataFrame:
    '''
    Reads a datastream and triggers on valid logic transition, before classifying every
    clock period thereafter. Classifies into simple binary logic events of 'high', 'low',
    'rising', 'falling' or None if no valid event can be classified due to the signal
    staying mostly in between the logic thresholds. 
    
    TODO: If a datastream is provided,
    the data will be classified by matching with the datastream. 

    TODO: Implement parallel option as this is completely parallelisable after triggering 
    has occurred. 
    '''
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
    data: BSpline = make_interp_spline(y=df[key], x=df['time'])
    df_resampled = pd.DataFrame({key: data(resample_time), 'time': resample_time})
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

def chunk_data_for_eye(transitions_df: pd.DataFrame, chunk_periods:int=3):
    '''
    Chunk the available data into consecutive sequences which can be identified as valid events.
    '''
    chunk_df = pd.DataFrame()
    for chunk, data in transitions_df.groupby(transitions_df['period_index'] // chunk_periods):
        data['sequence'] = chunk if not None in data['event'].unique() else None
        data['chunk_time'] = data['time']-data['time'].min()
        chunk_df = pd.concat([chunk_df, data], ignore_index=True)
    chunk_df=chunk_df.dropna(ignore_index=True)
    return chunk_df

def generate_eye_histogram(
        transitions_df: pd.DataFrame, key:str, 
        statistical_jitter_s:float, signaling:str = 'NRZ'
        ):
    '''
    Generate 2d histogram to be visualised as the eye diagram and apply any statistical jitter to it.
    Eye features will also be measured.

    Usage Note: Statistical Jitter must be given in terms of the standard deviation of jitter to be 
    applied to the distribution. If a maximum jitter is known, treat it as a 3 sigma value and divide 
    it by 3 to use as the `statistical_jitter_s` argument.

    TODO: Add chunking settings for eyes that have more clock periods such as where distortions are 
    caused by lower frequency signals coupling into the data line.
    '''
    
    chunk_df = chunk_data_for_eye(transitions_df)
    num_bins_v = 300
    num_bins_per_period = 300
    hist, x_edges, y_edges = histogram2d( 
        chunk_df[key],
        chunk_df['chunk_time'], 
        bins=[num_bins_v, num_bins_per_period*3],
        density=True
        )

    if statistical_jitter_s > 0:
        # create filter kernel 6 sigma wide in each direction 
        # the number of samples per standard deviation is the period divided by the statistical jitter 
        six_sig = linspace(-6, 6, ceil(chunk_df['chunk_time'].max()/statistical_jitter_s)*6*2)
        kernel = norm.pdf(six_sig)
        # apply the kernel as a time spread by convolving the pdf (total sum of 1 to conserve total power)
        # with the histogram (overlay of all signal periods)
        for row_idx in range(500):
            hist[row_idx,:] = fftconvolve(hist[row_idx,:], kernel, 'same')

    # identify logic levels 
    if signaling == 'NRZ' or signaling == 'RZ':
        logic_levels = 2
    elif signaling == 'PAM4':
        logic_levels = 4
    elif signaling == 'PAM6':
        logic_levels = 6
    else:
        raise NotImplementedError(f'Signaling method {signaling} not supported')
    
    hist_measurements = {}
    # Perform K-Means clustering based on the expected number of voltage levels
    clusters, centers = kmeans1d.cluster(chunk_df[key], logic_levels)
    chunk_df['cluster'] = clusters

    # estimate voltage levels by making shorth estimates of the mean from the clustered observations
    lms_estimates = []
    for grp, data in chunk_df.groupby('cluster'):
        observations = data[key].sort_values(ignore_index=True)
        h = int(floor(len(observations)/2) + 1) 
        top_obs = list(observations[h:-1])
        bottom_obs = list(observations[0:h-1])
        intervals = [a-b for a, b in zip(top_obs, bottom_obs)]
        min_interval = argmin(intervals)
        lms_estimates.append(mean([top_obs[min_interval], bottom_obs[min_interval]]))

    # estimate the eye center time by finding the clustered crossing voltage at the halfway points
    # between each pair of estimated voltage levels 
    t_left = []
    t_right = []
    for i in range(1, logic_levels):
        midpoint_v = (lms_estimates[i-1]+lms_estimates[i])/2
        tol_v = (lms_estimates[i]-lms_estimates[i-1])*0.01
        cluster_df = chunk_df.where(abs(chunk_df[key]-midpoint_v) < tol_v).dropna()
        clusters, centers = kmeans1d.cluster(cluster_df['chunk_time'], 2)
        cluster_df['cluster'] = clusters
        t_left.append(
                cluster_df['chunk_time'].where(
                cluster_df['cluster'] == 0
                ).max()
            )
        t_right.append(
                cluster_df['chunk_time'].where(
                cluster_df['cluster'] == 1
                ).min()
            )
    t_mid = (max(t_left)+min(t_right))/2
    hist_measurements.update({'t_mid': t_mid})

    # using the time +/-2.5% about the centre of the central eye estimate voltage levels
    dividers = [chunk_df[key].min()]
    for space in diff(lms_estimates)/2:
        dividers.append(space)
    dividers.append(chunk_df[key].max())
    t_tol = abs(0.025*(max(t_left)-min(t_right)))
    mins = []
    maxes = []
    means = []
    for i in range(logic_levels):
        
        division_df = chunk_df.where(
            dividers[i] <= chunk_df[key] 
            ).where(
                chunk_df[key] <= dividers[i+1]
            ).where(
                abs(chunk_df['chunk_time']-t_mid) < t_tol
            ).dropna()
        
        hist_measurements.update({f'logic_{i}':division_df[key].mean()})
        mins.append(division_df[key].min())
        maxes.append(division_df[key].max())
        means.append(division_df[key].mean())
        if i > 0:
            hist_measurements.update({f'eye_height_{i-1}': mins[i]-maxes[i-1]})
            hist_measurements.update({f'eye_amplitude_{i-1}': means[i]-means[i-1]})

    for i in range(1, logic_levels):
        midpoint_v = (means[i-1]+means[i])/2
        tol_v = (means[i]-means[i-1])*0.01
        cluster_df = chunk_df.where(abs(chunk_df[key]-midpoint_v) < tol_v).dropna()
        clusters, centers = kmeans1d.cluster(cluster_df[key], 2)
        cluster_df['cluster'] = clusters
        t_left = cluster_df[key].where(
                cluster_df['cluster'] == 0
                ).max()
        t_right = cluster_df[key].where(
                cluster_df['cluster'] == 1
                ).min()
        hist_measurements.update({f'eye_width_{i-1}':t_right-t_left})

    return hist, hist_measurements

def apply_mask(mask, eye):
    pass