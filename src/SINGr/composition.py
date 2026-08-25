'''
Module comprised of Pydantic BaseModel \'Composition\' which
enables one to compose an ngSPICE simulation to be run from
a configuration.
'''

from pydantic import BaseModel
from typing import List, Optional, Tuple
from .analysis import _ANALYSES
from .model import Model

class Composition(BaseModel):
    '''
    Compositions are simulation recipes comprising of a structure to simulate, configured specifically
    and a series of simulation and analysis workflows to perform on said structure.
    '''
    name: str
    '''name of the composition, used for identification'''
    analyses: List[_ANALYSES]
    '''a list of simulation and analysis workflows to run on the given net tree'''
    net_tree: CommunicationNet
    '''the structure to be simulated'''

class CommunicationNet(BaseModel):
    '''
    The CommunicationNet is a structure intended to be used recursively with each net being built
    around a transmission line. At each of the inputs of the transmission line, one can connect: 
    
    - an input node which may either be a simple SPICE node name or may be a subcircuit model to connect to,
    - and a termination which may either be in series with the input node and transmission line input or parallel

    At each of the outputs of the transmission line, one can connect: 

    - an output node which may either be a simple SPICE node name, a subcircuit model to connect to or even another communication net,
    - and a termination which may either be in series with the output node and transmission line output or parallel,

    For all input nodes, one can also specify a number of configuration features including clock frequency, stimulus delay, logic levels, 
    and stimulus definition.

    The transmission line that connects these nodes must simply be another model which provides sufficient input and output nodes for all inputs
    and outputs. If this is a model configurable with length such as a distributed RLC model, one can also specify the length of the transmission line.
    '''
    t_line_nodes_in: List[Model|str]
    '''connections at input nodes'''
    t_line_nodes_out: List[Model|CommunicationNet|str]
    '''connections at output nodes'''
    transmission_line: Model
    '''transmission line model'''
    l_tline_m: float = 0
    '''transmission line length'''
    clock_frequencies_Hz: List[Optional[float]] = []
    '''input stimulus clock frequencies'''
    delays_s: List[Optional[float]] = []
    '''stimulus delays in seconds'''
    v_logic: List[Optional[Tuple[Optional[float], float]]] = []
    '''logic levels (currently only 2)'''
    stimuli: List[Optional[str|int]] = []
    '''input stimuli corresponding to the input nodes'''
    terminations_start: List[Optional[Model]] = []
    '''terminations connected at the input nodes'''
    terminations_end: List[Optional[Model]] = []
    '''terminations connected at the output nodes'''