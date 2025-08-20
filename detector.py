'''
Written by Mengzhan Liufu at Yu Lab, the University of Chicago
'''
from scipy.signal import butter, cheby1, ellip
import numpy as np
from trodes_connection import call_statescript
from phase_estimators import ECHTEstimator, HTEstimator, PMEstimator


class Detector:

    def __init__(
        self,
        detector_name: str,
        data_buffer,
        statescript_fxn_num: int,
        trodes_hardware,
        method: str = 'ecHT',
        window_size = 400,
        target_phase = np.pi,
        target_lowcut = 6,
        target_highcut = 9,
        fs_filter = 1500,
        fltr_order = 2,
        filter_type = 'butter',
        # PM-specific parameters
        regr_buffer_size = 50,
        num_to_wait = 10,
        derv_bar = 0.01,
        default_slope = 0.012,
        gradient_factor = 1,
        reset_on = False,
        reset_threshold = 250,
        lock_on = False,
        lockdown = 50,
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
        self.method = method.lower()
        
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

        # Initialize phase estimator based on method
        self._initialize_phase_estimator(
            method, filter_type, fltr_order, target_lowcut, target_highcut, 
            fs_filter, regr_buffer_size, num_to_wait, derv_bar, default_slope,
            gradient_factor, reset_on, reset_threshold, lock_on, lockdown
        )

    def _initialize_phase_estimator(self, method, filter_type, fltr_order, 
                                   target_lowcut, target_highcut, fs_filter,
                                   regr_buffer_size, num_to_wait, derv_bar, 
                                   default_slope, gradient_factor, reset_on, 
                                   reset_threshold, lock_on, lockdown):
        """Initialize the appropriate phase estimator based on method"""        
        # Define filter parameters
        Wn = np.array([target_lowcut, target_highcut]) / (fs_filter / 2)
        rp, rs = 1, 40
        
        if method.lower() == 'echt':
            # For ecHT, use IIR filter coefficients
            if filter_type == 'butter':
                b, a = butter(fltr_order, Wn, btype='bandpass')
            elif filter_type == 'cheby1':
                b, a = cheby1(fltr_order, rp, Wn, btype='bandpass')
            elif filter_type == 'ellip':
                b, a = ellip(fltr_order, rp, rs, Wn, btype='bandpass')
            else:
                raise ValueError(f"Unknown filter type: {filter_type}")
            
            self.phase_estimator = ECHTEstimator(b, a, fs_filter)
            
        elif method.lower() in ['ht', 'hilbert']:
            # For HT, use SOS filter
            if filter_type == 'butter':
                sos = butter(fltr_order, Wn, btype='bandpass', output='sos')
            elif filter_type == 'cheby1':
                sos = cheby1(fltr_order, rp, Wn, btype='bandpass', output='sos')
            elif filter_type == 'ellip':
                sos = ellip(fltr_order, rp, rs, Wn, btype='bandpass', output='sos')
            else:
                raise ValueError(f"Unknown filter type: {filter_type}")
            
            self.phase_estimator = HTEstimator(sos)
            
        elif method.lower() == 'pm':
            # For PM, use SOS filter
            if filter_type == 'butter':
                sos = butter(fltr_order, Wn, btype='bandpass', output='sos')
            elif filter_type == 'cheby1':
                sos = cheby1(fltr_order, rp, Wn, btype='bandpass', output='sos')
            elif filter_type == 'ellip':
                sos = ellip(fltr_order, rp, rs, Wn, btype='bandpass', output='sos')
            else:
                raise ValueError(f"Unknown filter type: {filter_type}")
            
            self.phase_estimator = PMEstimator(
                sos, regr_buffer_size, num_to_wait, derv_bar, default_slope,
                gradient_factor, reset_on, reset_threshold, lock_on, lockdown
            )
        else:
            raise ValueError(f"Unknown phase estimation method: {method}")

    def update_curr_phase(self):
        """Update current phase using the selected phase estimation method"""
        data_window = list(self.data_buffer)[-self.window_size:]
        self.prev_phase = self.curr_phase
        self.curr_phase = self.phase_estimator.estimate_phase(data_window)

    def update_stim_ok(self):
        """Update stimulation readiness based on phase crossing detection"""
        try:
            # For PM method, stim_ok is handled internally by the estimator
            if self.method == 'pm':
                # PM method resets stim_ok at phase = 0 (trough)
                if hasattr(self.phase_estimator, 'curr_sign') and not self.phase_estimator.curr_sign:
                    self.stim_ok = True
            else:
                # For ecHT and HT methods, reset stim_ok at phase wrapping (troughs)
                if (self.prev_phase - self.curr_phase) > np.pi:
                    self.stim_ok = True
        except (TypeError, AttributeError):
            pass

    def closed_loop_stim(self):
        """Main loop for closed-loop phase-locked stimulation"""
        while True:
            self.update_curr_phase()
            self.update_stim_ok()

            try:
                if self.curr_phase >= self.target_phase and self.stim_ok:
                    print(f'{self.name} STIM at phase {self.curr_phase:.3f} using {self.method.upper()}')
                    call_statescript(
                        self.trodes_hardware, 
                        self.statescript_fxn_num
                    )
                    self.stim_ok = False
            except TypeError:
                # curr_phase is None initially
                pass

