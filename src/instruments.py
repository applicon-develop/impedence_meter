#
# Questo modulo contiene le funzioni per controllare, attraverso il protocollo NI-VISA
# il generatore di segnale e l'oscilloscopio
# #

import pyvisa as pv
import sys
import struct

##########################################################################
# VARIABILI GLOBALI
##########################################################################

rm = pv.ResourceManager()

NUMBER_OF_TIME_DIVISIONS = 10 # numero di divisioni dell'oscilloscopio sull'asse dei tempi

#
# Si connette allo strumento con l'indirizzo VISA specificato, se esiste
# #
def open_resource(visa_address):
    if visa_address not in rm.list_resources():
        print(f"Strumento con indirizzo {visa_address} non trovato")
        sys.exit(1)
    return rm.open_resource(visa_address)

#
# Controlla se il comando effettuato non abbia lasciato lo strumento 
# in uno stato di errore
# #
def check_instrument_error(instrument, command):
    error_string = instrument.query(":SYSTem:ERRor?")
        
    if error_string: # se viene restituita una stringa
        if error_string.find("+0", 0, 3) == -1: # Non è un "No error"
            print(f"ERROR: {error_string}, command: {command}")
            sys.exit(1)
    else: # poiché la query restituisce sempre una stringa, se non lo ha fatto c'è un errore
        print(f"ERROR: :SYSTem:ERRor? non ha restituito niente, comando: {command}")
        sys.exit(1)
    
#
# Esegue il comando specificato in formato ASCII ed effettua il controllo errori
# #
def do_command(instrument, command, hide_params = False):
    if hide_params: # nascondi i parametri quando fai il check
        (header, data) = command.split(" ", 1)
    instrument.write(command)
    if hide_params:
        check_instrument_error(instrument, header)
    else:
        check_instrument_error(instrument, command)

#
# Esegue il comando specificato in formato binario ed effettua il controllo errori
# #
def do_command_binary(instrument, command, values):
    instrument.write_binary_values(f"{command}", values, datatype='B')
    check_instrument_error(instrument, command)

#
# Invia la query specificata in formato ASCII  
# ed effettua il controllo errori
# #
def do_query_string(instrument, query):
    res = instrument.query(f"{query}")
    check_instrument_error(instrument, query)
    return res.strip()

#
# Invia la query specificata in formato binario  
# ed effettua il controllo errori
# #
def do_query_binary(instrument, query):
    res = instrument.query_binary_values(f"{query}", datatype='s', container=bytes)
    check_instrument_error(instrument, query)
    return res

#
# Inizializza lo strumento
# #
def initialize(instrument):
     # identificativo del dispositivo
    idn = do_query_string(instrument, "*IDN?")
    print(f"Identificativo dello strumento: {idn}")
    
    do_command(instrument, "*CLS")
    do_command(instrument, "*RST")
    
#
# Invia al generatore il comando per generare un segnale di corrente alternata sinusoidale
# #
def generate_sine_wave(generator, source = 1, amplitude = 1, frequency = 100):
    do_command(generator, f":SOURce{source}:FUNC SIN")
    do_command(generator, f":SOURce{source}:FREQ {frequency}")
    do_command(generator, f":SOURce{source}:VOLT {amplitude}")
    
    # abilita il canale d'uscita
    do_command(generator, f"OUTP{source} ON")
    
    print(f"SRC{source}: {frequency} Hz sine wave, {amplitude}Vpp") #NOTE Vpp indica la differenza tra i due picchi (positivo e negativo)

#
# Esegue la cattura della forma d'onda sul canale specificato
# salvando i dati nella coda di output dell'oscilloscopio
#
# Viene preso un campione del segnale che dura time_interval secondi
# (10^-2 di default)
# #
def capture(oscilloscope, channel = 1, time_interval = 1e-2):
    # scaling degli assi x e y, automatico
    do_command(oscilloscope, ":AUToscale")
    # scaling dell'asse x in base a quanto specificato
    do_command(oscilloscope, f':TIMebase:SCALe {time_interval / NUMBER_OF_TIME_DIVISIONS}')
    
    # impostazioni del trigger per misurare il segnale
    do_command(oscilloscope, ":TRIGger:MODE EDGE")
    do_command(oscilloscope, ":TRIGger:EDGE:LEVel 1.5")
    do_command(oscilloscope, ":TRIGger:EDGE:SLOpe POSitive")
    do_command(oscilloscope, f":TRIGger:EDGE:SOURce CHAN{channel}") # imposta il trigger sul canale specificato
    
    # acquisizione del segnale
    do_command(oscilloscope, ":ACQuire:TYPE NORMal")
    do_command(oscilloscope, f":DIGitize CHAN{channel}")

#
# Restituisce la misura dell'ampiezza resgistrata sul canale specificato
# #
def measure_amplitude(oscilloscope, channel = 1):
    do_command(oscilloscope, f":MEASure:SOURce CHAN{channel}")
    do_command(oscilloscope, ":MEASure:VAMPlitude")
    amplitude = do_query_string(oscilloscope, ":MEASure:VAMPlitude?")
    
    return amplitude

#
# Restituisce la misura della frequenza registrata sul canale specificato
# #
def measure_frequency(oscilloscope, channel = 1):
    do_command(oscilloscope, f":MEASure:SOURce CHAN{channel}")
    do_command(oscilloscope, ":MEASure:FREQuency")
    frequency = do_query_string(oscilloscope, ":MEASure:FREQuency?")
    
    return frequency    

#
# Restituisce la misura dello sfasamento registrata tra i due canali specificati.
# La misura viene eseguita dall'oscilloscopio e viene calcolata come:
#   phase = (delay / period of input 1) x 360
# dove delay è il ritardo tra i trigger delle due forme d'onda
# 
# ref: Programmer's Guide for InfiniiVision 2000 X-Series Oscilloscopes
# #
def measure_phase(oscilloscope, channel1 = 1, channel2 = 2):
    do_command(oscilloscope, ":ACQuire:TYPE NORMal")
    do_command(oscilloscope, f":DIGitize CHAN{channel1}, CHAN{channel2}")
    do_command(oscilloscope, f":MEASure:SOURce CHAN{channel1}, CHAN{channel2}")
    do_command(oscilloscope, f":MEASure:PHASe CHAN{channel1}, CHAN{channel2}")
    phase = do_query_string(oscilloscope, f":MEASure:PHASe? CHAN{channel1}, CHAN{channel2}")
    
    return phase

#
# Restituisce le misurazioni di ampiezza, fase e frequenza registrata
# sui canali specificati e relative alla frequenza in ingresso specificata.
# In assenza di rumore la frequenza registrata dovrebbe coincidere con quella specificata.
# Le ampiezze vengono prese singolarmente sui singoli canali mentre la fase viene calcolata
# come sfasamento tra le due forme d'onda registrate nei due canali.
# #
def exec_measurements(oscilloscope, frequency, channel1 = 1, channel2 = 2):
    
    a1 = measure_amplitude(oscilloscope, channel1)
    f1 = measure_frequency(oscilloscope, channel1)
    a2 = measure_amplitude(oscilloscope, channel2)
    f2 = measure_amplitude(oscilloscope, channel2)
    ph = measure_phase(oscilloscope, channel1, channel2)
    
    return {
        'expected_frequency': frequency,
        f'amplitude{channel1}': a1,
        f'frequency{channel1}': f1,
        f'amplitude{channel2}': a2,
        f'frequency{channel2}': f2,
        'phase': ph
    }
    
#
# Campiona la forma d'onda sul canale specificato per un intervallo 
# di tempo di ampiezza specificata (10^-2 di default) alla frequenza 
# di campionamento specificata (10^6 di default)
# #
def obtain_waveform(oscilloscope, channel, sampling_frequence = 1e6, time_interval = 1e-2):
    # ricatturo la forma d'onda per l'intervallo specificato
    capture(oscilloscope, channel, time_interval)
    
    # il numero di punti da prendere, ovvero il numero di campioni del segnale
    # sarà pari alla frequenza di campionamento moltiplicati i secondi
    # con cui è stata scalata l'asse dei tempi
    points_number = sampling_frequence * time_interval
    
    # preparazione all'acquisizione
    do_command(oscilloscope, f":WAVeform:SOURce CHAN{channel}")
    do_command(oscilloscope, ":WAVeform:POINts:MODE RAW")
    do_command(oscilloscope, f":WAVeform:POINts {points_number}")
    do_command(oscilloscope, ":WAVeform:FORMat BYTE")
    
    # preambolo
    WAVE_FORMATS = {
        0 : "BYTE",
        1 : "WORD",
        4 : "ASCii"
    }
    
    ACQUISITION_TYPES = {
        0 : "NORMal",
        1 : "PEAK",
        2 : "AVERange",
        3 : "HRESolution"
    }
    
    (
        wave_format, 
        acquisition_type,
        wave_points,
        avg_count,
        x_increment,
        x_origin,
        x_reference,
        y_increment,
        y_origin,
        y_reference
    ) = (oscilloscope.query(":WAVeform:PREamble?")).split(',')
    
    # valori numerici
    x_increment = float(oscilloscope.query(":WAVeform:XINCrement?"))
    x_origin = float(oscilloscope.query(":WAVeform:XORigin?"))
    y_increment = float(oscilloscope.query(":WAVeform:YINCrement?"))
    y_origin = float(oscilloscope.query(":WAVeform:YORigin?"))
    y_reference = float(oscilloscope.query(":WAVeform:YREFerence?"))
    
    # dati dell forma d'onda
    data_bytes = oscilloscope.query_binary_values(
        ":WAVeform:DATA?", 
        datatype = 's',
        container = bytes
    )
    data_bytes_length = len(data_bytes)
    #print(f"Conteggio bytes: ${data_bytes_length}")
    block_points = data_bytes_length
    
    values = struct.unpack("%dB" % block_points, data_bytes)
    #print(f"Numero di valori collezionati: ${len(values)}")
    
    res = []
    for i in range(len(values) - 1):
        time = x_origin + (i * x_increment)
        voltage = ((values[i] - y_reference) * y_increment) + y_origin
        res.append((time, voltage))
    
    return res

    
# NOTE
# CH1 misura voltaggio sul primo capo dello shunt
# CH2 misura lvoltaggio sul secondo capo dello shunt
# #