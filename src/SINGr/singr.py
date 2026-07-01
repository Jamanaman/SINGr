from InSpice.Spice.Simulator import Simulator
from InSpice.Probe.WaveForm import TransientAnalysis
from InSpice import Circuit
from random import randint
from typing import List
import pandas as pd, numpy as np

from . import topolib as tp, model

from .composition import Composition
from .analysis import perform_eye_analysis
from .sim_tools import make_pwl_from_bitstream

def compose_and_run_simulation(composition: Composition) -> TransientAnalysis:
        IC_input_pins: List[model.Model] = [
            model.build_model(
                'PIN', ic_input, 'Input', 'Typical'
                ) if ic_input is str else ic_input for ic_input in composition.inputs
            ]
        IC_output_pins: List[model.Model] = [
            model.build_model(
                'PIN', ic_output, 'Output', stimulus, 'Typical'
                ) if ic_output is str else ic_output for ic_output, stimulus in zip(
                    composition.outputs, composition.stimuli
                    )
            ]
        tline = model.build_model('TLine', composition.tlines[0]) if composition.tlines[0] is str else composition.tlines[0]
        
        # compose circuit structure based on topology
        circ: Circuit = tp.build_p2p(IC_input_pins, IC_output_pins, tline, composition.tline_lengths[0])

        # determine simulation timing features incl. simulation duration, max step size, initial settling delay
        min_freq_to_resolve = min(composition.clock_frequencies)
        max_period_to_resolve_s = 1/(max(composition.clock_frequencies))
        IBIS_MIN_SAMPLES_PER_RISE_AND_FALL = 200
        minimum_periods = 3
        max_step_s = 1/min_freq_to_resolve/IBIS_MIN_SAMPLES_PER_RISE_AND_FALL 
        min_duration_s = max_period_to_resolve_s*minimum_periods
        delay = 1/min_freq_to_resolve

        # compose any external stimuli
        for i, (stimulus, freq) in enumerate(zip(composition.stimuli, composition.clock_frequencies)):
            if stimulus == 'TRIG':
                ## TODO add prespecified bitstreams as option
                period = 1/freq
                min_duration_s = max((128+1)*period, min_duration_s)
                pwl_vals = make_pwl_from_bitstream([randint(0, 1) for _ in range(128)], period)
                circ.PieceWiseLinearVoltageSource(
                    f'pwl{i}', f'trig_{i}', circ.gnd, 
                    pwl_vals, repeat_time=0, delay_time=delay)

        simulator = Simulator.factory()
        simulation = simulator.simulation(circ)
        results: TransientAnalysis  = simulation.transient(step_time=max_step_s/100, end_time=min_duration_s, max_time=max_step_s)
        return results

def analyse_simulation_results(composition:Composition, results:TransientAnalysis):
    
    if "EYE" in composition.analyses:
        results_df = pd.DataFrame()
        results_df['tline_out0'] = pd.Series(results['tline_out0'], dtype=np.float64, name='tline_out0')
        results_df['time'] = pd.Series(results.time, dtype=np.float64, name='time')
        perform_eye_analysis(
            results_df, 
            'tline_out0', 
            composition.clock_frequencies[0],
            composition.v_logic[0][1],
            composition.v_logic[0][0],
            0.9, 
            0
            )