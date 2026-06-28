from pybis2spice import subcircuit as sckt, data_model as dm
from ecdtools.ibis import IbsFile #type:ignore
from dataclasses import dataclass
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Literal
import regex as re

# supported RLGC File Sources
_SOURCE = Literal['Zuken'] # TODO add support for openEMS to generate RLGC values

def build_model(model_type: str, **kwargs):
    if model_type == 'PIN':
        if not kwargs.get('ibis_file') is None:
            return IBISModel.build_model_from_file(**kwargs)
        
    if model_type == 'TLINE':
        if not kwargs.get('file_name') is None:
            return CoupledTlineModel.build_model_from_file(**kwargs)

@dataclass
class Model(ABC):
    model_name: str
    component_name: str
    subcircuit_card: str
    lib: Path

    @abstractmethod
    @classmethod
    def build_model_from_file(cls, *args, **kwargs) -> Model:
        raise NotImplementedError()

@dataclass
class CoupledTlineModel(Model):
    @classmethod
    def build_model_from_file(cls, file_name:str, length:int, source:_SOURCE='Zuken', lib_path:str = '.') -> Model:
        vals = [[], [], [], []]
        model_name = f'cpl_{file_name}_{length}'
        spice_str = f'.SUBCKT {model_name}'
        _tline_str = f'.MODEL {model_name} length={length}'
        if source == 'Zuken':
            try:
                with open(Path('.', file_name), 'r') as f:
                    idx = 0
                    for line in f.readlines():
                        if 'Lo' in line:
                            idx = 0
                        elif 'Co' in line:
                            idx = 1
                        elif 'Ro' in line:
                            idx = 2
                        elif 'Go' in line:
                            idx = 3
                        else:
                            row = []
                            for val in re.findall(r'[\d.e-]+', line):
                                row.append(float(val))
                            vals[idx].append(row)

            except FileNotFoundError as e:
                e.add_note(f"Transmission Line RLGC Model file: {file_name} not found.")
                raise e
        if not len(vals[0]) == len(vals[1]) and not len(vals[2]) == len(vals[3]):
            raise ValueError()
        for property, values in zip(['L', 'C', 'R', 'G'], vals):
            _tline_str = _tline_str + f' {property}='
            for row in values:
                for val in row:
                    _tline_str = _tline_str + f' {val}'
        _tline_str = _tline_str + ' \n'

        ins = ' '.join([f'in{i}' for i in range(len(vals[0]))])

        spice_str = spice_str + ins

        spice_str = spice_str + 'ref1'
        
        outs = ' '.join([f'out{i}' for i in range(len(vals[0]))])
        
        spice_str = spice_str + outs

        spice_str = spice_str + 'ref2 \n'

        spice_str = spice_str + f'P1 {outs} ref1 {ins} ref2 {model_name} \n'
        
        spice_str = spice_str + _tline_str + '.ENDS'
        subcircuit_card_path = Path(lib_path, f'{model_name}.lib')
        return CoupledTlineModel(model_name=model_name, component_name='Coupled Transmission Line', subcircuit_card=spice_str, lib=subcircuit_card_path)
        

@dataclass
class IBISModel(Model):  
    @classmethod
    def build_model_from_file(cls, model_name:str, component_name: str, ibis_file:str, io_type:sckt._IO_TYPE, corner:sckt._CORNER, stimulus:sckt._STIMULUS='ALL', lib_path:str = '.') -> Model:
        try:
            ibis = IbsFile(ibis_file, transform=True)
        except FileNotFoundError as e:
            e.add_note(f"IBIS Model file: {ibis_file} not found.")
            raise e

        model = dm.DataModel(ibis_file=ibis, model_name=model_name, component_name=component_name)
        spice_str = sckt.create_ngspice_output_model(model, corner, io_type, truncation=0.01, stimulus=stimulus)
        if stimulus == 'ALL':
            subcircuit_card_path = Path(lib_path, f'{model_name}_{component_name}_{corner}_{io_type}.lib')
        else:
            subcircuit_card_path = Path(lib_path, f'{model_name}_{component_name}_{corner}_{io_type}_{stimulus}.lib')
        with open(subcircuit_card_path, 'a+') as f:
            f.write(spice_str)
        return IBISModel(model_name=model.model_name, component_name=component_name, subcircuit_card=spice_str, lib=subcircuit_card_path)