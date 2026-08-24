'''
Module with generic utilities for generating simulations.
'''

from typing import List, Tuple

def make_pwl_from_bitstream(bitstream:List[int], period:float) -> List[Tuple[float]]:
    '''
    Make a PWL value sequence to be used in any InSpice source which implements PieceWiseLinearMixIn.
    '''
    pwl_vals = []
    for i, v_bit in enumerate(bitstream):
        pwl_vals.append((i*period, v_bit))
        pwl_vals.append((i*period+period*0.99, v_bit))
    return pwl_vals

def find_subckt_line(subcircuit_card: str, return_string: bool = False) -> str|Tuple[int,int]:
    sckt_line_start = subcircuit_card.find('.SUBCKT')
    sckt_line_end = subcircuit_card.find('\n', sckt_line_start)
    if return_string:
        return subcircuit_card[sckt_line_start:sckt_line_end]
    return (sckt_line_start, sckt_line_end)