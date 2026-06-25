# APPLT - Amplitude Phase Plotter
APPLT è un tool che genera il diagramma di ampiezza e fase di un qualunque carico arbitrario.

## Setup
Collegare un generatore di segnale e un oscilloscopio ad un circuito che comprende il carico e una resistenza di Shunt
con valore di resistenza arbitrario. Collegare una sonda dell'oscilloscopio nel nodo tra il generatore e il carico (*canale 1*)
e un'altra nel nodo tra il carico e la resistenza di Shunt *(canale 2)*. 

L'oscilloscopio e il generatore devono essere compatibili con il protocollo di comunicazione NI-VISA. Gli indirizzi NI-VISA delle interfacce
dei due strumenti devono essere specificati nel file `config.ini` come segue:
```ini
[default]
OSCILLOSCOPE_VISA_ADDRESS = <indirizzo_interfaccia_oscilloscopio> 
GENERATOR_VISA_ADDRESS = <indirizzo_interfaccia_generatore>
```
Per ottenere gli indirizzi NI-VISA delle interfacce dei due strumenti eseguire il seguente script python:
```python
import pyvisa

re = pyvisa.ResourceManager()
print(re.list_resources())
```
oppure, eseguire in alternativa il file `ins_discover.py`. 

*NOTA: per scoprire lo strumento associato ad ogni indirizzo eseguire lo script ogni volta che viene collegato uno strumento*

## Prerequisiti
Per utilizzare il tool è richiesta linstallazione di una versione del protocollo [NI-VISA](https://www.ni.com/en/support/downloads/drivers/download.ni-visa.html?srsltid=AfmBOopw5HzeLWNJFbzZjas5lRyYnws8KxJGQZlaCvtE1vAyhimTcgca#590234) e del pacchetto python [pyvisa](https://www.pyvisa.com/)

```bash
pip install pyvisa
```

## Uso
Per avere una referenza sul funzionamento del tool aprire la pagina di help.
```bash
python applt.py --help
```
Esempio di uso:
```bash
python applt.py -gen_source 1 -ch1 1 -ch2 2 -sweep 18000:40000:500 -signal_ampl 10 -time_int 0.01 -sampl_freq 1000000 -points_data_base_path C:\\points\ -points_data_format json -measure_path C:\\measure.csv -impedence_path C:\\impedence.mat -shunt 12
```