import re
import pytest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from hello_word.crawlers.tjac import tjac

from hello_word.crawlers.trf3 import trf3
from hello_word.crawlers.trf4 import trf4

CASOS_POR_TRIBUNAL = {
    # Números de processos fictícios para demonstração
    trf3: ['0000001-11.2024.4.03.0000', '0000002-22.2024.4.03.0000'],
    trf4: ['0000001-11.2025.4.04.7100', '0000002-22.2024.4.04.7110'],
    tjac: ['0000001-11.2024.8.01.0001']

}

TODOS_OS_CASOS_DE_TESTE = [
    (crawler, processo)
    for crawler, processos in CASOS_POR_TRIBUNAL.items()
    for processo in processos
]

def normalizar_numero_processo(dado: any) -> str:
    """Converte o dado para string e remove caracteres não numéricos."""
    return re.sub(r'\D', '', str(dado))


@pytest.mark.parametrize("crawler_func, process_number", TODOS_OS_CASOS_DE_TESTE)
def test_consulta_retorna_processo_correto(crawler_func, process_number):
    """
    Verifica se o resultado da consulta contém o número do processo pesquisado.
    """
    resultado = crawler_func(process_number)

    numero_pesquisado_normalizado = normalizar_numero_processo(process_number)
    conteudo_retornado_normalizado = normalizar_numero_processo(resultado)

    assert numero_pesquisado_normalizado in conteudo_retornado_normalizado, \
        f"Número do processo {process_number} não foi encontrado no resultado retornado pelo crawler '{crawler_func.__name__}'"

if __name__ == "__main__":
    # Teste manual com número fictício
    print(trf3('0000001-11.2024.4.03.0000'))