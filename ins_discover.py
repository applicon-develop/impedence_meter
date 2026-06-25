import pyvisa

#
# Questo script stampa a video l'elenco degli indirizzi NI-VISA delle interfacce degli strumenti collegati
# #

re = pyvisa.ResourceManager()
list = re.list_resources() 
print(f'{list}' if list else 'Nessuno strumento trovato...')