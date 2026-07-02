from pybis2spice import subcircuit as sckt, circuit_builder as ckt_build, data_model as dm
from ecdtools import ibis as ecd #type:ignore
from dataclasses import dataclass
from pathlib import Path
from abc import ABC
from typing import Literal, Optional
import regex as re
import os

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
    spice_model_name: str

    @classmethod
    def build_model_from_file(cls, *args, **kwargs) -> Model:
        raise NotImplementedError()

@dataclass
class CoupledTlineModel(Model):
    @classmethod
    def build_model_from_file(cls, file_name:str,  source:_SOURCE='Zuken', lib_path:str = '.') -> Model:
        vals = [[], [], [], []]
        model_name = f'cpl_{file_name.split('.')[0]}'
        _tline_str = f'.MODEL {model_name} CPL length=0.1'
        if source == 'Zuken':
            try:
                with open(Path(lib_path, file_name), 'r') as f:
                    idx = 0
                    for line in f.readlines():
                        if '.model' in line:
                            continue
                        elif 'Lo' in line:
                            idx = 0
                        elif 'Co' in line:
                            idx = 1
                        elif 'Ro' in line:
                            idx = 2
                        elif 'Go' in line:
                            idx = 3
                        elif 'Rs' in line:
                            break
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
            property_vals = ''
            dim = len(values)
            for col in range(dim):
                for row in range(col, dim):
                    property_vals += str(values[row][col]) + ' '
            property_vals += ' '
            _tline_str += property_vals
        _tline_str = _tline_str + ' \n'
        
        spice_str = _tline_str
        subcircuit_card_path = Path(lib_path, f'{model_name}.lib')
        with open(subcircuit_card_path, 'w+') as fp:
            fp.write(spice_str)
        return CoupledTlineModel(model_name=model_name, component_name='Coupled Transmission Line', subcircuit_card=spice_str, lib=subcircuit_card_path, spice_model_name=model_name)
        

@dataclass
class IBISModel(Model):  
    @classmethod
    def build_model_from_file(cls, model_name:str, component_name: str, ibis_file:str, io_type:sckt._IO_TYPE, corner:sckt._CORNER, stimulus:Optional[sckt._STIMULUS]='ALL', lib_path:Path|str = '.') -> Model:
        if stimulus == 'ALL' or stimulus is None: 
            spice_model_name = f'{model_name}_{io_type}_{corner}'
            subcircuit_card_path = Path(lib_path, f'{model_name}_{component_name}_{corner}_{io_type}.lib')
        else:
            spice_model_name = f'{model_name}_{io_type}_{corner}_{stimulus}'
            subcircuit_card_path = Path(lib_path, f'{model_name}_{component_name}_{corner}_{io_type}_{stimulus}.lib')
        if subcircuit_card_path.name in os.listdir(Path(lib_path)):
            spice_str = open(subcircuit_card_path, 'r').read()
            return IBISModel(model_name=model_name, component_name=component_name, subcircuit_card=spice_str, lib=subcircuit_card_path, spice_model_name=spice_model_name)
        try:
            ibis = ecd.load_file(Path(lib_path) / ibis_file, transform=True)
        except FileNotFoundError as e:
            e.add_note(f"IBIS Model file: {ibis_file} not found.")
            raise e

        model = dm.DataModel(ibis_file=ibis, model_name=model_name, component_name=component_name)
        if stimulus == 'ALL':
            subcircuit_card_path = Path(lib_path, f'{model_name}_{component_name}_{corner}_{io_type}.lib')
        else:
            subcircuit_card_path = Path(lib_path, f'{model_name}_{component_name}_{corner}_{io_type}_{stimulus}.lib')
        spice_str = ckt_build.generate_spice_model_file(io_type, 'ngSPICE', model, corner, truncation=0.01, stimulus=stimulus, output_filepath=subcircuit_card_path)

        return IBISModel(model_name=model.model_name, component_name=component_name, subcircuit_card=spice_str, lib=subcircuit_card_path)