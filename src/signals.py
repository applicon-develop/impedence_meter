import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import fft, fftfreq

#
# Esegue un filtro media mobile sul segnale specificato
# #
def moving_average(signal, time, window_size = 5):
    res_signal = []
    res_time = []
    filter = [signal[i] for i in range(window_size)]

    for i in range(len(signal)):
        res_signal.append(sum(filter) / window_size)
        res_time.append(time[i])
        
        for j in range(window_size - 1):
            filter[j] = filter[j + 1]

        filter[-1] = signal[i]

    return res_signal, res_time

#
# Calcola la FFT a num punti del segnale e restituisce 
# ampiezza, fase e l'intervallo di frequenze 
# #
def compute_fft(signal, num = 1000, deg = False):
    spectrum = fft(signal, num)
    frequencies = fftfreq(num)

    amplitudes = 2 * np.abs(spectrum) / len(signal) #np.sqrt(real * real + imag * imag)
    phases = np.angle(spectrum, deg)
    
    return amplitudes, phases, frequencies

#
# Mostra il grafico del segnale specificato
# #
def plot(signal, time):
    fig, ax = plt.subplots()
    ax.plot(time, signal)
    ax.set_xlabel('Tempo t[s]')
    
    plt.show()

#
# Mostra il grafico dello spettro in frequenza del segnale
# calcolato tramite una FFT a num punti
# #
def plot_spectrum(signal, num = 1000):
    spectrum, _, frequencies = compute_fft(signal, num)
    
    fig, ax = plt.subplots()
    ax.plot(frequencies, spectrum)
    ax.set_title('Spettro in frequenza')
    ax.set_xlabel('Frequenza f[Hz]')
    ax.set_ylabel('Ampiezza')
    
    plt.show()

#
# Mostra il grafico ampiezza-fase del segnale passato
# calcolato tramite una FFT a num punti
# #
def plot_amplitude_phase(signal, num = 1000, deg = False):
    amplitudes, phases, frequencies = compute_fft(signal, num, deg)
    
    fig, ax = plt.subplots(2)
    ax[0].plot(frequencies, amplitudes)
    ax[0].set_xlabel('Frequenza f[Hz]')
    ax[0].set_ylabel('Ampiezza')
    
    ax[1].plot(frequencies, phases)
    ax[1].set_xlabel('Frequenza f[Hz]')
    ax[1].set_ylabel('Fase')
    
    plt.show()

#
# Estrae il fasore associato alla componente dominante del segnale specificato
# nelle coordinate specificate ottenuta tramite una FFT a num punti.
# 
# Le coordinate possono essere:
#   - 'polar' ==> polari
#   - 'cartesian' ==> cartesiane o rettangolari
# #
def get_peak_phasor(signal, num = 1000, coords = 'polar', deg = False):
    amplitudes, phases, _ = compute_fft(signal, num, deg)
    
    # frequenza dominante
    freq = np.argmax(amplitudes)
    
    if coords == 'polar':
        ampl = amplitudes[freq]
        phase = phases[freq]
        
        return ampl, phase, freq
    
    if coords == 'cartesian':
        real = amplitudes[freq] * np.cos(phases[freq])
        imag = amplitudes[freq] * np.sin(phases[freq])
        
        return real, imag, freq
    
    print(f'ERROR: le coordinate specificate \'{coords}\' non sono valide')
    return None
