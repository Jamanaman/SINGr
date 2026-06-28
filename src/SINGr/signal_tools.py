from numpy import isclose
import pandas as pd 

def walk_back_to_logic_level(
        df:pd.DataFrame, key:str, 
        t_transition_detected: float, logic_level_v:float,
        v_tol: float
        ) -> float:
    '''
    Walks back from transition being detected to the previous logic level.
    '''

    df_walkback = df.where(df['time']<t_transition_detected).sort_values(['time'], ascending=False)
    for row in df_walkback.itertuples():
        if isclose(row[key], logic_level_v, atol=v_tol):
            return row['time']
    else:
        raise Exception()
        
def classify_period(
        df:pd.DataFrame, key:str, 
        v_high_th:float, v_low_th:float, 
        min_transition_slope:float
        ) -> pd.DataFrame:
    '''
    Classifies time series in single clock period as one of 'high', 'low',
    'rising', 'falling' or None if no valid event can be classified due to the signal
    staying mostly in between the logic thresholds.
    '''

    diff_df = df.rolling(10).median().diff().median()
    dxdt = diff_df[key]/diff_df['time']
    if dxdt > min_transition_slope:
        df['event'] = 'rising'
        return df
    elif dxdt < -min_transition_slope:
        df['event'] = 'falling'
        return df
    else:
        if df[key].median()>v_high_th:
            df['event'] = 'high'
            return df
        elif df[key].median()<v_low_th:
            df['event'] = 'low'
            return df
        else:
            df['event'] = None
            return df