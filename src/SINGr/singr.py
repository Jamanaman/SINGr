from InSpice.Spice.Simulator import Simulator
from InSpice.Probe.WaveForm import TransientAnalysis
from InSpice import Circuit
from random import randint
from typing import List
import pandas as pd, numpy as np

from . import net_builder as build, model

from .composition import Composition
from .analysis import perform_eye_analysis
from .sim_tools import make_pwl_from_bitstream

def compose_and_run_simulation(composition: Composition) -> TransientAnalysis:
        
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

def analyse_simulation_results(composition:Composition, results:TransientAnalysis):
    
    if "EYE" in composition.analyses:
        results_df = pd.DataFrame()
        results_df['pin_out_0_0'] = pd.Series(results['pin_out_0_0'], dtype=np.float64, name='pin_out_0_0')
        results_df['time'] = pd.Series(results.time, dtype=np.float64, name='time')
        perform_eye_analysis(
            results_df, 
            'pin_out_0_0', 
            composition.net_tree.clock_frequencies_Hz[0],
            composition.net_tree.v_logic[0][1],
            composition.net_tree.v_logic[0][0],
            0.9, 
            0
            )