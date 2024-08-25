'''
Written by Mengzhan Liufu at Yu Lab, the University of Chicago
'''
# from collections import deque
from scipy.signal import butter
import numpy as np
from echt import echt
from trodes_connection import call_statescript


class Detector:

    def __init__(
        self,
        detector_name: str,
        data_buffer,
        statescript_fxn_num: int,
        trodes_hardware,
        window_size = 400,
        target_phase = np.pi,
        target_lowcut = 6,
        target_highcut = 9,
        fs_filter = 1500,
        fltr_order = 2,
    ):
        self.name = detector_name
        print(f'Starting new process for {detector_name}')

        # For online filtering
        self.data_buffer = data_buffer
        self.window_size = window_size
        assert self.window_size <= len(data_buffer), (
            'Detector input window size must be smaller than data buffer size'
        )

        self.target_lowcut = target_lowcut
        self.target_highcut = target_highcut
        assert self.target_lowcut < self.target_highcut, (
            'Filter lowcut must be smaller than filter highcut'
        )

        self.fs_filter = fs_filter
        
        # For issuing stimulation command to trodes
        self.trodes_hardware = trodes_hardware
        self.statescript_fxn_num = statescript_fxn_num
    
        # For stim_ok and phase estimation
        self.target_phase = target_phase
        assert self.target_phase >= 0 and self.target_phase <= 2*np.pi, (
            'Target phase must be within [0, 2pi]'
        )

        self.curr_phase = None
        self.prev_phase = None
        self.stim_ok = True

        b, a = butter(
            fltr_order, 
            np.array([target_lowcut, target_highcut]) / (fs_filter / 2), 
            btype='bandpass'
        )
        self.IIR_denominator = a
        self.IIR_numerator = b

    def echt_update_curr_phase(self):
        curr_analytic = echt(
            list(self.data_buffer)[-self.window_size:], 
            self.IIR_numerator, 
            self.IIR_denominator, 
            self.fs_filter
        )
        self.prev_phase = self.curr_phase
        self.curr_phase = np.angle(curr_analytic)[0] + np.pi

    def update_stim_ok(self):
        # Flip stim_ok to True at troughs
        try:
            if (self.prev_phase - self.curr_phase) > np.pi:
                self.stim_ok = True

        except TypeError:
            pass

    def closed_loop_stim(self):
        while True:
            self.echt_update_curr_phase()
            self.update_stim_ok()

            try:
                if self.curr_phase >= self.target_phase and self.stim_ok:
                    print(f'{self.name} STIM at phase {self.curr_phase}')
                    call_statescript(
                        self.trodes_hardware, 
                        self.statescript_fxn_num
                    )
                    self.stim_ok = False
            except TypeError:
                # curr_phase is None initially
                pass

