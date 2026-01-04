import sys
import os
import time

# Adiciona o diretório do projeto à lista de caminhos do Python
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../hello_world')))
from crawlers.trf3 import trf3

processo = '0002877-39.2020.4.03.6321' 

print(f"Iniciando teste para processo {processo}...")
inicio = time.time()

resultado = trf3(processo)

tempo_decorrido = time.time() - inicio
print(f"\n{'='*60}")
print(f"Tempo total de execução: {tempo_decorrido:.2f} segundos")
print(f"{'='*60}\n")
print(resultado)