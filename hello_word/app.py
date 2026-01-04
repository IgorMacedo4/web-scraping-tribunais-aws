import json
from crawlers.tribunais_handlers import TribunaisHandlers
from proxy_test import handler_proxy, test_socket, HEADERS, TARGET, PROXY

import logging
logging.getLogger().setLevel(logging.INFO)

import signal

class TimeoutException(Exception):
    """Custom exception to handle timeouts."""
    pass
def timeout_handler(signum, frame):
    """Signal handler to raise a TimeoutException."""
    raise TimeoutException("Function execution timed out")

# Register the signal handler for timeouts
signal.signal(signal.SIGALRM, timeout_handler)

# Set a timeout for the function execution
TIMEOUT = 55 # 38

# -*- coding: utf-8 -*-

def lambda_handler(event, context=None):
    """
    Sample pure Lambda function

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """
    logging.info(event['body'])
    if 'test' in json.loads(event['body']):
        return handler_proxy('', '')

    signal.alarm(TIMEOUT)  # Set timeout to 10 seconds
    try:
        handler = TribunaisHandlers()
        proc = json.loads(event['body'])['num_cnj']
        request_id = event.get('requestContext', {}).get('requestId', 'unknown')

        logging.info(f"requestId: {request_id} - Tribunal: {handler.codigo_tribunal(proc)}; Processo: {proc}")

        andamentos = handler.consultar(proc)

        logging.info(f"requestId: {request_id} - Tribunal: {handler.codigo_tribunal(proc)}; Processo: {proc} - Movimentos Processuais - {andamentos}")

    except Exception as erro:

        logging.error(json.dumps({
            "error": str(erro),
            "input": f"requestId: {request_id} - Processo: {proc} - Erro ao consultar o processo: {erro}"
            })
        )
        
        if isinstance(erro, TimeoutException):
            raise TimeoutException(f"Consulta ao processo {proc} excedeu o tempo limite de {TIMEOUT} segundos.")
        else:
            return {
                "statusCode": 504,
                "body": json.dumps({"error": f"Erro: {erro}\nBody:\n{event['body']}"}),
            }
    
    finally:
        signal.alarm(0)
    
    return {
            "statusCode": 200,
            "body": json.dumps({"movimentos_processo": str(andamentos)}),
        }
