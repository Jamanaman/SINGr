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