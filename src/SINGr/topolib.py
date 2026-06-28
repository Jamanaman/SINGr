from InSpice import Circuit
from typing import List, Literal, Optional
from .model import Model
import re

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
    sckt_line_end = model.subcircuit_card.find(sub='\n', start=sckt_line_start, end=None)
    param_names = re.findall(_NG_PARAMS, model.subcircuit_card[sckt_line_start:sckt_line_end])
    param_dict = {}
    for param_name in param_names:
        instance_param_name = param_name+'_'+instance_name
        circ.parameter(instance_param_name, default_val)
        param_dict.update({param_name: f'{{{instance_param_name}}}'})
    circ.X(instance_name, model.model_name, *pins, **param_dict)

def build_p2p(
        ins: List[Model], outs: List[Model], 
        tline:Model, terminations: Optional[List[Model]] = None
        ) -> Circuit:
    '''
    This function builds an ngSPICE netlist of a point to point communication net 
    which takes a list of network inputs ie input signals providers, network output connections ie input buffers,
    and a model representing the single transmission line in the middle.

    Future Improvements:
    - Support for multiple pieces of transmission line. Potentially by chaining p2p networks.
    - Support for terminations at either end of the net.
    '''

    critical_signal = ins[0].model_name
    circ = Circuit(f"Point2Point_{critical_signal}")
    for idx, i, o in zip(range(len(ins)), ins, outs):
        circ.raw_spice = circ.raw_spice + (i.subcircuit_card) + '\n\n'
        circ.raw_spice = circ.raw_spice + (o.subcircuit_card) + '\n\n'
        instantiate_subckt_with_instance_params(circ, i, [f'TLine_in{idx}'], f'input{idx}')
        instantiate_subckt_with_instance_params(circ, o, [f'TLine_out{idx}'], f'output{idx}')
        
    in_pins = [pin for pin in circ.node_names if pin.startswith('TLine_in')]
    out_pins = [pin for pin in circ.node_names if pin.startswith('TLine_out')]
    circ.X(f'TLINE', tline.model_name, *out_pins, circ.gnd, *in_pins, circ.gnd)

    return circ