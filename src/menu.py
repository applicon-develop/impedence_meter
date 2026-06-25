#
# Questo modulo gestisce l'interfaccia con l'utente e dirigendo l'oggetto sweepMeasure
# aiuta a specificare tutti i parametri per eseguire la misurazione
# #

import sys
from pathlib import Path

main_dir = Path(__file__).resolve().parent
if str(main_dir) not in sys.path:
    sys.path.insert(0, str(main_dir))

from src.sweep import SweepMeasure
import re
import platform

WINDOWS_DIR_PATH_REGEX = r'^(?:[a-zA-Z]:\\|\\\\(?:[^\\\:*?"<>| \t\r\n]+)\\)(?:[^\\\:*?"<>|\r\n]+\\)*' 
WINDOWS_FILE_NAME_REGEX = r'[^\\\:*?"<>|]+'
WINDOWS_FILE_PATH_REGEX = f'^{WINDOWS_DIR_PATH_REGEX}{WINDOWS_FILE_NAME_REGEX}'
UNIX_DIR_PATH_REGEX = r'^(\/|(?:\.\.?\/)|[a-zA-Z0-9_\-\s.]+)(\/[a-zA-Z0-9_\-\s.]+)*\/'
UNIX_FILE_NAME_REGEX = r'[^/]+'
FILE_EXTENSION_REGEX = r'\.(csv|mat|json)'

# parametri passabili alla chiamata del programma
ALLOWED_ARGUMENTS = {
    #########################################################
    # argomenti per sweep measure
    #########################################################
    
    # identificativo della sorgente da cui il generatore invia il segnale
    '-gen_source': {
        'regex': r'[1-4]',
        'message': 'Inserire la sorgente del generatore da cui inviare il segnale',
        'error_message': 'Formato non valido per l\'argomento -gen_source\nSintassi: -gen_source <identificativo_della_sorgente_del_generatore> (da 1 a 4)',
        'required': True
    },
    # identificativo del canale 1 dell'oscilloscopio
    '-ch1': {
        'regex': r'[1-4]',
        'message': 'Inserire il canale 1 dell\'oscilloscopio',
        'error_message': 'Formato non valido per l\'argomento -ch1\nSintassi: -ch1 <identificativo_del_canale_dell\'oscilloscopio> (da 1 a 4)',
        'required': True
    },
    # identificativo del canale 2 dell'oscilloscopio
    '-ch2': {
        'regex': r'[1-4]',
        'message': 'Inserire il canale 2 dell\'oscilloscopio',
        'error_message': 'Formato non valido per l\'argomento -ch2\nSintassi: -ch2 <identificativo_del_canale_dell\'oscilloscopio> (da 1 a 4)',
        'required': True
    },
    # sweep di frequenze (start:stop:step)
    '-sweep': {
        'regex': r'\b\d+:\d+:\d+\b',
        'message': 'Inserire lo sweep di frequenze: <frequenza_iniziale>:<frequenza_finale>:<step>',
        'error_message': 'Formato non valido per l\'argomento -sweep\nSintassi: -sweep <frequenza_iniziale>:<frequenza_finale>:<step>',
        'required': True
    },
    # ampiezza del segnale che il generatore deve inviare alla sorgente
    '-signal_ampl': {
        'regex': r'\d+[.]?\d*',
        'message': 'Inserire l\'ampiezza [Vpp] del segnale da inviare al circuito',
        'error_message': 'Formato non valido per l\'argomento -signal_ampl\nSintassi: -signal_ampl <ampiezza_segnale_Vpp>',
        'required': True 
    },                 
    # durata dell'intervallo di tempo in cui eseguire la misura
    '-time_int': {
        'regex': r'\d+[.]?\d*',
        'message': 'Inserire la durata dell\'intervallo di tempo [s] in cui eseguire la misura su una singola forma d\'onda',
        'error_message': 'Formato non valido per l\'argomento -time_int\nSintassi: -time_int <durata_intervallo_s>',
        'required': False
    },                
    # frequenza di campionamento    
    '-sampl_freq': {
        'regex': r'\d+[.]?\d*',
        'message': 'Inserire la frequenza di campionamento [Hz] della forma d\'onda',
        'error_message': 'Formato non valido per l\'argomento -sampl_freq\nSintassi: -sampl_freq <frequenza_di_campionamento>',
        'required': False
    },
    # percorso della directory in cui inserire i punti delle forme d'onda acquisite sul canale 1 e 2
    '-points_data_base_path': {
        'regex': WINDOWS_DIR_PATH_REGEX if platform.system() == 'Windows'
                    else UNIX_DIR_PATH_REGEX,
        'message': 'Inserire il percorso della directory in cui inserire i punti delle forme d\'onda acquisite sui canali specificati',
        'error_message': 'Formato non valido per l\'argomento -points_data_base_path\nPercorso non valido',
        'required': False
    },
    # formato dei dati dei punti delle forme d'onda acquisite sui canali dell'oscilloscopio
    '-points_data_format': {
        'regex': r'(csv|mat|json|none)',
        'message': 'Inserire il formato dei dati in cui salvare i dati dei punti delle forme d\'onda acquisite sui canali specificati',
        'error_message': 'Formato non valido per l\'argomento -points_data_format\nFormato non supportato',
        'required': False
    },
    # percorso del file in cui inserire le misure svolte sui capi del carico    
    '-measure_path': {
        'regex': f'{WINDOWS_DIR_PATH_REGEX}{WINDOWS_FILE_NAME_REGEX}{FILE_EXTENSION_REGEX}' if platform.system() == 'Windows'
                    else f'{UNIX_DIR_PATH_REGEX}{UNIX_FILE_NAME_REGEX}{FILE_EXTENSION_REGEX}',
        'message': 'Inserire il percorso del file in cui inserire le misure svolte sui capi del carico',
        'error_message': 'Formato non valido per l\'argomento -measure_path\nPercorso non valido',
        'required': False
    },
    # percorso del file in cui inserire i dati di ampiezza e fase dell'impedenza ricavati
    '-impedence_path': {
        'regex': f'{WINDOWS_DIR_PATH_REGEX}{WINDOWS_FILE_NAME_REGEX}{FILE_EXTENSION_REGEX}' if platform.system() == 'Windows'
                    else f'{UNIX_DIR_PATH_REGEX}{UNIX_FILE_NAME_REGEX}{FILE_EXTENSION_REGEX}',
        'message': 'Inserire il percorso del file in cui inserire i dati di ampiezza e fase dell\'impedenza del carico',
        'error_message': 'Formato non valido per l\'argomento -impendence_path\nPercorso non valido',
        'required': False
    },
    # ribadisce che l'utente non vuole salvare in maneira permanente nulla, se specificato, 
    # il menu non chiede all'utente di inserire i percorsi dove salvare i dati    
    '-no_permanent_saving': {
        'regex': None,
        'message': None,
        'error_message': None,
        'required': False
    },         
    
    #########################################################
    # argomenti per diagramma ampiezza-fase
    #########################################################
    
    # valore della resistenza di Shunt
    '-shunt': {
        'regex': r'\d+[.]?\d*',
        'message': 'Inserire il valore della resistenza di Shunt del circuito [Ohm]',
        'error_message': 'Formato non valido per l\'argomento -shunt\nSintassi: -shunt <resistenza_Ohm>',
        'required': True
    },                 
    
    #########################################################
    # altri argomenti
    #########################################################
    
    # richiesta della pagina del manuale
    '--help': {
        'regex': None,
        'message': None,
        'error_message': None,
        'required': False
    },
    # richiesta della pagina del manuale      
    '--h': {'regex': None,
        'message': None,
        'error_message': None,
        'required': False
    },                 
}

class ArgumentParser:
    def __init__(self, arguments):
        self.arguments = arguments
    
    def get_parameter(self, param):
        idx = self.arguments.index(param) if param in self.arguments else -1        
        
        if idx == -1: # argomento non specificato
            if not ALLOWED_ARGUMENTS[param]['required']: # se non è obbligatorio impostalo al valore di default
                
                # se però sono dei parmetri dove si può dare una scelta all'utente chiediglielo comunque
                if ((param == '-points_data_base_path' or param == '-measure_path' or param == '-impedence_path' or param == '-points_data_format') 
                    and '-no_permanent_saving' not in self.arguments):
                    argument_value = input(f'{ALLOWED_ARGUMENTS[param]["message"]}: ')
                
                return None
            else: # se è obbligatorio chiediglielo
                argument_value = input(f'{ALLOWED_ARGUMENTS[param]["message"]}: ')
        else: # l'argomento deve essere per forza il successivo
            argument_value = self.arguments[idx + 1]
        
        while(not self.check_parameter_value(argument_value, param)): # argomento non valido
            argument_value = input(f'{ALLOWED_ARGUMENTS[param]["message"]}: ')
            
            if '--help' in argument_value or '--h' in argument_value:
                show_help()
                argument_value = input(f'{ALLOWED_ARGUMENTS[param]["message"]}: ')
        return argument_value
        
    def check_parameter_value(self, argument_value, param):
        # per test
        #print(f">>>> Regex: {ALLOWED_ARGUMENTS[param]['regex']}")
        if bool(re.compile(ALLOWED_ARGUMENTS[param]['regex']).fullmatch(argument_value)):
            return True
        
        print(f'ERROR: {ALLOWED_ARGUMENTS[param]["error_message"]}\n')
        return False

#
# dati gli argomenti con cui è stato chiamato il programma principale, dirige la creazione dell'oggetto sweepMeasure e 
# chiede all'utente di specificare gli argomenti obbligatori non inseriti negli args
# #
def show_menu(args, sweep: SweepMeasure):
    # mostra la documentazione
    #if '--help' in args or '--h' in args:
    #    show_help()
    #    sys.exit(0)

    argument_parser = ArgumentParser(args)

    sweep.set_generator_source(int(argument_parser.get_parameter('-gen_source')))
    sweep.set_oscilloscope_channel1(int(argument_parser.get_parameter('-ch1')))
    sweep.set_oscilloscope_channel2(int(argument_parser.get_parameter('-ch2')))
    sweep_range = argument_parser.get_parameter('-sweep').split(':')
    sweep.set_sweep_range(int(sweep_range[0]), int(sweep_range[1]), int(sweep_range[2]))
    sweep.set_signal_amplitude(float(argument_parser.get_parameter('-signal_ampl')))
    sweep.set_shunt_resistance(float(argument_parser.get_parameter('-shunt')))
    
    # gestione dei parametri facoltativi
    parameter = argument_parser.get_parameter('-time_int')
    if parameter != None: sweep.set_time_interval(float(parameter))
    
    parameter = argument_parser.get_parameter('-sampl_freq')
    if parameter != None: sweep.set_sampling_frequence(float(parameter))
    
    sweep.enable_point_data_saving(
        argument_parser.get_parameter('-points_data_base_path'),
        argument_parser.get_parameter('-points_data_format')    
    )
    sweep.enable_measurements_saving(argument_parser.get_parameter('-measure_path'))
    sweep.enable_impedence_data_saving(argument_parser.get_parameter('-impedence_path'))
    
    # per test 
    #print(sweep.to_string())
    
    # Controlla che tutti i parametri obbligatori siano stati inseriti
    if not sweep.check_status():
        raise RuntimeError('ERROR: errore nella specifica dei parametri: un parametro obbligatorio non è stato specificato, digitare python applt.py --help per consultare la documentazione')

def show_help():
    print(f"================================APPLT help page================================\n" +
          f" Tool per la generazione del diagramma ampiezza fase di un carico\n" + 
          f"USO\n" +
          f"  python applt.py [ARGOMENTI]\n" +
          f"DESCRIZIONE\n" +
          f"  Il programma genera il diagramma ampiezza fase del carico inserito in un circuito\n" + 
          f"  costituito dai seguenti elementi posti in serie:\n" +
          f"     + un generatore di segnale\n" +
          f"     + il carico di cui si vuole ricavare il diagramma\n" +
          f"     + una resistenza di shunt\n" +
          f"  Per generare tale diagramma esegue delle misurazioni comandando un oscilloscopio.\n" + 
          f"  Per eseguire le misurazioni si deve porre una sonda dell'osclloscopio sul nodo posto \n" +
          f"  tra il generatore e il carico (questa verrà nominata canale 1) e un'altra sonda \n" +
          f"  sul nodo tra il carico e la resistenza di shunt (questa verrà nominata canale 2)\n" +
          f"  Le misurazioni avvengono sullo sweep di frequenze specificato.\n" +
          f"ARGOMENTI\n" +
          f" -gen_source <identificativo_sorgente>                      specifica la sorgente del generatore da cui inviare il segnale\n" +
          f" -ch1 <identificativo_canale>                               specifica il canale dell'oscilloscopio posto sul nodo tra il generatore e il carico\n" +
          f" -ch2 <identificativo_canale>                               specifica il canale dell'oscilloscopio posto sul nodo tra il carico e la resistenza di shunt\n" +
          f" -sweep <frequenza_iniziale>:<frequenza_finale>:<step>      specifica lo sweep di frequenza su cui fare le misurazioni\n" +
          f" -signal_ampl <ampiezza_segnale_Vpp>                        specifica l'ampiezza [Vpp] del segnale da inviare al circuito\n" +
          f" -time_int <valore_intervallo> (opzionale)                  specifica la durata dell'intervallo di tempo [s] in cui campionare le singole forme d'onda\n" +
          f"                                                            (default: 0.01[s])\n" +
          f" -sampl_freq <frequenza_di_campionamento> (opzionale)       specifica la frequenza di campionamento [Hz] delle singole forme d'onda (default: 10^6[Hz])\n"
          f" -shunt <valore_resistenza>                                 specifica il valore della resistenza di shunt [Ohm]\n" +
          f" -points_data_base_path <percorso_directory> (opzionale)    specifica il percorso della directory in cui si vogliono salvare i dati dei campioni delle\n" +
          f"                                                            singole forme d'onda\n"+
          f"                                                            (se non specificato il programma non salva tali dati in maniera persistente)\n"+
          f" -points_data_format <formato> (opzionale)                  specifica il formato dei file in cui salvare i dati dei campioni delle singole forme d'onda\n"+
          f"                                                            (valori possibili: csv, mat, json)\n" +
          f" -measure_path <percorso_file> (opzionale)                  specifica il percorso del file in cui salvare le misure di ampiezza e fase delle singole forme d'onda\n" +
          f"                                                            (se non specificato il programma non salva tali dati in maniera persistente)\n" +
          f" -impedence_path <percorso_file> (opzionale)                specifica il percorso del file in cui salvare i valori di ampiezza e fase dell'impedenza ricavati\n" +
          f"                                                            (se non specificato il programma non salva tali dati in maniera persistente)\n" +
          f" -no_permanent_saving (opzionale)                           vieta al programma di salvare dati in maniera persistente\n" +
          f" --help                                                     mostra questa pagina"
        )