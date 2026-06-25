#
# Questo modulo esegue le misure sul circuito tramite sweep di frequenze
# #

import sys
from pathlib import Path

main_dir = Path(__file__).resolve().parent
if str(main_dir) not in sys.path:
    sys.path.insert(0, str(main_dir))

import instruments as ins
import os
import json
import csv
import scipy.io as sio

###########################################################################
#   VARIABILI GLOBALI
###########################################################################

SUPPORTED_FORMATS = ['csv', 'json', 'mat']

class SweepMeasure:
    """
        Questa classe gestisce l'esecuzione delle misure tramite sweep di frequenze utilizzando un generatore di segnale
        e un oscilloscopio. Dell'oscilloscopio `oscilloscope` si utilizzano due sonde, corrispondenti ai canali `oscilloscope_channel1` e 
        `oscilloscope_channel2`, mentre del generatore si utilizza la sorgente `generator_source`. La misura avviene 
        inviando al circuito da testare un segnale di ampiezza `signal_amplitude` con il generatore `generator` 
        e di esegurie le misure di ampiezza sui due canali dell'oscilloscopio, nonché lo sfasamento tra le due forme d'onda misurate.
        Vengono inoltre salvati i punti delle forme d'onda ricavate. Lo sweep di frequenze è specificato dagli attributi 
        `starting_frequence`, `stopping_frequence` e `step_frequence`. Una volta eseguita la misura, salva i valori di ampiezza
        registrati dai due canali e il loro sfasamento in maniera persistente e in formato json nel file `measurements_file_path`, 
        se `save_measurements` è uguale a True e salva i dati dei punti delle forme d'onda registrate in maniera persistente e in
        formato json nella cartella `measurements_file_path`, se `save_points_data` è uguale a True. In quest'ultimo caso, 
        i dati dei punti delle forme d'onda vengono divisi per la loro frequenza.
        
        Attributes
        ----------
        `oscilloscope`: pyvisa.Resource 
            controller dell'oscilloscopio
        `generator`: pyvisa.Resource 
            controller del generatore di segnale
        `generator_source`: int
            identificativo della sorgente del segnale del generatore
        `oscilloscope_channel1`: int
            identificativo del canale dell'oscilloscopio corrispondende alla sonda posta sul nodo tra il generatore e il carico
        `oscilloscope_channel2`: int
            identificativo del canale dell'oscilloscopio corrispondende alla sonda posta sul nodo tra il carico e la resistenza di Shunt
        `starting_frequence`: int
            frequenza iniziale dello sweep di frequenze
        `stopping_frequence`: int
            frequenza finale dello sweep di frequenze
        `step_frequence`: int 
            passo dello sweep di frequenze
        `signal_amplitude`: double
            ampiezza del segnale generato
        `time_interval`: int
            durata (in secondi) dell'intervallo di tempo della forma d'onda da campionare
        `sampling frequence`: int
            frequenza di campionamento della forma d'onda
        `shunt_resistance`: double
            valore della resistenza di Shunt utilizzata
        `points_data_base_path`: str
            indirizzo della cartella in cui memorizzare in maniera persistente i dati dei punti delle forme d'onda
        `points_data_format`: str
            specifica il formato in cui vanno memorizzati in maniera persistente i dati delle forme d'onda. I valori possibili sono:
                > `'mat'`  -> matlab variable file
                > `'csv'`  -> csv file
                > `'json'` -> json file
                > `'none'` -> non salva i dati
        `measurements_file_path`: str
            percorso del file in cui memorizzare in maniera persistente le misure registrate sui canali dell'oscilloscopio. Il formato
            dei dati viene ricavato dal percorso specificato. I possibili formati sono:
                > `'mat'`  -> matlab variable file
                > `'csv'`  -> csv file
                > `'json'` -> json file
                > `'none'` -> non salva i dati
        `impedence_data_file_path`: str
            percorso del file in cui memorizzare in maniera persistente i dati di ampiezza e fase ricavati. Il formato
            dei dati viene ricavato dal percorso specificato. I possibili formati sono:
                > `'mat'`  -> matlab variable file
                > `'csv'`  -> csv file
                > `'json'` -> json file
                > `'none'` -> non salva i dati
    """
    
    def __init__(self):
        self.oscilloscope = None
        self.generator = None
        
        self.generator_source = -1
        self.oscilloscope_channel1 = -1
        self.oscilloscope_channel2 = -1
        
        self.starting_frequence = None
        self.stopping_frequence = None
        self.step_frequence = None
        
        self.signal_amplitude = None
        self.time_interval = 1e-2
        self.sampling_frequence = 1e6
        self.epsilon = 1e-4
        self.shunt_resistance = None
        
        self.points_data_base_path = ''
        self.points_data_format = 'none'
        self.measurements_file_path = ''
        self.impedence_data_file_path = ''
        
        # Formato dei dati
        self.impedence_data_format = 'none'
        self.measurements_data_format = 'none'
        
    def set_oscilloscope(self, oscilloscope):
        self.oscilloscope = oscilloscope
        
    def set_generator(self, generator):
        self.generator = generator
    
    def set_generator_source(self, generator_source):
        self.generator_source = generator_source
        
    def set_oscilloscope_channel1(self, oscilloscope_channel1):
        self.oscilloscope_channel1 = oscilloscope_channel1
        
    def set_oscilloscope_channel2(self, oscilloscope_channel2):
        self.oscilloscope_channel2 = oscilloscope_channel2
        
    def set_sweep_range(self, starting_frequence, stopping_frequence, step_frequence):
        if(stopping_frequence < starting_frequence):
            raise RuntimeError('ERROR: la frequenza iniziale deve essere più piccola di quella finale')
        
        self.starting_frequence = starting_frequence
        self.stopping_frequence = stopping_frequence
        self.step_frequence = step_frequence
        
    def set_signal_amplitude(self, signal_amplitude):
        if signal_amplitude == 0: raise RuntimeError('ERROR: l\'ampiezza del segnale da generare per eseguire la misura non può essere nulla')
        self.signal_amplitude = abs(signal_amplitude)
    
    #
    # Abilita il salvataggio dei dati dei punti delle forme d'onda lette dall'oscilloscopio e imposta il
    # percorso della cartella destinazione specificato. Se questo è None o vuoto non abilita il salvataggio ma non informa l'utente.
    # #
    def enable_point_data_saving(self, points_data_base_path, points_data_format):
        if points_data_format == 'none': return
        
        if points_data_base_path: # se non è '' o None
            if not self.FileHelper.is_supported(points_data_format):
                raise RuntimeError(f'ERROR il formato {points_data_base_path} specificato per salvare i dati delle forme d\'onda non è supoortato')
            
            self.points_data_base_path = points_data_base_path
            self.points_data_format = points_data_format
    
    #
    # Abilita il salvataggio dei dati delle misure di ampiezza e fase effettuate dall'oscilloscopio e imposta il
    # percorso del file destinazione specificato. Se questo è None o vuoto non abilita il salvataggio ma non informa l'utente.
    # #
    def enable_measurements_saving(self, measurements_file_path):
        if measurements_file_path: # se non è '' o None
            if not self.FileHelper.check_file_data_format(measurements_file_path):
                raise RuntimeError(f'ERROR: l\'estensione del percorso {measurements_file_path} specificato per salvare i dati delle misure non è supportata')
            
            self.measurements_file_path = measurements_file_path
            self.measurements_data_format = self.FileHelper.retrieve_file_format(measurements_file_path)
    
    #
    # Abilita il salvataggio dei dati delle misure di ampiezza e fase dell'impedenza data dal carico
    # ricavate e imposta il percorso del file destinazione specificato. 
    # Se questo è None o vuoto non abilita il salvataggio ma non informa l'utente.
    # #      
    def enable_impedence_data_saving(self, impedence_data_file_path):
        if impedence_data_file_path: # se non è '' o None
            if not self.FileHelper.check_file_data_format(impedence_data_file_path):
                raise RuntimeError(f'ERROR: l\'estensione del percorso {impedence_data_file_path} specificato per salvare i dati di ampiezza e fase dell\'impedenza non è supportata')
            
            self.impedence_data_file_path = impedence_data_file_path
            self.impedence_data_format = self.FileHelper.retrieve_file_format(impedence_data_file_path)
        
    def set_sampling_frequence(self, sampling_frequence):
        if sampling_frequence <= 0: raise RuntimeError('ERROR: la frequenza di campionamento deve essere positiva')
        
        self.sampling_frequence = sampling_frequence
        self.epsilon = 1 / (self.sampling_frequence * self.time_interval)
    
    def set_time_interval(self, time_interval):
        if time_interval <= 0: raise RuntimeError('ERROR: la durata dell\'intervallo di tempo della forma d\'onda da campionare deve essere positivo')
        
        self.time_interval = time_interval
        self.epsilon = 1 / (self.sampling_frequence * self.time_interval)
            
    def set_shunt_resistance(self, shunt_resistance):
        if shunt_resistance <= 0: raise RuntimeError('ERROR: il valore della resistenza di Shunt deve essere positivo')
        
        self.shunt_resistance = shunt_resistance
    
    def check_status(self):
        return (self.oscilloscope != None
                and self.generator != None
                and self.generator_source != -1
                and self.oscilloscope_channel1 != -1
                and self.oscilloscope_channel2 != -1
                and self.starting_frequence != None
                and self.stopping_frequence != None
                and self.step_frequence != None
                and self.signal_amplitude != None
                and self.shunt_resistance != None) 
    
    def save_measurements(self, measurements):
        self.FileHelper.create_dir(self.measurements_file_path)
        self.FileHelper.save_data(self.measurements_file_path, measurements)
    
    def save_points_data(self, ch1_waveform, ch2_waveform, frequence):
        points = []
        for i in range(len(ch1_waveform)):
            x1, y1 = ch1_waveform[i]
            x2, y2 = ch2_waveform[i]
            
            points.append({
                f'x{self.oscilloscope_channel1}': x1,
                f'x{self.oscilloscope_channel2}': x2,
                f'y{self.oscilloscope_channel1}': y1,
                f'y{self.oscilloscope_channel2}': y2
            })
        
        file_path = f'{self.points_data_base_path}freq{frequence}Hz.{self.points_data_format}'
        self.FileHelper.create_dir(file_path)
        self.FileHelper.save_data(file_path, points)
    
    #
    # Esegue la misura specificata dallo stato dell'oggetto e restituisce le 
    # frequenze dello sweep specificato, le misure della caduta di tensione sul carico 
    # e le forme d'onda delle due tensioni ai capi del carico rispetto alle frequenze stesse. 
    # Se necessario, salva i dati sulle misure e sulle forme d'onda in modo permanente
    # #
    def exec(self):
        # verifica che i parametri non opzionali non siano impostati al valore di default    
        if not self.check_status():
            raise RuntimeError(f'ERROR: impossibile eseguire la misura a causa di un errore nella specifica dei parametri\nParametri specificati: {self.to_string()}')
        
        # inizializza gli strumenti
        ins.initialize(self.oscilloscope)
        ins.initialize(self.generator)
        
        # incertezza sull'istante di campionamento della forma d'onda
        self.epsilon = 1 / (self.sampling_frequence * self.time_interval)
        
        # caratteristiche della forma d'onda del potenziale sul carico
        load_voltage_measurements = []
        
        # forme d'onda sui due canali
        ch1_waveforms = []
        ch2_waveforms = []
        
        # frequenze dello sweep
        frequencies = []

        for freq in range(self.starting_frequence, self.stopping_frequence + self.step_frequence, self.step_frequence):
            # genera la forma d'onda
            ins.generate_sine_wave(self.generator, self.generator_source, self.signal_amplitude, freq)

            # esegui le misure
            load_volt_meas = ins.exec_measurements(self.oscilloscope, freq, self.oscilloscope_channel1, self.oscilloscope_channel2)
            ch1_wave = ins.obtain_waveform(self.oscilloscope, self.oscilloscope_channel1)
            ch2_wave = ins.obtain_waveform(self.oscilloscope, self.oscilloscope_channel2)
            
            # controllo sulla consistenza delle forme d'onda
            for i in range(len(ch1_wave)):
                (x1, _) = ch1_wave[i]
                (x2, _) = ch2_wave[i]
                if(abs(x1 - x2) > self.epsilon):
                    print(f'ERRORE: i due tempi non coincidono x{self.oscilloscope_channel1}:{x1}; x{self.oscilloscope_channel2}:{x2}')
                    sys.exit(1)

            # carica le misure nelle strutture dati
            frequencies.append(freq)
            load_voltage_measurements.append(load_volt_meas)
            ch1_waveforms.append(ch1_wave)
            ch2_waveforms.append(ch2_wave)
            
            # se necessario, salva in maniera permanente le forme d'onda
            if self.points_data_base_path != '':
                self.save_points_data(ch1_wave, ch2_wave, freq)
        
        # se necessario, salva in maniera permanente le misure
        if self.measurements_file_path != '':
            self.save_measurements(load_voltage_measurements)
                
        #se necessario, crea il percorso dove salvare il file dell'impedenza
        if self.impedence_data_file_path != '':
            self.FileHelper.create_dir(self.impedence_data_file_path)    
        
        return frequencies, load_voltage_measurements, ch1_waveforms, ch2_waveforms
    
    def to_string(self):
        return (f'Sweep Measure:\n' 
                + f'oscilloscope: {self.oscilloscope}\n' 
                + f'generator: {self.generator}\n'
                + f'generator source: {self.generator_source}\n'
                + f'channel 1: {self.oscilloscope_channel1}\n'
                + f'channel 2: {self.oscilloscope_channel2}\n'
                + f'sweep: {self.starting_frequence}:{self.stopping_frequence}:{self.step_frequence}\n'
                + f'signal amplitude: {self.signal_amplitude}\n'
                + f'time interval: {self.time_interval}\n'
                + f'sampling frequence: {self.sampling_frequence}\n'
                + f'shunt resistance: {self.shunt_resistance}\n'
                + f'points data base path: {self.points_data_base_path}\n'
                + f'measure file path: {self.measurements_file_path}\n'
                + f'impedence data file path: {self.impedence_data_file_path}\n'
                + f'points data format: {self.points_data_format}\n'
                + f'measure data format: {self.measurements_data_format}\n'
                + f'impedence data format: {self.impedence_data_format}\n')
        
    # INNER CLASS
    class FileHelper:
        def __init__(self):
            pass
        
        @classmethod
        def retrieve_file_name(cls, file_path):
            return file_path.split('\\/')[-1]
        
        @classmethod
        def retrieve_file_format(cls, file_path):
            return file_path.split('.')[1]
            
        @classmethod
        def check_file_data_format(cls, file_path):
            return cls.retrieve_file_format(file_path) in SUPPORTED_FORMATS
        
        @classmethod
        def is_supported(cls, data_format):
            return data_format in SUPPORTED_FORMATS
        
        @classmethod
        def save_data(cls, file_path, data):
            file_format = file_path.split('.')[1]

            if file_format == 'csv':
                with open(file_path, 'w') as f:
                    fieldnames = list(data[0].keys())
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(data)
            elif file_format == 'json':
                with open(file_path, 'w+') as f:
                    json.dump(data, f)
            elif file_format == 'mat':
                struct = {key: [data_item[key] for data_item in data] for key in data[0].keys()}     
                sio.savemat(file_path, struct)
            else:
                raise RuntimeError(f'ERROR: il percorso {file_path} ha un estensione non supportata')
            
        @classmethod
        def create_dir(cls, file_path):
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)