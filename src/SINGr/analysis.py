
from numpy import histogram2d, zeros, floor, ceil, linspace, mean, diff, isclose
from scipy.signal import fftconvolve
from scipy.stats import norm
from sklearn.cluster import KMeans
import pandas as pd 
from .signal_tools import walk_forward_to_logic_level, classify_period
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
    df_trig = df.where(df['time']>=t_transition-clock_period)
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
    Chunk the available data into consecutive sequences which can be identified as valid events.
    '''
    transitions_df['sequence'] = transitions_df.rolling(
            window=chunk_periods, on='period_index'
        ).apply(
            lambda chunk: chunk['period_index'].min() if not None in chunk['event'].unique() else None
        )
    transitions_df.dropna()
    transitions_df['chunk_time'] = transitions_df.groupby('sequence').apply(lambda chunk: chunk['time']-chunk['time'].min())
    return transitions_df

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

    ## TODO: Add chunking settings for eyes that have more clock periods such as where distortions are 
    caused by lower frequency signals coupling into the data line.
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

    # identify logic levels 
    if signaling == 'NRZ':
        logic_levels = 2
    elif signaling == 'PAM4':
        logic_levels = 4
    elif signaling == 'PAM6':
        logic_levels = 6
    else:
        raise NotImplementedError(f'Signaling method {signaling} not supported')
    
    hist_measurements = {}
    # Perform K-Means clustering based on the expected number of voltage levels
    v_range = transitions_df[key].max()-transitions_df[key].min()
    initial_estimates = [transitions_df[key].min()+v_range/(logic_levels-1)*i for i in range(logic_levels)]
    kmeans_levels = KMeans(n_clusters=logic_levels, init=initial_estimates).fit(transitions_df[key])
    transitions_df['cluster'] = kmeans_levels.predict(transitions_df[key])

    # estimate voltage levels by making shorth estimates of the mean from the clustered observations
    shorth_estimates = []
    for grp, data in transitions_df.groupby('cluster'):
        observations = data[key].sort_values()
        h = floor(len(observations)/2) + 1 
        intervals = observations[h:-1]-observations[0:h-1]
        shorth_estimates.append(mean(intervals))

    # estimate the eye center time by finding the clustered crossing voltage at the halfway points
    # between each pair of estimated voltage levels 
    t_range = transitions_df['chunk_time'].max()
    initial_estimates = [t_range/4, 3*t_range/4]
    kmeans_time = KMeans(n_clusters=2, init=initial_estimates)
    t_left = []
    t_right = []
    for i in range(1, logic_levels):
        midpoint_v = (shorth_estimates[i-1]+shorth_estimates[i])/2
        tol_v = (shorth_estimates[i]-shorth_estimates[i-1])*0.01
        cluster_df = transitions_df.where(isclose(transitions_df[key], midpoint_v, atol=tol_v))
        crossover_fit = kmeans_time.fit(cluster_df[key])
        cluster_df['cluster'] = crossover_fit.predict(cluster_df[key])
        t_left.append(
                cluster_df[key].where(
                crossover_fit.cluster_centers_[cluster_df['cluster']] == crossover_fit.cluster_centers_.min()
                ).max()
            )
        t_left.append(
                cluster_df[key].where(
                crossover_fit.cluster_centers_[cluster_df['cluster']] == crossover_fit.cluster_centers_.max()
                ).min()
            )
    t_mid = (max(t_left)+min(t_right))/2
    hist_measurements.update({'t_mid': t_mid})

    # using the time +/-2.5% about the centre of the central eye estimate voltage levels
    dividers = [transitions_df[key].min()]
    dividers.append(diff(shorth_estimates)/2)
    dividers.append(transitions_df[key].max())
    t_tol = 0.025*(max(t_left)-min(t_right))
    mins = []
    maxes = []
    means = []
    for i in range(1, logic_levels+1):
        division_df = transitions_df.where(
            (dividers[i-1] <= transitions_df[key]) and (transitions_df[key] <= dividers[i])
            ).where(isclose(transitions_df['chunk_time'], t_mid, atol=t_tol))
        hist_measurements.update({f'logic_{i-1}':division_df.mean()})
        mins.append(division_df.min())
        maxes.append(division_df.max())
        means.append(division_df.mean())
        if i > 0 and i < logic_levels:
            hist_measurements.update({f'eye_height_{i-1}': mins[i]-maxes[i-1]})
            hist_measurements.update({f'eye_amplitude_{i-1}': means[i]-means[i-1]})

    for i in range(1, logic_levels):
        midpoint_v = (means[i-1]+means[i])/2
        tol_v = (means[i]-means[i-1])*0.01
        cluster_df = transitions_df.where(isclose(transitions_df[key], midpoint_v, atol=tol_v))
        crossover_fit = kmeans_time.fit(cluster_df[key])
        cluster_df['cluster'] = crossover_fit.predict(cluster_df[key])
        t_left = cluster_df[key].where(
                crossover_fit.cluster_centers_[cluster_df['cluster']] == crossover_fit.cluster_centers_.min()
                ).max()
        t_right = cluster_df[key].where(
                crossover_fit.cluster_centers_[cluster_df['cluster']] == crossover_fit.cluster_centers_.max()
                ).min()
        hist_measurements.update({f'eye_width_{i-1}':t_right-t_left})

    return hist, hist_measurements

def apply_mask(mask, eye):
    pass