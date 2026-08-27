from InSpice.Spice.Simulator import Simulator
from InSpice.Probe.WaveForm import TransientAnalysis
from InSpice import Circuit
import pandas as pd, numpy as np
from typing import Dict

from . import net_builder as build

from .composition import Composition
from .analysis import perform_eye_analysis, perform_waveform_analysis

def compose_and_run_simulation(composition: Composition) -> TransientAnalysis:
    '''
    Utility function which takes a Composition object and builds the InSPICE circuit
    to be simulated, calculates simulation parameters such as duration and max time step
    and runs the simulation.

    Parameters
    ----------
    composition : Composition
        Structure to be simulated

    Returns
    -------
    TransientAnalysis
        Results of simulation

    Raises
    ------
    ValueError
        No clock frequency provided for an active stimulus.
    '''
    # determine simulation timing features incl. simulation duration, max step size, initial settling delay
    # TODO apply frequency check to all layers of net tree
    min_freq_to_resolve = min(composition.net_tree.clock_frequencies_Hz)
    max_period_to_resolve_s = 1/(max(composition.net_tree.clock_frequencies_Hz))
    IBIS_MIN_SAMPLES_PER_RISE_AND_FALL = 200
    minimum_periods = 3
    max_step_s = 1/min_freq_to_resolve/IBIS_MIN_SAMPLES_PER_RISE_AND_FALL 
    min_duration_s = max_period_to_resolve_s*minimum_periods
    min_delay = 1/min_freq_to_resolve
    # TODO apply delay to all levels of net tree
    delays_new = []
    for delay in composition.net_tree.delays_s:
        if delay is None:
            delays_new.append(min_delay)
        else:
            delays_new.append(delay+min_delay)
    composition.net_tree.delays_s = delays_new
    for idx, stimulus in enumerate(composition.net_tree.stimuli):
        if stimulus == 'TRIG':
            if not composition.net_tree.clock_frequencies_Hz[idx] is None:
                min_duration_s = (128+1)/composition.net_tree.clock_frequencies_Hz[idx]
            else:
                raise ValueError("No clock frequency given for active stimulus.")
    # compose circuit structure based on topology
    circ = Circuit(composition.name)
    circ: Circuit = build.traverse_net_tree_and_build(composition.net_tree, circ=circ)

    simulator = Simulator.factory()
    simulation = simulator.simulation(circ)
    results: TransientAnalysis  = simulation.transient(step_time=max_step_s/100, end_time=min_duration_s, max_time=max_step_s)
    return results

def analyse_simulation_results(
        composition:Composition, results:TransientAnalysis, 
        visualise:bool=False, output_report:bool=True, 
        eye_config:Dict={}, waveform_config:Dict={}
        ):
    '''
    Wrapper function that takes simulation setup (Composition) and simulation results (TransientAnalysis)
    and passes them to the required analysis workflows.

    Parameters
    ----------
    composition : Composition
        Structure that was simulated.
    results : TransientAnalysis
        Results data from transient analysis performed by InSPICE
    visualise : bool, optional
        generates plots if true
    output_report : bool, optional
        generates reports if true
    eye_config : Dict, optional
        changes the configuration of eye analysis
    waveform_config : Dict, optional
        changes the configuration of waveform analysis
    '''
    results_df = pd.DataFrame()
    results_df['time'] = pd.Series(results.time, dtype=np.float64, name='time')
    if "EYE" in composition.analyses:
        config = {
            'key': 'pin_out_0_0',
            'clock_frequency': composition.net_tree.clock_frequencies_Hz[0],
            'v_high': composition.net_tree.v_logic[0][1],
            'v_low': composition.net_tree.v_logic[0][0],
            'threshold_pct': 0.9,
            'statistical_jitter_s': 0,
            'datastream': None,
            'visualise': True,
            'output_report': False 
        }
        config.update(eye_config)
        if not results_df.get(config['key']):
            results_df[config['key']] = pd.Series(results[config['key']], dtype=np.float64, name=config['key'])
        perform_eye_analysis(
            results_df, 
            config['key'],
            config['clock_frequency'],
            config['v_high'],
            config['v_low'],
            config['threshold_pct'],
            config['statistical_jitter_s'],
            config['datastream'],
            config['visualise'], 
            config['output_report']
            )
    if "WAVEFORM" in composition.analyses:
        config = {
            'key': 'pin_out_0_0',
            'clock_frequency': composition.net_tree.clock_frequencies_Hz[0],
            'v_high': composition.net_tree.v_logic[0][1],
            'v_low': composition.net_tree.v_logic[0][0],
            'threshold_pct': 0.9,
            'datastream': None,
            'visualise': True,
            'output_report': False 
        }
        config.update(waveform_config)
        if results_df.get(config['key']) is None:
            results_df[config['key']] = pd.Series(results[config['key']], dtype=np.float64, name=config['key'])
        perform_waveform_analysis(
            results_df, 
            config['key'],
            config['clock_frequency'],
            config['v_high'],
            config['v_low'],
            config['threshold_pct'],
            config['datastream'],
            config['visualise'], 
            config['output_report']
            )