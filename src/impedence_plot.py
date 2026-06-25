import sys
from pathlib import Path

main_dir = Path(__file__).resolve().parent
if str(main_dir) not in sys.path:
    sys.path.insert(0, str(main_dir))

import numpy as np
import matplotlib.pyplot as plt
import signals
import json
import csv
import scipy.io as sio
from src.sweep import SweepMeasure

#
# Restituisce un vettore che contiene le ampiezze dell'impedenza data dal carico calcolate
# a partire dai fasori di tensione del generatore e della caduta di potenziale ai capi della
# resistenza di Shunt. Questi fasori sono stati ottenuti, per ognuna delle frequenze
# specificate, tramite FFT delle forme d'onda specificate
# #
def get_impedence_amplitudes(frequencies, vg_waveforms, vs_waveforms, shunt_resistance):
    impedence_amplitudes = []
    
    for i in range(len(frequencies)):
        vg = [point[1] for point in vg_waveforms[i]] # tensione del generatore
        vs = [point[1] for point in vs_waveforms[i]] # caduta di potenziale sullo shunt
        
        # ricavo ampiezza e fase della caduta di potenziale sul generatore e sullo shunts
        V_g, theta_g, _ = signals.get_peak_phasor(vg, num = 10000, deg = True)
        V_s, theta_s, _ = signals.get_peak_phasor(vs, num = 10000, deg = True)

        # calcolo la tensione di carico
        V_l_real = V_g * np.cos(theta_g) - V_s * np.cos(theta_s)
        V_l_imag = V_g * np.sin(theta_g) - V_s * np.sin(theta_s)
        V_l = np.sqrt((V_l_real * V_l_real) + (V_l_imag * V_l_imag))

        # calcolo la corrente
        current_ampl = V_s / shunt_resistance # la corrente è data dalla tensione fratto la resistenza
        
        # calcolo l'ampiezza dell'impedenza
        impedence_amplitudes.append(V_l / current_ampl)
        
    return impedence_amplitudes

#
# Restituisce un vettore che contiene le fasi dell'impedenza data dal carico misurate
# direttamente dall'oscilloscopio e contenute nel vettore di misure specificato
# Questo metodo scarta inoltre i valori di fase non misurati correttamente dall'oscilloscopio.
# #
def get_impedence_phases(measurements, frequencies):
    phases = []
    freqs = []
    for i in range(len(measurements)):
        phase = float(measurements[i]['phase'])
        if abs(phase) <= 360:
            phases.append(phase)
            freqs.append(frequencies[i])
        else: print(f'WARNING: fase non misurata per la frequenza {frequencies[i]}')
    return phases, freqs

#
# Effettua il salvataggio dei dati nel file specificato
# 
def save_impedence_data(frequencies, amplitudes, phases, data_file_path):
    data_format = data_file_path.split('.')[1]
    
    if data_format == 'json':
        data = [{
            'frequence': frequencies[i],
            'amplitude': amplitudes[i],
            'phase': phases[i] 
        } for i in range(len(frequencies))]

        with open(data_file_path) as file:
            json.dump(data, file)
    elif data_format == 'csv':
        data = [{
            'frequence': frequencies[i],
            'amplitude': amplitudes[i],
            'phase': phases[i] 
        } for i in range(len(frequencies))]
        
        with open(data_file_path, 'w') as f:
            fieldnames = list(data[0].keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
    elif data_format == 'mat':
        mat_data = {'frequencies': frequencies,
         'amplitudes': amplitudes,
         'phases': phases}
        sio.savemat(data_file_path, mat_data)
    else:
        raise RuntimeError(f'ERROR: formato specificato {data_format} non supportato.')

#
# Calcola e mostra il grafico ampiezza-fase dell'impedenza data dal carico e, se necessario,
# avvia la routine di salvataggio dei dati nel formato specificato dall'utente
# #
def impedence_applt(frequencies, measurements, ch1_waveforms, ch2_waveforms, sweep: SweepMeasure):
    amplitudes = get_impedence_amplitudes(frequencies, ch1_waveforms, ch2_waveforms, sweep.shunt_resistance)
    phases, frequencies_2 = get_impedence_phases(measurements, frequencies)
    
    if sweep.impedence_data_format != 'none':
        save_impedence_data(frequencies, amplitudes, phases, sweep.impedence_data_file_path)
            
    fig, ax = plt.subplots(2)
    ax[0].set_title('Impedence magnitude')
    ax[0].plot(frequencies, amplitudes)
    ax[0].set_xlabel('Frequence [Hz]')
    ax[0].set_ylabel('Impedence [Ohm]')
    ax[0].grid()
    
    ax[1].set_title('Impedence phase')
    ax[1].plot(frequencies_2, phases)
    ax[1].set_xlabel('Frequence [Hz]')
    ax[1].set_ylabel('Phase [deg]')
    ax[1].set_yticks([-90, -45, 0, 45, 90]) 
    ax[1].grid()
    plt.show()