'''
Module containing all functions which enable one to build, visualise and characterise 
signal eye diagrams.
'''

from numpy import histogram2d, floor, ceil, linspace, mean, diff, argmin
from scipy.signal import fftconvolve
from scipy.stats import norm
import kmeans1d
import pandas as pd 

from .signal_tools import walk_forward_to_logic_level, classify_period

def chunk_data_for_eye(transitions_df: pd.DataFrame, chunk_periods:int=3):
    '''
    Chunk the available data into consecutive sequences which can be identified as valid events.
    '''
    chunk_df = pd.DataFrame()
    for chunk, data in transitions_df.groupby(transitions_df['period_index'] // chunk_periods):
        data['sequence'] = chunk if not None in data['event'].unique() else None
        data['chunk_time'] = data['time']-data['time'].min()
        data['sequence_events'] = ' '.join([event for event in data['event'].unique()])
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

    return chunk_df, hist_measurements

def apply_mask(mask, eye):
    pass