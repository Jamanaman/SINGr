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

    |Time Eye Center: 1.779E-09|
    |0 Level: -2.249E-01|
    |1 Level: 1.440E+00|
    |Eye Height 0: 1.080E+00|
    |Eye Amplitude 0: 1.665E+00|
    |Eye Width 0: 3.956E-04|

.. image:: /examples_resources/ex1_wf.png
    :width: 80%
    :align: center

The measurements from the eye diagram analysis are as follows: :: 

    |Fall Time: 1.225E-09|
    |Slew Rate Fall: -7.835E+08|
    |Rise Time: 9.873E-10|
    |Slew Rate Rise: 9.724E+08|
    |Overshoot: -4.354E-02|
    |Undershoot: -5.082E-02|
    |Settling Time: 1.243E-09|

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

The measurements from the waveform analysis are as follows: ::

    |Fall Time: 1.003E-09|
    |Slew Rate Fall: -9.572E+08|
    |Rise Time: 1.056E-09|
    |Slew Rate Rise: 9.091E+08|
    |Overshoot: 2.616E-02|
    |Undershoot: -1.222E-01|
    |Settling Time: 1.238E-09|

.. image:: /examples_resources/ex2_wf.png
    :width: 80%
    :align: center
   
The measurements from the eye diagram analysis are as follows: :: 
    
    |Time Eye Center: 3.041E-09|
    |0 Level: 1.041E-01|
    |1 Level: 1.053E+00|
    |Eye Height 0: 5.933E-01|
    |Eye Amplitude 0: 9.491E-01|
    |Eye Width 0: 5.062E-04|

.. image:: /examples_resources/ex2_eye.png
    :width: 80%
    :align: center