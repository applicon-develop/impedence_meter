import sys
from pathlib import Path

main_dir = Path(__file__).resolve().parent
if str(main_dir) not in sys.path:
    sys.path.insert(0, str(main_dir))

import src.menu as menu
import src.instruments as ins
from src.sweep import SweepMeasure
import configparser
import src.impedence_plot as iplt

def initialize_instruments():
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    oscilloscope_address = config.get('default', 'OSCILLOSCOPE_VISA_ADDRESS')
    generator_address = config.get('default', 'GENERATOR_VISA_ADDRESS')
    
    oscilloscope = ins.open_resource(oscilloscope_address)
    generator = ins.open_resource(generator_address)
    ins.initialize(oscilloscope)
    ins.initialize(generator)
    
    return oscilloscope, generator

if __name__ == '__main__':
    print(sys.argv)
    
    # mostra documentazione
    if '--h' in sys.argv or '--help' in sys.argv:
        menu.show_help()
        sys.exit(0)
    
    sweep = SweepMeasure()
    
    # inizializza gli strumenti
    oscilloscope, generator = initialize_instruments()
    sweep.set_oscilloscope(oscilloscope)
    sweep.set_generator(generator)
    
    # mostra il menu
    menu.show_menu(sys.argv, sweep)
    print(sweep.to_string())
    
    # esegui la misura
    frequencies, measurements, vg_waveforms, vs_waveforms = sweep.exec()
    # mostra il grafico
    iplt.impedence_applt(frequencies, measurements, vg_waveforms, vs_waveforms, sweep)