'''
Library of different constructor functions which produce generic
chip-to-chip communication circuits for analysis. 
'''

from InSpice import Circuit
from typing import List, Optional, Dict
import re
from numpy.random import randint

from .model import Model
from .composition import CommunicationNet
from .sim_tools import find_subckt_line, make_pwl_from_bitstream

_NG_PARAMS = re.compile(r'(\w+)(?:=)(?:\d+)')

def instantiate_subckt_with_instance_params(
        circ:Circuit, model:Model, 
        pins:List[str], instance_name:str = '', 
        custom_params: Dict = {}, default_val:str = '0'
        ) -> None:
    '''
    Instantiates a subcircuit instance of the given subcircuit model and adds named parameters to the netlist
    for later editing. 
    '''
    sckt_line_start, sckt_line_end = find_subckt_line(model.subcircuit_card)
    param_names = re.findall(_NG_PARAMS, model.subcircuit_card[sckt_line_start:sckt_line_end])
    param_dict = {}
    for param_name in param_names:
        instance_param_name = param_name+'_'+instance_name
        circ.parameter(instance_param_name, custom_params.get(param_name, default_val))
        param_dict.update({param_name: f'{{{instance_param_name}}}'})
    circ.X(instance_name, model.spice_model_name, *pins, **param_dict)

def traverse_net_tree_and_build(net_tree: CommunicationNet, tree_level:int = 0, circ: Circuit = Circuit('Net_Tree')) -> Circuit:
    tline_ins = []
    for idx, (node_in, termination_in, stimulus, freq, delay) in enumerate(zip(net_tree.t_line_nodes_in, net_tree.terminations_start, net_tree.stimuli, net_tree.clock_frequencies_Hz, net_tree.delays_s)):
        name_node_in = f'pin_in_{tree_level}_{idx}'
        name_series_node = f'line_in_{tree_level}_{idx}'
        series_termination = False
        if not termination_in is None:
            circ.include(termination_in.lib)
            sckt_line:str = find_subckt_line(termination_in.subcircuit_card, True)
            termination_nodes = []
            for entry in sckt_line.split(' ')[2:]:
                if not '=' in entry:
                    termination_nodes.append(entry)
            if len(termination_nodes) > 1:
                series_termination = True
                instantiate_subckt_with_instance_params(circ, termination_in, [name_node_in, name_series_node], f'start_termination_{tree_level}_{idx}')
                tline_ins.append(name_series_node)
        if isinstance(node_in, Model):
            params_dict = {}
            if not net_tree.clock_frequencies_Hz[idx] is None:
                params_dict.update({'freq': net_tree.clock_frequencies_Hz[idx]})
            circ.include(node_in.lib)
            if 'TRIG' in node_in.subcircuit_card and stimulus == 'TRIG':
                if freq is None:
                     raise ValueError('TRIG Stimulus given without clock frequency')
                period = 1/freq
                pwl_vals = make_pwl_from_bitstream(randint(2, size=128), period)
                circ.PieceWiseLinearVoltageSource(
                    f'pwl{idx}', f'trig_{tree_level}_{idx}', circ.gnd, 
                    pwl_vals, repeat_time=0, delay_time=delay)
                instantiate_subckt_with_instance_params(circ, node_in, [name_node_in, f'trig_{tree_level}_{idx}'], f'sender_{tree_level}_{idx}')
            else:
                instantiate_subckt_with_instance_params(circ, node_in, [name_node_in], f'sender_{tree_level}_{idx}')
            if not series_termination:
                tline_ins.append(name_node_in)

    # Output nodes
    tline_outs = []
    for idx, (node_out, termination_out) in enumerate(zip(net_tree.t_line_nodes_out, net_tree.terminations_end)):
        name_node_out = f'pin_out_{tree_level}_{idx}'
        name_series_node = f'line_out_{tree_level}_{idx}'
        series_termination = False
        
        # First handle termination
        if not termination_out is None:
            circ.include(termination_out.lib)
            sckt_line:str = find_subckt_line(termination_out.subcircuit_card, True)
            termination_nodes = []
            for entry in sckt_line.split(' ')[2:]:
                if not '=' in entry:
                    termination_nodes.append(entry)
            if len(termination_nodes) > 1:
                series_termination = True
                instantiate_subckt_with_instance_params(circ, termination_out, [name_node_out, name_series_node], f'end_termination_{tree_level}_{idx}')
        
        # then handle node
        if isinstance(node_out, Model):
            params_dict = {}
            if not net_tree.clock_frequencies_Hz[idx] is None:
                params_dict.update({'freq': net_tree.clock_frequencies_Hz[idx]})
            circ.include(node_out.lib)
            instantiate_subckt_with_instance_params(circ, node_out, [name_node_out], f'receiver_{tree_level}_{idx}')
        # if node is another tree then traverse deeper and recurse back up
        elif type(node_out) is CommunicationNet:
            circ = traverse_net_tree_and_build(node_out, tree_level+1, circ)
        
        if not series_termination:
            tline_outs.append(name_node_out)
        else:
            tline_outs.append(name_series_node)

    # Add transmission line model
    circ.include(net_tree.transmission_line.lib)
    circ.CoupledMulticonductorLine(
        f'TLINE', *tline_outs, circ.gnd, 
        *tline_ins, circ.gnd, length=net_tree.l_tline_m, 
        model=net_tree.transmission_line.model_name
        )
    
    return circ