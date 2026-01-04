from requests import Session
from time import sleep
import json
import re
from html.parser import HTMLParser
from time import sleep
from datetime import datetime

class TRF3Headers:
    """Agrupa os campos de cabeçalho que variam conforme SO/navegador."""

    VERSAO_NAVEGADOR = '142'

    USER_AGENT = f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{VERSAO_NAVEGADOR}.0.0.0 Safari/537.36'
    # USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36'
    
    SEC_CH_UA = f'"Google Chrome";v="{VERSAO_NAVEGADOR}", "Not_A Brand";v="8", "Chromium";v="{VERSAO_NAVEGADOR}"'
    # SEC_CH_UA = '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"'

    SEC_CH_UA_PLATFORM = '"Windows"'
    # SEC_CH_UA_PLATFORM = '"macOS"'

    SEC_CH_UA_MOBILE = '?0'

class MeuParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.texto = []
        self.ignorando = False

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.ignorando = True

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.ignorando = False

    def handle_data(self, data):
        if not self.ignorando:
            self.texto.append(data)

    def obter_texto(self):
        return ''.join(self.texto)


def extrai_text(movimentos):
    parser = MeuParser()
    parser.feed(movimentos)

    # Obtendo e imprimindo o texto extraído
    texto_extraido = parser.obter_texto()
    lines = (line.strip() for line in texto_extraido.splitlines())

    # Divide múltiplas linhas em uma única linha
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))

    # Junta as partes em um único texto
    cleaned_text = "\n".join(chunk for chunk in chunks if chunk)
    
    return cleaned_text


def formatar_andamentos(texto_extraido):

    dados_desnecessarios = (
    ' Ação Coletiva de subst. processual:' 
    # + texto_extraido # .split(' Ação Coletiva de subst. processual:')[1].split('\n')[0]
    )
    andamentos_formatados = (
            texto_extraido
            .replace(dados_desnecessarios, '')
            .replace('Número Processo\n', 'Número do Processo: ')
            .replace('Data da Distribuição\n', '\nData da Distribuição: ')
            .replace('Órgão Julgador\n', 'Órgão Julgador: ')
            .replace('Jurisdição\n', 'Jurisdição: ')
            .replace('Classe Judicial\n', '\nClasse da Ação: ')
            .replace('Assunto\n','\nAssunto (Descrição, Código): ')
            .replace('Código Descrição', '')
            .replace('Polo ativo\nParticipanteSituação\n','Polo Ativo (Participante / Situação):\n')
            .replace('Polo Passivo\nParticipanteSituação\n', 'Polo Passivo (Participante / Situação):\n')
            .replace(r'MovimentoDocumento', '')
            .replace('Movimentações do Processo', '\n\nMOVIMENTAÇÕES DO PROCESSO:')
            .replace('Informações Adicionais', '\nInformações Adicionais:\n')
    )
    andamentos_formatados = re.sub(r'(\n( )*\n)+', '\n', andamentos_formatados)
    andamentos_formatados = re.sub(r'\s+-\s+', ' - ', andamentos_formatados)
    andamentos_formatados = re.sub(r'\s+\(', ' (', andamentos_formatados)
    andamentos_formatados = re.sub(r'\s+AUTOR - ', '\nAutor - ', andamentos_formatados)
    andamentos_formatados = re.sub(r'\s+Informações Adicionais:\s+Valor da Causa:\s+','\nInformações Adicionais:\nValor da Causa: ',andamentos_formatados)
    andamentos_formatados = re.sub(r'\s+Data inicial da contagem do prazo:', '; Data inicial da contagem do prazo:', andamentos_formatados)
    andamentos_formatados = re.sub(r'\s+Prazo:', '; Prazo:', andamentos_formatados)
    andamentos_formatados = re.sub(r'\s+Data final:', '; Data final:', andamentos_formatados)
    andamentos_formatados = re.sub(r'\s+Local:', '; Local:', andamentos_formatados)
    andamentos_formatados = re.sub(r'\s+Perito:', '; Perito:', andamentos_formatados)
    andamentos_formatados = re.sub(r'\s+ao Evento', ' ao Evento', andamentos_formatados)
    andamentos_formatados = re.sub(r'\s+Data:', '; Data:', andamentos_formatados)
    andamentos_formatados = re.sub(r'\n\d{1,2} resultados encontrados', '', andamentos_formatados)
    andamentos_formatados = re.sub(
        r'\)\s+LUIZ GUSTAVO BERTOLINI NASSIF\s+MG207353\s+-\s+INSTITUTO NACIONAL DO SEGURO SOCIAL - INSS\s+\(29.9\*\*\*\*\*\*\*\*\*\*\*\*\*\*\)\s+',
        ') LUIZ GUSTAVO BERTOLINI NASSIF MG207353\nRéu - INSTITUTO NACIONAL DO SEGURO SOCIAL - INSS (29.9**************) ', andamentos_formatados)

    last_line = re.search(
        r'(\s+V(?:\s+)?oltar(?:\s+)?(?:\nkeyboard_arrow_up)?)', 
        andamentos_formatados)
    if last_line:
        andamentos_formatados = andamentos_formatados.split(last_line.group(1))[0]

    datas = re.findall(r'\n(\d{1,2}) (\d{2}/\d{2}/\d{4}) \d{2}:\d{2}:\d{2} ', andamentos_formatados)
    for data in datas:
        andamentos_formatados = andamentos_formatados.replace(
            ' '.join(data), f'{data[0]} - {data[1]} -')

    return andamentos_formatados


def extrair_payload_do_html(html, processo):
    
    import re
    from datetime import datetime

    # Extrair ViewState
    try:
        viewstate = html.split('javax.faces.ViewState" value="')[1].split('"')[0]
    except Exception:
        viewstate = 'j_id1'

    # Dicionário para armazenar os IDs encontrados
    ids = {}

    # Padrões para encontrar os IDs no HTML
    # Exemplo: <input type="text" id="fPP:j_id164:processoReferenciaInput" name="fPP:j_id164:processoReferenciaInput"

    # ID para processo de referência
    match = re.search(r'name="(fPP:[^"]*:processoReferenciaInput)"', html)
    if match:
        ids['processoReferenciaInput'] = match.group(1)

    # ID para nome da parte
    match = re.search(r'name="(fPP:dnp:nomeParte)"', html)
    if match:
        ids['nomeParte'] = match.group(1)

    # ID para nome do advogado
    match = re.search(r'name="(fPP:[^"]*:nomeAdv)"', html)
    if match:
        ids['nomeAdv'] = match.group(1)

    # ID para classe judicial
    match = re.search(r'name="(fPP:[^"]*:classeJudicial)"', html)
    if match:
        ids['classeJudicial'] = match.group(1)
        ids['sgbClasseJudicial_selection'] = match.group(1).replace('classeJudicial', 'sgbClasseJudicial_selection')

    # ID para documento da parte
    match = re.search(r'name="(fPP:dpDec:documentoParte)"', html)
    if match:
        ids['documentoParte'] = match.group(1)

    # ID para número da OAB
    match = re.search(r'name="(fPP:Decoration:numeroOAB)"', html)
    if match:
        ids['numeroOAB'] = match.group(1)

    # ID para campo auxiliar da OAB (geralmente j_id seguido de número)
    match = re.search(r'name="(fPP:Decoration:j_id\d+)"', html)
    if match:
        ids['decorationJId'] = match.group(1)

    # ID para estado combo OAB
    match = re.search(r'name="(fPP:Decoration:estadoComboOAB)"', html)
    if match:
        ids['estadoComboOAB'] = match.group(1)

    # ID do botão de pesquisa (geralmente fPP:j_id seguido de número)
    match = re.search(r'name="(fPP:j_id\d+)"[^>]*type="submit"', html)
    if match:
        ids['submitButton'] = match.group(1)

    # Construir payload com os IDs extraídos ou valores padrão
    payload = {
        'AJAXREQUEST': '_viewRoot',
        'fPP:numProcesso-inputNumeroProcessoDecoration:numProcesso-inputNumeroProcesso': processo,
        'mascaraProcessoReferenciaRadio': 'on',
        ids.get('processoReferenciaInput', 'fPP:j_id164:processoReferenciaInput'): '',
        ids.get('nomeParte', 'fPP:dnp:nomeParte'): '',
        ids.get('nomeAdv', 'fPP:j_id182:nomeAdv'): '',
        ids.get('classeJudicial', 'fPP:j_id191:classeJudicial'): '',
        ids.get('sgbClasseJudicial_selection', 'fPP:j_id191:sgbClasseJudicial_selection'): '',
        'tipoMascaraDocumento': 'on',
        ids.get('documentoParte', 'fPP:dpDec:documentoParte'): '',
        ids.get('numeroOAB', 'fPP:Decoration:numeroOAB'): '',
        ids.get('decorationJId', 'fPP:Decoration:j_id225'): '',
        ids.get('estadoComboOAB', 'fPP:Decoration:estadoComboOAB'): 'org.jboss.seam.ui.NoSelectionConverter.noSelectionValue',
        'fPP:dataAutuacaoDecoration:dataAutuacaoInicioInputDate': '',
        'fPP:dataAutuacaoDecoration:dataAutuacaoInicioInputCurrentDate': datetime.now().strftime('%m/%Y'),
        'fPP:dataAutuacaoDecoration:dataAutuacaoFimInputDate': '',
        'fPP:dataAutuacaoDecoration:dataAutuacaoFimInputCurrentDate': datetime.now().strftime('%m/%Y'),
        'fPP': 'fPP',
        'autoScroll': '',
        'javax.faces.ViewState': viewstate,
        ids.get('submitButton', 'fPP:j_id246'): ids.get('submitButton', 'fPP:j_id246'),
        'AJAX:EVENTS_COUNT': '1',
    }

    return payload


import logging

def trf3(processo):

    s = Session()

    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        'cache-control': 'no-cache',
        'pragma': 'no-cache',
        'priority': 'u=0, i',
        'referer': 'https://www.google.com/',
        'sec-ch-ua': TRF3Headers.SEC_CH_UA,
        'sec-ch-ua-mobile': TRF3Headers.SEC_CH_UA_MOBILE,
        'sec-ch-ua-platform': TRF3Headers.SEC_CH_UA_PLATFORM,
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'cross-site',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': TRF3Headers.USER_AGENT,
        # 'cookie': 'JSESSIONID2=...'
    }

    r = s.get('https://pje1g.trf3.jus.br/pje/ConsultaPublica/listView.seam', headers=headers,
            # proxies={"http":"http://170.106.118.114:2334:u7b247c4a561205c0-zone-custom-region-br-session-n3AL7TiyZ-sessTime-120:u7b247c4a561205c0"}
    )
    logging.info(f'Primeira requisicao: {r.status_code}')
    sleep(0.5)

    # Construir payload dinamicamente extraindo IDs do HTML
    data = extrair_payload_do_html(r.text, processo)
    logging.info(f'Payload construído dinamicamente: {data}')

    r = s.post(
        'https://pje1g.trf3.jus.br/pje/ConsultaPublica/listView.seam',
        # cookies=cookies,
        headers=headers,
        data=data,
        # proxies={"http":"http://170.106.118.114:2334:u7b247c4a561205c0-zone-custom-region-br-session-n3AL7TiyZ-sessTime-120:u7b247c4a561205c0"}
    
    )
    logging.info(f'Segunda requisicao: {r.status_code}')
    try:
        ca = r.text.split('ca=')[1].split("'")[0]
    except Exception:
        s.close()
        return 'Sua pesquisa não encontrou nenhum processo disponível.'

    sleep(0.3)

    params = {'ca': ca}

    r = s.get(
        'https://pje1g.trf3.jus.br/pje/ConsultaPublica/DetalheProcessoConsultaPublica/listView.seam',
        params=params, headers=headers, timeout=12,
        # proxies={"http":"http://170.106.118.114:2334:u7b247c4a561205c0-zone-custom-region-br-session-n3AL7TiyZ-sessTime-120:u7b247c4a561205c0"}
    )
    logging.info(f"Terceira requisicao: {r.status_code}")
    sleep(0.3)
    
    try:
        pages = r.text.split('rich-inslider-right-num ">')[1].split("</")[0]
    except Exception:
        pages = 1
    view_state = r.text.split('ViewState" value="')[1].split('"')[0]
    
    andamentos = extrai_text(r.text)
    andamentos_formatados = 'DADOS DA CAPA DO PROCESSO:\n' + andamentos.split('«»Dados do Processo')[1] 
    final_chunk = re.search(r'\d{1,3} resultados encontrados(.*)\nDocumentoCertidão', andamentos_formatados)
    if final_chunk:
        andamentos_formatados = andamentos_formatados.split(final_chunk.group(0))[0]
    todos_movimentos = andamentos_formatados
    
    # if pages == 1:
    #     return formatar_andamentos(todos_movimentos)
    if pages != 1:
        for page in range(2, min(int(pages)+1, 3)):

            headers = {
                'accept': '*/*',
                'accept-language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
                'cache-control': 'no-cache',
                'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'origin': 'https://pje1g.trf3.jus.br',
                'pragma': 'no-cache',
                'priority': 'u=1, i',
                'referer': f'https://pje1g.trf3.jus.br/pje/ConsultaPublica/DetalheProcessoConsultaPublica/listView.seam?ca={ca}',
                'sec-ch-ua': TRF3Headers.SEC_CH_UA,
                'sec-ch-ua-mobile': TRF3Headers.SEC_CH_UA_MOBILE,
                'sec-ch-ua-platform': TRF3Headers.SEC_CH_UA_PLATFORM,
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'user-agent': TRF3Headers.USER_AGENT,
                # 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            }

            data = f'AJAXREQUEST=j_id142%3Aj_id466&j_id142%3Aj_id543%3Aj_id544={page}&j_id142%3Aj_id543=j_id142%3Aj_id543&autoScroll=&javax.faces.ViewState={view_state}&j_id142%3Aj_id543%3Aj_id545=j_id142%3Aj_id543%3Aj_id545&AJAX%3AEVENTS_COUNT=1&'

            response = s.post(
                f'https://pje1g.trf3.jus.br/pje/ConsultaPublica/DetalheProcessoConsultaPublica/listView.seam', 
                headers=headers, data=data, timeout=20,
                # proxies={"http":"http://170.106.118.114:2334:u7b247c4a561205c0-zone-custom-region-br-session-n3AL7TiyZ-sessTime-120:u7b247c4a561205c0"}
    
            )
            logging.info(f"Quarta requisicao: {response.status_code}")
            movs = extrai_text(response.text).replace('Movimentações do ProcessoMovimentoDocumento', '')
            
            datas = re.findall(r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}', movs)
            for data in datas:
                movs = movs.replace(data, f"\n{data}")
            final_chunk = re.search(r'(\d{1,3} resultados encontrados(.*)(?:\n)?)', movs)
            if final_chunk:
                movs = movs.split(final_chunk.group(1))[0]
            movs = re.sub(r'\n+', '\n', movs)
            todos_movimentos += f'{movs}'

    publicacoes = []
    html_first_page = r.text
    padrao_url = r"(https://pje1g\.trf3\.jus\.br:443/pje/ConsultaPublica/DetalheProcessoConsultaPublica/documentoSemLoginHTML\.seam\?ca=(?:.*)&amp;idProcessoDoc=\d{5,11}&amp;codigo=)'\);"

    for url in list(set(re.findall(padrao_url, html_first_page))):

        params = {
            'ca': url.split('ca=')[1].split('&')[0],
            'idProcessoDoc': url.split('idProcessoDoc=')[1].split('&')[0],
            'codigo': '',
        }
        response = s.get(
            'https://pje1g.trf3.jus.br/pje/ConsultaPublica/DetalheProcessoConsultaPublica/documentoSemLoginHTML.seam',
            params=params, headers=headers, timeout=12,
            # proxies={"http":"http://170.106.118.114:2334:u7b247c4a561205c0-zone-custom-region-br-session-n3AL7TiyZ-sessTime-120:u7b247c4a561205c0"}
        )
        logging.info(f"Quinta requisicao: {response.status_code}")
        publicacao = extrai_text(response.text)
        data = re.findall(r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}', publicacao)
        if data and all(len(publicacao) != len(publicacao_capturada[1]) for publicacao_capturada in publicacoes):
            publicacoes.append((data[0], re.sub('\n+', ' ',publicacao.split('Assinado eletronicamente por:')[0])))

        sleep(0.3)

    andamentos_formatados_lista = todos_movimentos.split('\n')
    for publicacao in publicacoes:
        for index, linha in enumerate(andamentos_formatados_lista):
            if publicacao[0] in linha:
                andamentos_formatados_lista[index] = linha + ' - Conteúdo do Movimento: "' + publicacao[1] + '"'
                break

    movimentos_com_publicacoes = '\n'.join(andamentos_formatados_lista)

    return formatar_andamentos(movimentos_com_publicacoes)

# print(trf3('5000589-93.2019.4.03.6183')) # '0007160-72.2020.4.03.6332'))