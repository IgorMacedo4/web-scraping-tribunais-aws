import json
import re
import time
import os
from urllib.parse import urlparse, urlunparse
import certifi
import requests
from bs4 import BeautifulSoup
from twocaptcha import TwoCaptcha


class ConsultaProcessualTRF4:
    user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
    chave_solver_padrao = os.getenv('TWOCAPTCHA_API_KEY', 'your_api_key_here')

    def __init__(self, chave_solver: str | None = None):
        self.sessao = requests.Session()
        self.sessao.verify = certifi.where()
        self.sessao.cookies.set('aviso_privacidade_aceito', 'S', domain='.trf4.jus.br', path='/')
        self.solver = TwoCaptcha(chave_solver or self.chave_solver_padrao)
        self.url_portal = 'https://www.trf4.jus.br/trf4/controlador.php'
        self.url_consulta = 'https://consulta.trf4.jus.br/trf4/controlador.php'
        self.documentos_processados = set()

    def acessar_portal_principal(self):
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7,fr;q=0.6',
            'Connection': 'keep-alive',
            'Referer': 'https://www.trf4.jus.br/trf4/controlador.php?acao=pagina_visualizar&id_pagina=3929',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': self.user_agent,
            'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
        }
        params = {'acao': 'principal'}
        return self.sessao.get(self.url_portal, params=params, headers=headers, timeout=30)

    def acessar_pagina_pesquisa(self, processo, origem):
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7,fr;q=0.6',
            'Connection': 'keep-alive',
            'Referer': 'https://www.trf4.jus.br/',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-site',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': self.user_agent,
            'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
        }
        params = {
            'acao': 'consulta_processual_pesquisa',
            'strSecao': self.definir_secao_pesquisa(origem),
            'txtValor': processo,
            'selForma': 'NU',
            'txtDataFase': '01/01/1970',
            'chkMostrarBaixados': '',
        }
        return self.sessao.get(self.url_consulta, params=params, headers=headers, timeout=30)

    def carregar_validacao(self, processo, origem):
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'pt-BR,pt;q=0.9',
            'Connection': 'keep-alive',
            'Referer': f'https://consulta.trf4.jus.br/trf4/controlador.php?acao=consulta_processual_pesquisa&strSecao={self.definir_secao_pesquisa(origem)}&txtValor={processo}&selForma=NU&txtDataFase=01/01/1970&chkMostrarBaixados=',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': self.user_agent,
            'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
        }
        params = {
            'acao': 'consulta_processual_valida_pesquisa',
            'selForma': 'NU',
            'txtValor': processo,
            'selOrigem': origem,
            'txtOrigemPesquisa': '1',
        }
        return self.sessao.get(self.url_consulta, params=params, headers=headers, timeout=30)

    def resolver_captcha(self, sitekey, processo, origem):
        url_desafio = f'https://consulta.trf4.jus.br/trf4/controlador.php?acao=consulta_processual_valida_pesquisa&selForma=NU&txtValor={processo}&selOrigem={origem}&txtOrigemPesquisa=1'
        resposta = self.solver.turnstile(sitekey=sitekey, url=url_desafio)
        return resposta.get('code') if isinstance(resposta, dict) else None

    def enviar_validacao(self, processo, origem, token, campos_hidden):
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'pt-BR,pt;q=0.9',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://consulta.trf4.jus.br',
            'Referer': f'https://consulta.trf4.jus.br/trf4/controlador.php?acao=consulta_processual_valida_pesquisa&txtOrigemPesquisa=1&seq=&selForma=NU&txtValor={processo}&txtChave=&selOrigem={origem}&txtDataFase=01%2F01%2F1970',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': self.user_agent,
            'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
        }
        dados = dict(campos_hidden)
        dados.update({
            'cf-turnstile-response': token or '',
            'hdnInfraCaptcha': '1',
            'sbmContinuar': ' Continuar ',
            'selForma': dados.get('selForma', 'NU'),
            'txtValor': dados.get('txtValor', processo),
            'chkMostrarBaixados': dados.get('chkMostrarBaixados', ''),
            'todasfases': dados.get('todasfases', ''),
            'todosvalores': dados.get('todosvalores', ''),
            'todaspartes': dados.get('todaspartes', ''),
            'txtDataFase': dados.get('txtDataFase', '01/01/1970'),
            'selOrigem': origem,
            'sistema': dados.get('sistema', ''),
            'codigoparte': dados.get('codigoparte', ''),
            'txtChave': dados.get('txtChave', ''),
        })
        params = {'acao': 'consulta_processual_valida_pesquisa'}
        return self.sessao.post(self.url_consulta, params=params, headers=headers, data=dados, timeout=30)

    def consultar_resultado(self, processo, origem):
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7,fr;q=0.6',
            'Connection': 'keep-alive',
            'Referer': f'https://consulta.trf4.jus.br/trf4/controlador.php?acao=consulta_processual_valida_pesquisa&selForma=NU&txtValor={processo}&selOrigem={origem}&txtOrigemPesquisa=1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': self.user_agent,
            'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
        }
        params = {
            'acao': 'consulta_processual_resultado_pesquisa',
            'selForma': 'NU',
            'txtValor': processo,
            'chkMostrarBaixados': '',
            'todasfases': '',
            'todosvalores': '',
            'todaspartes': '',
            'txtDataFase': '01/01/1970',
            'selOrigem': origem,
            'sistema': '',
            'txtChave': '',
            'seq': '',
        }
        return self.sessao.get(self.url_consulta, params=params, headers=headers, timeout=30)

    def executar_busca(self, processo, origem):
        resposta_portal = self.acessar_portal_principal()
        resposta_pesquisa = self.acessar_pagina_pesquisa(processo, origem)
        resposta_validacao = self.carregar_validacao(processo, origem)
        sitekey, campos_hidden = self.analisar_validacao(resposta_validacao.text)
        token = self.resolver_captcha(sitekey, processo, origem)
        resposta_post = self.enviar_validacao(processo, origem, token, campos_hidden)
        time.sleep(1)
        resposta_resultado = self.consultar_resultado(processo, origem)
        if 'Sua pesquisa não encontrou nenhum processo disponível' in resposta_resultado.text:
            return 'Sua pesquisa não encontrou nenhum processo disponível.'
        paginas = self.coletar_paginas_movimentos(resposta_resultado.text, processo, origem)
        capa = self.extrair_capa(paginas[0])
        movimentos = self.extrair_movimentos(paginas)
        return self.formatar_resultado(capa, movimentos)

    def analisar_validacao(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        sitekey = None
        elemento = soup.find(attrs={'data-sitekey': True})
        if elemento:
            sitekey = elemento.get('data-sitekey')
        campos_hidden = {}
        for hidden in soup.select('input[type="hidden"]'):
            nome = hidden.get('name')
            if nome and nome not in campos_hidden:
                campos_hidden[nome] = hidden.get('value', '')
        return sitekey, campos_hidden

    def determinar_origem(self, processo):
        if len(processo) < 4:
            return None
        sufixo = processo[-4:]
        if sufixo.startswith('72'):
            return 'SC'
        if sufixo.startswith('71'):
            return 'RS'
        if sufixo.startswith('70'):
            return 'PR'
        if sufixo == '0000':
            return 'TRF'
        if sufixo == '9999':
            return 'DELEGADA'
        return None

    def definir_secao_pesquisa(self, origem):
        return origem if origem else 'TRF'

    def listar_origens(self, processo):
        origem_inicial = self.determinar_origem(processo)
        rotas = []
        if origem_inicial and origem_inicial not in ['DELEGADA']:
            rotas.append(origem_inicial)
        for candidato in ['TRF', 'SC', 'RS', 'PR']:
            if candidato not in rotas:
                rotas.append(candidato)
        if origem_inicial == 'DELEGADA' and 'TRF' not in rotas:
            rotas.insert(0, 'TRF')
        return rotas

    def coletar_paginas_movimentos(self, html_inicial, processo, origem):
        paginas = {0: html_inicial}
        return [paginas[p] for p in sorted(paginas.keys())]

    def extrair_paginas_relacionadas(self, html, visitados):
        soup = BeautifulSoup(html, 'html.parser')
        paginas = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if 'numPagina=' not in href:
                continue
            match = re.search(r'numPagina=(\d+)', href)
            if not match:
                continue
            pagina = int(match.group(1))
            if pagina not in visitados and pagina not in paginas:
                paginas.append(pagina)
        return paginas

    def consultar_resultado_pagina(self, processo, origem, pagina):
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7,fr;q=0.6',
            'Connection': 'keep-alive',
            'Referer': f'https://consulta.trf4.jus.br/trf4/controlador.php?acao=consulta_processual_valida_pesquisa&selForma=NU&txtValor={processo}&selOrigem={origem}&txtOrigemPesquisa=1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': self.user_agent,
            'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
        }
        params = {
            'acao': 'consulta_processual_resultado_pesquisa',
            'selForma': 'NU',
            'txtValor': processo,
            'chkMostrarBaixados': '',
            'todasfases': '',
            'todosvalores': '',
            'todaspartes': '',
            'txtDataFase': '01/01/1970',
            'selOrigem': origem,
            'sistema': '',
            'txtChave': '',
            'seq': '',
            'numPagina': str(pagina),
        }
        return self.sessao.get(self.url_consulta, params=params, headers=headers, timeout=30)

    def extrair_movimentos(self, paginas_html):
        movimentos = []
        self.documentos_processados = set()
        self.documentos_extraidos = 0
        for html in paginas_html:
            soup = BeautifulSoup(html, 'html.parser')
            tabela = soup.find('table', class_='tabela')
            if not tabela:
                continue
            for linha in tabela.find_all('tr'):
                colunas = linha.find_all('td', recursive=False)
                if len(colunas) < 3:
                    continue
                sequencia = colunas[0].get_text(strip=True)
                if not sequencia.isdigit():
                    continue
                data = colunas[1].get_text(' ', strip=True)
                descricao = colunas[2].get_text(' ', strip=True)
                anexos = self.coletar_documentos(linha)
                movimentos.append({'sequencia': sequencia, 'data': data, 'descricao': descricao, 'documentos': anexos})
        return movimentos

    def coletar_documentos(self, linha):
        anexos = []
        for link in linha.find_all('a', href=True):
            href = link['href']
            if 'acessar_documento_publico' not in href:
                continue
            info = self.extrair_parametros_documento(href)
            if not info or info['doc'] in self.documentos_processados:
                continue
            self.documentos_processados.add(info['doc'])
            if self.documentos_extraidos >= 2:
                break
            conteudo = self.baixar_documento(info)
            anexos.append({'nome': link.get_text(strip=True), 'dados': info, 'conteudo': conteudo})
            self.documentos_extraidos += 1
        return anexos

    def extrair_parametros_documento(self, href):
        match_doc = re.search(r'doc=([^&]+)', href)
        match_evento = re.search(r'evento=([^&]+)', href)
        match_key = re.search(r'key=([^&]+)', href)
        match_hash = re.search(r'hash=([^&]+)', href)
        if not (match_doc and match_evento and match_key and match_hash):
            return None
        return {
            'url': href,
            'doc': match_doc.group(1),
            'evento': match_evento.group(1),
            'key': match_key.group(1),
            'hash': match_hash.group(1),
        }

    def baixar_documento(self, info):
        url_publico = info['url']
        resposta_publico = self.sessao.get(url_publico, timeout=30)
        texto_publico = resposta_publico.text
        if 'Documento não encontrado' in texto_publico:
            return ''
        if '<article' in texto_publico or 'divBody' in texto_publico:
            resposta_publico.encoding = resposta_publico.apparent_encoding or resposta_publico.encoding or 'iso-8859-1'
            return resposta_publico.text
        parsed = urlparse(url_publico)
        implementacao_url = urlunparse(parsed._replace(query=''))
        headers = {
            'accept': '*/*',
            'accept-language': 'pt-BR,pt;q=0.9',
            'priority': 'u=0, i',
            'referer': url_publico,
            'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': self.user_agent,
            'x-requested-with': 'XMLHttpRequest',
        }
        params = {
            'acao': 'acessar_documento_implementacao',
            'acao_origem': 'acessar_documento_publico',
            'doc': info['doc'],
            'evento': info['evento'],
            'key': info['key'],
            'hash': info['hash'],
            'termosPesquisados': '',
        }
        resposta = self.sessao.get(implementacao_url, params=params, headers=headers, timeout=30)
        if 'Documento não encontrado' in resposta.text:
            return ''
        resposta.encoding = resposta.apparent_encoding or resposta.encoding or 'iso-8859-1'
        return resposta.text

    def extrair_capa(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        conteudo = soup.find(id='divConteudo') or soup.find('div', class_='conteudo') or soup
        copia = BeautifulSoup(str(conteudo), 'html.parser')
        tabela = copia.find('table', class_='tabela')
        if tabela:
            tabela.decompose()
        for link in copia.find_all('a', href=True):
            href = link['href']
            if 'consulta_processual_resultado_pesquisa' in href and 'numPagina=' in href:
                link.decompose()
        for elemento in copia(['script', 'style']):
            elemento.extract()
        linhas = [linha.strip() for linha in copia.get_text('\n').splitlines() if linha.strip()]
        return '\n'.join(linhas)

    def formatar_resultado(self, capa_texto, movimentos):
        corpo = capa_texto
        capa = (
            'DADOS DA CAPA DO PROCESSO:\n' +
            corpo.replace('PROCEDIMENTO', '\nPROCEDIMENTO')
            .replace('Data de autuação:', '\nData de autuação:')
            .replace('Tutela:', '\nTutela:')
            .replace('Juiz:', '\nJuiz(a):')
            .replace('Órgão Julgador:', '\nÓrgão Julgador:')
            .replace('Situação:', '\nSituação:')
            .replace('Justiça gratuita:', '\nJustiça gratuita:')
            .replace('Valor da causa:', '\nValor da Causa:')
            .replace('Intervenção MP:', '\nIntervenção MP:')
            .replace('Competência:', '\nCompetência:')
            .replace('Assuntos', '\nAssunto')
            .replace('AUTOR:', '\nAutor:')
            .replace('RÉU:', '\nRéu:')
            .replace('PERITO:', '\nPerito:')
        )
        capa = re.sub(r'(\n\s*){2,}', '\n', capa).strip()
        linhas_mov = []
        for mov in movimentos:
            linha = f"{mov['sequencia']} - {mov['data']} - {mov['descricao']}"
            for anexo in mov['documentos']:
                if anexo['conteudo']:
                    linha += f" - CONTEÚDO: {self.limpar_conteudo_documento(anexo['conteudo'])}"
            linhas_mov.append(linha)
        if linhas_mov:
            movimentos_txt = '\n'.join(linhas_mov)
            return f"{capa}\n\nMOVIMENTOS PROCESSUAIS:\n{movimentos_txt}"
        return capa

    def limpar_conteudo_documento(self, conteudo):
        soup = BeautifulSoup(conteudo, 'html.parser')
        for elemento in soup(['script', 'style']):
            elemento.extract()
        linhas = [linha.strip() for linha in soup.get_text(' ').splitlines() if linha.strip()]
        return re.sub(r'\s+', ' ', ' '.join(linhas))

    def buscar_processo(self, processo):
        numero = processo.strip()
        origem = self.listar_origens(numero)[0]
        return self.executar_busca(numero, origem)

    def consultar(self, processo):
        resultado_bruto = self.buscar_processo(processo)
        texto = re.sub(r'\s+', ' ', resultado_bruto).strip()
        return json.dumps({'movimentos_processo': texto}, ensure_ascii=False)


def trf4(processo: str) -> str:
    consulta = ConsultaProcessualTRF4()
    return consulta.consultar(processo)
