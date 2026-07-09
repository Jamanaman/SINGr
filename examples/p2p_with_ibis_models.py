from SINGr.singr import compose_and_run_simulation, analyse_simulation_results
from SINGr.composition import Composition, CommunicationNet
from SINGr.model import IBISModel, CoupledTlineModel
from pathlib import Path

if __name__ == '__main__':
    
    sender_1 = IBISModel.build_model_from_file(
        model_name='12_cnio_r25c', component_name='5AGXMA3D4F27I3_',
        ibis_file='arria5.ibs', io_type='Output',
        corner='Typical', stimulus='TRIG',
        lib_path=Path(__file__).parent
        )
    
    sender_2 = IBISModel.build_model_from_file(
        model_name='12_cnio_r25c', component_name='5AGXMA3D4F27I3_',
        ibis_file='arria5.ibs', io_type='Output',
        corner='Typical', stimulus='LOW',
        lib_path=Path(__file__).parent
        )
    
    receiver_1 = IBISModel.build_model_from_file(
        model_name='DQ_IN_ODT40_1600', component_name='MT41J128M8DA',
        ibis_file='v88a_it.ibs', io_type='Input',
        corner='Typical',
        lib_path=Path(__file__).parent
        )

    tline = CoupledTlineModel.build_model_from_file(
        file_name='coupled_tline_x3.lib',
        lib_path=Path(__file__).parent
        )
    
    comp = Composition(
        name='DDR3_Test_point_to_point',
        net_tree=CommunicationNet(
            t_line_nodes_in=[sender_1, sender_2, sender_2],
            t_line_nodes_out=[receiver_1, receiver_1, receiver_1],
            transmission_line=tline,
            l_tline_m=50e-3,
            clock_frequencies_Hz=[800e6, 800e6, 800e6],
            delays_s=[None, None, None],
            v_logic=[(0, 1.2), (0, 1.2), (0, 1.2)],
            stimuli=["TRIG", "LOW", "LOW"],
            terminations_start=[None, None, None],
            terminations_end=[None, None, None]
        ),
        analyses=['EYE', 'WAVEFORM']
    )

    results = compose_and_run_simulation(comp)
    analyse_simulation_results(comp, results)