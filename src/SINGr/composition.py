'''
Module comprised of Pydantic BaseModel \'Composition\' which
enables one to compose an ngSPICE simulation to be run from
a configuration.
'''

from pydantic import BaseModel
from typing import List, Optional, Tuple
from .topolib import _TOPOLOGIES
from .analysis import _ANALYSES
from .model import Model

class Composition(BaseModel):
    name: str
    topology: _TOPOLOGIES
    analyses: List[_ANALYSES]
    inputs: List[str|Model]
    outputs: List[str|Model]
    tlines: List[str|Model]
    tline_lengths: List[float]
    terminations: Optional[List[str|Model]] = None
    stimuli: List[str]
    clock_frequencies: List[float]
    v_logic: List[Tuple[float, float]]
    