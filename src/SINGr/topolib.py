'''
Library of different constructor functions which produce generic
chip-to-chip communication circuits for analysis. 
'''

from InSpice import Circuit
from typing import List, Literal, Optional
import re

from .model import Model

_TOPOLOGIES = Literal['Point2Point']

_NG_PARAMS = re.compile(r'(\w+)(?:=)(?:\d+)')

def instantiate_subckt_with_instance_params(
        circ:Circuit, model:Model, 
        pins:List[str], instance_name:str = '', 
        default_val:str = '0'
        ) -> None:
    '''
    Instantiates a subcircuit instance of the given subcircuit model and adds named parameters to the netlist
    for later editing. 
    '''
    sckt_line_start = model.subcircuit_card.find('.SUBCKT')
    sckt_line_end = model.subcircuit_card.find('\n', sckt_line_start)
    param_names = re.findall(_NG_PARAMS, model.subcircuit_card[sckt_line_start:sckt_line_end])
    param_dict = {}
    for param_name in param_names:
        instance_param_name = param_name+'_'+instance_name
        circ.parameter(instance_param_name, default_val)
        param_dict.update({param_name: f'{{{instance_param_name}}}'})
    circ.X(instance_name, model.spice_model_name, *pins, **param_dict)

def build_p2p(
        input_pins: List[Model], output_pins: List[Model], 
        tline:Model, tline_length:float, 
        terminations: Optional[List[Model]] = None
        ) -> Circuit:
    '''
    This function builds an ngSPICE netlist of a point to point communication net 
    which takes a list of network inputs ie input signals providers, network output connections ie input buffers,
    and a model representing the single transmission line in the middle.

    Future Improvements:
    - Support for multiple pieces of transmission line. Potentially by chaining p2p networks.
    - Support for terminations at either end of the net.
    '''

    critical_signal = output_pins[0].model_name
    circ: Circuit = Circuit(f"Point2Point_{critical_signal}")
    for idx, i, o in zip(range(len(input_pins)), input_pins, output_pins):
        circ.include(i.lib)
        circ.include(o.lib)
        if 'TRIG' in i.subcircuit_card:
            instantiate_subckt_with_instance_params(circ, i, [f'sender{idx}', f'trig_{idx}'], f'sender{idx}')
        else:
            instantiate_subckt_with_instance_params(circ, i, [f'sender{idx}'], f'sender{idx}')
        instantiate_subckt_with_instance_params(circ, o, [f'TLine_out{idx}'], f'receiver{idx}')
        circ.R(f's{idx}', f'sender{idx}', f'TLine_in{idx}', 25)
        
    
    tline_ins = [pin for pin in circ.node_names if pin.startswith('TLine_in')]
    tline_outs = [pin for pin in circ.node_names if pin.startswith('TLine_out')]
    circ.include(tline.lib)
    circ.CoupledMulticonductorLine(f'TLINE', *tline_outs, circ.gnd, *tline_ins, circ.gnd, length=tline_length, model=tline.model_name)

    return circ