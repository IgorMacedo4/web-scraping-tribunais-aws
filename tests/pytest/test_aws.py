import re
import pytest
import requests
import os

API_URL = os.getenv('AWS_API_URL', 'https://your-api-gateway.execute-api.us-east-1.amazonaws.com/Prod/hello/')

CASOS_POR_TRIBUNAL = {
    # Números de processos fictícios para demonstração
    'trf3': ['0000001-11.2024.4.03.0000', '0000002-22.2024.4.03.0000'],
    'trf4': ['0000001-11.2025.4.04.7100', '0000002-22.2024.4.04.7110'],
}

TODOS_OS_CASOS_DE_TESTE = [
    (tribunal, processo)
    for tribunal, processos in CASOS_POR_TRIBUNAL.items()
    for processo in processos
]

def consultar_processo_api(numero_processo: str) -> dict:
    try:
        response = requests.post(API_URL, json={"num_cnj": numero_processo}, timeout=300)
        return response.json()
    except Exception as e:
        return {"error": str(e), "process": numero_processo}

def normalizar_numero_processo(dado: any) -> str:
    return re.sub(r'\D', '', str(dado))

@pytest.mark.parametrize("tribunal, numero_processo", TODOS_OS_CASOS_DE_TESTE)
def test_consulta_retorna_processo_correto(tribunal, numero_processo):
    resultado = consultar_processo_api(numero_processo)
    numero_pesquisado_normalizado = normalizar_numero_processo(numero_processo)
    conteudo_retornado_normalizado = normalizar_numero_processo(resultado)
    assert numero_pesquisado_normalizado in conteudo_retornado_normalizado, \
        f"Número do processo {numero_processo} não foi encontrado no resultado retornado pelo tribunal '{tribunal}'"