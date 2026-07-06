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
    name: str
    analyses: List[_ANALYSES]
    net_tree: CommunicationNet

class CommunicationNet(BaseModel):
    t_line_nodes_in: List[Model|str]
    t_line_nodes_out: List[Model|CommunicationNet|str]
    transmission_line: Model
    l_tline_m: float
    clock_frequencies_Hz: List[Optional[float]]
    delays_s: List[Optional[float]]
    v_logic: List[Optional[Tuple[Optional[float], float]]]
    stimuli: List[Optional[str|int]]
    terminations_start: List[Optional[Model]]
    terminations_end: List[Optional[Model]]