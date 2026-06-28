from . import topolib as tp, model
from pydantic import BaseModel
from typing import List, Optional
from InSpice.Spice.Simulator import Simulator
from InSpice import Circuit

class Composition(BaseModel):
    name: str
    inputs: List[str]
    outputs: List[str]
    topology: tp._TOPOLOGIES
    tlines: List[str]
    terminations: Optional[List[str]] = None
    stimuli: List[str]
    clock_frequencies: List[float]

    def compose_simulation(self):
        simulator = Simulator.factory()

        IC_inputs = [model.build_model('PIN', ic_input, 'Input') for ic_input in self.inputs]
        IC_outputs = [model.build_model('PIN', ic_output, 'Output', stimulus) for ic_output, stimulus in zip(self.outputs, self.stimuli)]
        tline = model.build_model('TLine', self.tlines[0])

        circ: Circuit = tp.build_p2p(IC_inputs, IC_outputs, tline)

        simulator = Simulator.factory()
        simulation = simulator.simulation(circ, temperature=25, nominal_temperature=25)
        return simulation

    

    