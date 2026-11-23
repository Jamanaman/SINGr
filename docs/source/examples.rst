Examples
========
Example 1: Point to Point Network
---------------------------------
The first example simply provides a single point to point net with
no additional structures attached. Here the first input is 
controlled by an internally generated PRBS7 Bit Stream. This 
was the only arbitrary stream that was currently implemented as of 
v0.0.1. 

To achieve this, first one must generate the required SPICE models for 
simulation as is done with the following IBIS models 
(Altera Arria 5 FPGA IO Buffers and Micron v88a DRAM Receiver Models) 
as well as a transmission line model generated in Zuken eCADSTAR: ::

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

Then the structure is composed together into a ``CommunicationNet`` object where
input/output models or nodes, are connected, a transmission line model is provided and 
configuration parameters are provided. Additionally, the requested analyses are listed.
::

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

The measurements from the waveform analysis are as follows: ::

    |Fall Time: 1.846E-10|
    |Slew Rate Fall: -5.200E+09|
    |Rise Time: 1.904E-10|
    |Slew Rate Rise: 5.042E+09|
    |Overshoot: 5.258E-01|
    |Undershoot: -4.503E-01|
    |Settling Time: 1.243E-09|

.. image:: /examples_resources/ex1_wf.png
    :width: 80%
    :align: center

The measurements from the eye diagram analysis are as follows: :: 

    |Time Eye Center: 7.722E-10|
    |0 Level: -1.404E-01|
    |1 Level: 1.435E+00|
    |Eye Height 0: 1.100E+00|
    |Eye Bottom 0: 1.153E+00|
    |Eye Top 0: 5.336E-02|
    |Eye Amplitude 0: 1.576E+00|
    |Eye Width 0: 1.176E-09|
    |Eye Right 0: 1.357E-09|
    |Eye Left 0: 1.813E-10|

.. image:: /examples_resources/ex1_eye.png

Example 2: Daisy Chain
----------------------
This example implements a daisy chain with 2 communication nets which are nested to 
produce a structure where the 3 sender ICs are connected to 3 coupled transmission lines.
One of the ICs connects to a receiver at the end of this first stretch of transmission line,
whilst the others reach their receivers at the end of a second stretch of transmission line 
of equal characteristic impedance and length with a third sacrificial conductor. 


Waveform and Eye Analysis were performed on the daisy chain structure detailed in the following code snippet from examples/daisy_with_ibis_models.py:
::

    net2 = CommunicationNet(
            t_line_nodes_in=['net1_out1', 'net1_out2', 'gnd'],
            t_line_nodes_out=[receiver_1, receiver_1, 'gnd'],
            transmission_line=tline,
            l_tline_m=10e-3,
            clock_frequencies_Hz=[800e6, 800e6, None],
            delays_s=[None, None, None],
            v_logic=[(0, 1.2), (0, 1.2), None],
            stimuli=[None, None, None],
            terminations_start=[None, None, None],
            terminations_end=[None, None, None]
    )

    net1 = CommunicationNet(
            t_line_nodes_in=[sender_1, sender_2, sender_2],
            t_line_nodes_out=[net2, 'net1_out2', receiver_1],
            transmission_line=tline,
            l_tline_m=10e-3,
            clock_frequencies_Hz=[800e6, 800e6, 800e6],
            delays_s=[None, None, None],
            v_logic=[(0, 1.2), (0, 1.2), (0, 1.2)],
            stimuli=["TRIG", "LOW", "LOW"],
            terminations_start=[None, None, None],
            terminations_end=[None, None, None]
    )

Additionally, the analyses were manually configured with the specific node name to be checked and some specific 
configuration settings in a dictionary: ::

    analysis_config = {'key': 'pin_out_1_0',     
                'clock_frequency': comp.net_tree.clock_frequencies_Hz[0],
                'v_high': comp.net_tree.v_logic[0][1],
                'v_low':  comp.net_tree.v_logic[0][0],
                'threshold_pct': 0.8, 
                'statistical_jitter_s': 0,
                'visualise': True}
    results = compose_and_run_simulation(comp)
    analyse_simulation_results(comp, results, visualise=True, eye_config=analysis_config, waveform_config=analysis_config)

The measurements from the waveform analysis are as follows: ::

    |Fall Time: 1.365E-10|
    |Slew Rate Fall: -7.036E+09|
    |Rise Time: 1.357E-10|
    |Slew Rate Rise: 7.076E+09|
    |Overshoot: 5.061E-01|
    |Undershoot: -4.756E-01|
    |Settling Time: 9.807E-10|

.. image:: /examples_resources/ex2_wf.png
    :width: 80%
    :align: center
   
The measurements from the eye diagram analysis are as follows: :: 
    
    |Time Eye Center: 1.059E-09|
    |0 Level: -1.817E-01|
    |1 Level: 1.460E+00|
    |Eye Height 0: 1.027E+00|
    |Eye Bottom 0: 1.130E+00|
    |Eye Top 0: 1.027E-01|
    |Eye Amplitude 0: 1.642E+00|
    |Eye Width 0: 1.176E-09|
    |Eye Right 0: 1.634E-09|
    |Eye Left 0: 4.575E-10|

.. image:: /examples_resources/ex2_eye.png
    :width: 80%
    :align: center