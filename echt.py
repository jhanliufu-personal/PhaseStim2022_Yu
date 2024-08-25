import numpy as np
from scipy.signal import freqz

def echt(xr, b, a, Fs, n=None):
    """
    endpoint-correcting hilbert transform

    Parameters
    ----------
    xr: array like, input signal
    b: numerators of IIR filter response
    a: denominator of IIR filter response
    Fs: signal sampling rate
    n

    Returns
    -------
    analytic signal

    """
    # Check input
    if n is None:
        # default: n is length of xr
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