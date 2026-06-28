from numpy.typing import NDArray
from typing import List

def count_contiguous_cells(x:int, y:int, bw_hist:NDArray, hist_counted:NDArray, count:int=0, group_coords:List = []): 
    '''
    Counts contiguous cells from a starting cell using a recursive quadtree search.
    '''
    if bw_hist[x+1, y] and not hist_counted[x+1, y]>0:
        hist_counted[x+1, y] = True
        group_coords.append((x+1, y))
        count += count_contiguous_cells(x+1, y, bw_hist, hist_counted, count+1, group_coords)
    if bw_hist[x-1, y] and not hist_counted[x-1, y]>0:
        hist_counted[x-1, y] = True
        group_coords.append((x-1, y))
        count += count_contiguous_cells(x-1, y, bw_hist, hist_counted, count+1, group_coords)
    if bw_hist[x, y+1] and not hist_counted[x, y+1]>0:
        hist_counted[x, y+1] = True
        group_coords.append((x, y+1))
        count += count_contiguous_cells(x+1, y, bw_hist, hist_counted, count+1, group_coords)
    if bw_hist[x, y-1] and not hist_counted[x, y-1]>0:
        hist_counted[x, y-1] = True
        group_coords.append((x, y-1))
        count += count_contiguous_cells(x, y-1, bw_hist, hist_counted, count+1, group_coords)
    return count