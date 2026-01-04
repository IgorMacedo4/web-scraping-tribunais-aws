processo = '5002601-66.2020.4.04.7202'

"""
import requests
from time import time

time_start = time()
print('Iniciando consulta...')
print(requests.post('https://jqlo0q82ek.execute-api.us-east-1.amazonaws.com/Prod/hello/', json={"num_cnj":"5005389-14.2024.4.04.7202"}).text)
print('Consulta finalizada em: ', time() - time_start)

"""
"""
TRF4 (5016525-17.2023.4.04.0000)
JFPR (5077491-92.2023.4.04.7000)
JFRS (5053239-16.2023.4.04.7100) 
JFSC (5005389-14.2024.4.04.7202)
"""
import sys
import os
import requests

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../hello_world')))

from crawlers.trf4 import trf4
from time import time

import logging

logging.getLogger().setLevel(logging.INFO)


if __name__ == '__main__':
    time_start = time()
    print('Iniciando consulta...')

    processo = '5005389-14.2024.4.04.7202'
    processo = '5002387-61.2023.4.04.7011'

    # print(trf4(processo))

    r = requests.post('https://jqlo0q82ek.execute-api.us-east-1.amazonaws.com/Prod/hello/', json={"num_cnj":processo})
    print(r.text)

    print('Consulta finalizada em: ', round(time() - time_start, 2))
