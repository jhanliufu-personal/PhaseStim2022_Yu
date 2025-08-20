"""
Phase estimation methods for real-time phase detection
Written by Mengzhan Liufu at Yu Lab, the University of Chicago
"""

import numpy as np
from abc import ABC, abstractmethod
from scipy.signal import hilbert, sosfiltfilt, freqz


class PhaseEstimator(ABC):
    """Abstract base class for phase estimation methods"""
    
    @abstractmethod
    def estimate_phase(self, data_window, **kwargs):
        """Estimate phase from data window"""
        pass


class ECHTEstimator(PhaseEstimator):
    """Endpoint-Correcting Hilbert Transform phase estimator"""
    
    def __init__(self, numerator, denominator, fs):
        self.numerator = numerator
        self.denominator = denominator
        self.fs = fs
    
    def _echt(self, xr, b, a, Fs, n=None):
        """
        Endpoint-correcting hilbert transform
        
        Parameters
        ----------
        xr: array like, input signal
        b: numerators of IIR filter response
        a: denominator of IIR filter response
        Fs: signal sampling rate
        n: length parameter
        
        Returns
        -------
        analytic signal
        """
        # Check input
        if n is None:
            n = len(xr)
        if not all(np.isreal(xr)):
            xr = np.real(xr)

        # Compute FFT
        x = np.fft.fft(xr, n)

        # Set negative components to zero and multiply positive by 2 (apart from DC and Nyquist frequency)
        h = np.zeros(n, dtype=x.dtype)
        if n > 0 and 2 * (n // 2) == n:
            # even and non-empty
            h[[0, n // 2]] = 1
            h[1:n // 2] = 2
        elif n > 0:
            # odd and non-empty
            h[0] = 1
            h[1:(n + 1) // 2] = 2
        x = x * h

        # Compute filter's frequency response
        T = 1 / Fs * n
        filt_freq = np.ceil(np.arange(-n/2, n/2)) / T
        filt_coeff = freqz(b, a, worN=filt_freq, fs=Fs)

        # Multiply FFT by filter's response function
        x = np.fft.fftshift(x)
        x = x * filt_coeff[1]
        x = np.fft.ifftshift(x)

        # IFFT
        x = np.fft.ifft(x)
        return x
    
    def estimate_phase(self, data_window, **kwargs):
        """Estimate phase using ecHT method"""
        analytic_signal = self._echt(
            data_window, 
            self.numerator, 
            self.denominator, 
            self.fs
        )
        return np.angle(analytic_signal)[-1] + np.pi


class HTEstimator(PhaseEstimator):
    """Standard Hilbert Transform phase estimator"""
    
    def __init__(self, sos):
        self.sos = sos
    
    def estimate_phase(self, data_window, **kwargs):
        """Estimate phase using standard HT method"""
        filtered = sosfiltfilt(self.sos, data_window)
        analytic_signal = hilbert(filtered)
        return np.angle(analytic_signal)[-1] + np.pi


class PMEstimator(PhaseEstimator):
    """Phase Mapping estimator"""
    
    def __init__(self, sos, regr_buffer_size=50, num_to_wait=10, 
                 derv_bar=0.01, default_slope=0.012, gradient_factor=1,
                 reset_on=False, reset_threshold=250, lock_on=False, lockdown=50):
        self.sos = sos
        self.regr_buffer_size = regr_buffer_size
        self.num_to_wait = num_to_wait
        self.derv_bar = derv_bar
        self.default_slope = default_slope
        self.gradient_factor = gradient_factor
        self.reset_on = reset_on
        self.reset_threshold = reset_threshold
        self.lock_on = lock_on
        self.lockdown = lockdown
        
        # Initialize state variables
        self.A = self._generate_matrix(regr_buffer_size)
        self.sign_buffer = [True] * num_to_wait
        self.curr_sign = True
        self.sample_count = None
        self.slope = default_slope
        self.in_lock = 0
        self.prev_filtered_buffer = None
    
    def _generate_matrix(self, size):
        """
        Generate matrix for linear regression (linear algebra method)

        Parameters
        ----------
        size : int, size of matrix created for regression

        Returns
        -------
        A : 2-dimensional numpy array that represents matrix for linear regression
        """
        sampling_axis = np.arange(size)
        A = np.vstack([sampling_axis, np.ones(len(sampling_axis))]).T
        return A

    def _calculate_derivative(self, buffer):
        """
        Calculate derivative / linear regression with linear algebra

        Parameters
        ----------
        buffer : list or array of values for linear regression

        Returns
        -------
        float, derivative / slope of the regression line
        """
        curr_regr = buffer[:, np.newaxis]
        pinv = np.linalg.pinv(self.A)
        alpha = pinv.dot(curr_regr)
        return alpha[0][0]
    
    def _force_reset(self):
        """Check if force reset is needed"""
        if not self.reset_on or self.sample_count is None:
            return False
        return self.sample_count >= self.reset_threshold
    
    def estimate_phase(self, data_window, **kwargs):
        """Estimate phase using Phase Mapping method"""
        # Filter the data - maintain buffer for derivative calculation
        filtered = sosfiltfilt(self.sos, data_window)
        
        # Update filtered buffer for regression
        if self.prev_filtered_buffer is None:
            self.prev_filtered_buffer = filtered[-self.regr_buffer_size:]
        else:
            # Append new sample and maintain buffer size
            self.prev_filtered_buffer = np.concatenate([
                self.prev_filtered_buffer[1:], 
                [filtered[-1]]
            ])
        
        # Calculate derivative
        curr_derv = self._calculate_derivative(self.prev_filtered_buffer)
        
        # Update lock counter
        if self.in_lock > 0:
            self.in_lock -= 1
        
        # Extrapolate current phase
        if self.sample_count is not None:
            curr_phase = self.sample_count * self.slope
        else:
            curr_phase = 0
        
        # Update sign buffer
        self.sign_buffer.append(curr_derv > 0)
        self.sign_buffer.pop(0)
        
        # Increment sample count
        if self.sample_count is not None:
            self.sample_count += 1
        
        # Check for critical point/reset conditions
        if_flip = (self.curr_sign + sum(self.sign_buffer) / self.num_to_wait == 1 
                   and np.abs(curr_derv) >= self.derv_bar)
        if_force = self._force_reset()
        
        # Critical point / reset logic
        if (if_flip or if_force) and self.in_lock == 0:
            curr_phase = self.curr_sign * np.pi
            
            if self.sample_count is not None:
                if self.curr_sign:
                    self.slope = (2 - self.curr_sign) * np.pi / self.sample_count
                else:
                    self.slope = (2 - self.curr_sign) * np.pi / (self.sample_count / self.gradient_factor)
                    self.in_lock = self.lockdown * self.lock_on
                
                self.sample_count = self.curr_sign * int(np.pi / self.slope)
            else:
                self.sample_count = self.curr_sign * int(np.pi / self.slope)
            
            self.curr_sign = not self.curr_sign
            self.sign_buffer = [self.curr_sign] * self.num_to_wait
        
        # Convert from [0, 2π] to [-π, π] range to match other methods
        return curr_phase % (2 * np.pi) - np.pi if curr_phase is not None else 0