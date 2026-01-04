from requests import Session
from time import sleep
import re
from html.parser import HTMLParser
from bs4 import BeautifulSoup


class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.content_buffer = []
        self.skip_content = False

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.skip_content = True

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.skip_content = False

    def handle_data(self, data):
        if not self.skip_content:
            self.content_buffer.append(data)

    def get_extracted_text(self):
        return ''.join(self.content_buffer)


def extract_clean_text(html_content):
    """Extract clean text from HTML content"""
    text_parser = HTMLTextExtractor()
    text_parser.feed(html_content)
    
    extracted_text = text_parser.get_extracted_text()
    lines = (line.strip() for line in extracted_text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    cleaned_text = "\n".join(chunk for chunk in chunks if chunk)
    
    return cleaned_text


def extract_process_parties(html_content):
    """Extract process parties information"""
    document_parser = BeautifulSoup(html_content, 'html.parser')
    parties_list = []
    
    parties_table = document_parser.find('table', id='tablePartesPrincipais')
    if parties_table:
        table_rows = parties_table.find_all('tr')
        for row in table_rows:
            row_cells = row.find_all('td')
            if len(row_cells) >= 2:
                type_cell = row_cells[0]
                type_span = type_cell.find('span', class_='mensagemExibindo tipoDeParticipacao')
                if type_span:
                    party_type = type_span.get_text(strip=True).replace('&nbsp;', '').strip()
                    
                    info_cell = row_cells[1]
                    complete_text = info_cell.get_text(separator='\n', strip=True)
                    text_lines = [line.strip() for line in complete_text.split('\n') if line.strip()]
                    
                    party_name = ''
                    attorney_name = ''
                    
                    for i, line in enumerate(text_lines):
                        if not party_name and line and 'Advogado:' not in line:
                            party_name = line
                        
                        if 'Advogado:' in line:
                            if line.replace('Advogado:', '').strip():
                                attorney_name = line.replace('Advogado:', '').strip()
                            elif i + 1 < len(text_lines):
                                attorney_name = text_lines[i + 1]
                            break
                    
                    if party_name and party_type in ['Autor', 'Réu']:
                        party_entry = f'{party_type}: {party_name}'
                        
                        if attorney_name:
                            party_entry += f'\nAdvogado: {attorney_name}'
                        
                        parties_list.append(party_entry)
    
    return parties_list


def extract_class_history(html_content):
    """Extract class history information"""
    document_parser = BeautifulSoup(html_content, 'html.parser')
    history_entries = []
    
    data_tables = document_parser.find_all('table')
    
    for table in data_tables:
        table_headers = table.find_all('th')
        if len(table_headers) >= 5:
            header_texts = [th.get_text(strip=True) for th in table_headers]
            if 'Data' in header_texts and 'Tipo' in header_texts and 'Classe' in header_texts:
                table_rows = table.find_all('tr')
                
                for row in table_rows:
                    row_cells = row.find_all('td')
                    if len(row_cells) >= 5:
                        entry_date = row_cells[0].get_text(strip=True)
                        entry_type = row_cells[1].get_text(strip=True)
                        entry_class = row_cells[2].get_text(strip=True)
                        entry_area = row_cells[3].get_text(strip=True)
                        entry_reason = row_cells[4].get_text(strip=True)
                        
                        if entry_date and re.match(r'^\d{2}/\d{2}/\d{4}$', entry_date):
                            history_line = f'{entry_date} - {entry_type} - {entry_class} - {entry_area}'
                            if entry_reason and entry_reason != '-':
                                history_line += f' - {entry_reason}'
                            history_entries.append(history_line)
                break
    
    return history_entries


def format_tjac_data(extracted_text, html_content):
    """Format extracted TJAC data"""
    
    output_sections = []
    output_sections.append('Dados da Capa do Processo:')
    document_parser = BeautifulSoup(html_content, 'html.parser')
    process_number_element = document_parser.find('span', id='numeroProcesso')
    if process_number_element:
        process_number = process_number_element.get_text(strip=True)
        output_sections.append(f'Número do Processo: {process_number}')
        
        header_fields = [
            'Classe', 'Assunto', 'Foro', 'Vara', 'Juiz',
            'Distribuição', 'Controle', 'Área', 'Valor da ação', 'Outros assuntos'
        ]
        
        for i, field in enumerate(header_fields):
            if field in extracted_text:
                start_position = extracted_text.find(field) + len(field)
                end_position = len(extracted_text)
                
                for j in range(i + 1, len(header_fields)):
                    next_field = header_fields[j]
                    field_position = extracted_text.find(next_field, start_position)
                    if field_position > start_position and field_position < end_position:
                        end_position = field_position
                        break
                
                if end_position == len(extracted_text):
                    section_markers = ['\nMenu e-SAJ', '\nPartes do processo', '\nMovimentações', '\nRecolher', '\nMais']
                    for marker in section_markers:
                        marker_position = extracted_text.find(marker, start_position)
                        if marker_position > start_position and marker_position < end_position:
                            end_position = marker_position
                
                field_value = extracted_text[start_position:end_position].strip()
                field_value = re.sub(r'\s+', ' ', field_value).replace('\n', ' ').strip()
                
                cleanup_markers = ['Recolher', 'Mais', 'Menu e-SAJ']
                for marker in cleanup_markers:
                    if field_value.endswith(marker):
                        field_value = field_value[:-len(marker)].strip()
                
                if field_value:
                    output_sections.append(f'{field}: {field_value}')
    
    process_parties = extract_process_parties(html_content)
    if process_parties:
        output_sections.append('\nPartes do processo:')
        output_sections.extend(process_parties)
    else:
        if 'Partes do processo' in extracted_text:
            output_sections.append('\nPartes do processo:')
            
            parties_start = extracted_text.find('Partes do processo')
            parties_end = extracted_text.find('Movimentações', parties_start)
            if parties_end == -1:
                parties_end = len(extracted_text)
            
            parties_section = extracted_text[parties_start:parties_end]
            
            if 'Autor' in parties_section:
                section_lines = parties_section.split('\n')
                for i, line in enumerate(section_lines):
                    if line.strip().startswith('Autor') and '\t' in line:
                        line_parts = line.split('\t', 1)
                        if len(line_parts) > 1:
                            author_name = line_parts[1].strip()
                            author_entry = f'Autor: {author_name}'
                            
                            if i + 1 < len(section_lines) and 'Advogado:' in section_lines[i + 1]:
                                attorney = section_lines[i + 1].replace('Advogado:', '').strip()
                                author_entry += f'\nAdvogado: {attorney}'
                            
                            output_sections.append(author_entry)
                            break
            
            if 'Réu' in parties_section:
                section_lines = parties_section.split('\n')
                for line in section_lines:
                    if line.strip().startswith('Réu') and '\t' in line:
                        line_parts = line.split('\t', 1)
                        if len(line_parts) > 1:
                            defendant_name = line_parts[1].strip()
                            output_sections.append(f'Réu: {defendant_name}')
                            break
    
    if 'Movimentações' in extracted_text:
        output_sections.append('\nMovimentações (Data / Movimento):')
        
        movements_start = extracted_text.find('Movimentações')
        movements_end = len(extracted_text)
        end_markers = ['Petições diversas', 'Incidentes, ações', 'Apensos,', 'Audiências', 'Histórico de classes']
        for marker in end_markers:
            marker_position = extracted_text.find(marker, movements_start)
            if marker_position > movements_start and marker_position < movements_end:
                movements_end = marker_position
        
        movements_section = extracted_text[movements_start:movements_end]
        movements_section = movements_section.replace('Data\t \tMovimento', '').replace('Movimentações', '')
        
        section_lines = movements_section.split('\n')
        current_movement = ''
        
        for line in section_lines:
            line = line.strip()
            if not line:
                continue
                
            if re.match(r'^\d{2}/\d{2}/\d{4}', line):
                if current_movement:
                    output_sections.append(current_movement)
                
                line_parts = line.split('\t', 2)
                movement_date = line_parts[0].strip()
                movement_description = '\t'.join(line_parts[1:]).strip() if len(line_parts) > 1 else ''
                current_movement = f'{movement_date} - {movement_description}'
            else:
                if current_movement and line:
                    current_movement += f'\n{line}'
        
        if current_movement:
            output_sections.append(current_movement)
    
    class_history = extract_class_history(html_content)
    if class_history:
        output_sections.append('\nHistórico de classes:')
        output_sections.extend(class_history)
    
    return {'movimentos_processo': '\n'.join(output_sections).replace('\n', ' ')}


def tjac(process_number):
    """
    Consulta processo no TJAC
    
    Args:
        process_number (str): Número do processo no formato CNJ
        
    Returns:
        str: Dados do processo formatados
    """
    
    http_session = Session()
    
    browser_headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'pt-BR,pt;q=0.9',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
    }

    initial_response = http_session.get('https://esaj.tjac.jus.br/cpopg/open.do', headers=browser_headers)
    
    if initial_response.status_code != 200:
        http_session.close()
        return {'erro': f'Erro ao acessar página inicial: {initial_response.status_code}'}
    
    if 'jsessionid=' not in initial_response.text:
        http_session.close()
        return {'erro': 'Erro: Não foi possível obter o JSESSIONID'}

    unified_number_part = process_number.rsplit('.', 2)[0]
    court_number_part = process_number.split('.')[-1]
    
    search_parameters = {
        'conversationId': '',
        'cbPesquisa': 'NUMPROC',
        'numeroDigitoAnoUnificado': unified_number_part,
        'foroNumeroUnificado': court_number_part,
        'dadosConsulta.valorConsultaNuUnificado': [process_number, 'UNIFICADO'],
        'dadosConsulta.valorConsulta': '',
        'dadosConsulta.tipoNuProcesso': 'UNIFICADO',
    }
    
    sleep(0.5)
    
    search_response = http_session.get(
        'https://esaj.tjac.jus.br/cpopg/search.do',
        params=search_parameters,
        headers=browser_headers,
        allow_redirects=False
    )
    
    if search_response.status_code == 302:
        redirect_location = search_response.headers.get('location', '')
        
        if '/cpopg/show.do?' in redirect_location:
            details_url = 'https://esaj.tjac.jus.br' + redirect_location if redirect_location.startswith('/') else redirect_location
            
            sleep(0.5)
            
            details_response = http_session.get(details_url, headers=browser_headers)
            
            if details_response.status_code == 200:
                extracted_text = extract_clean_text(details_response.text)
                formatted_result = format_tjac_data(extracted_text, details_response.text)
                
                http_session.close()
                return formatted_result
            else:
                http_session.close()
                return {'erro': f'Erro ao acessar dados do processo: {details_response.status_code}'}
        else:
            http_session.close()
            return {'erro': 'Erro: Redirecionamento inesperado'}
    else:
        http_session.close()
        return {'erro': f'Erro na consulta: {search_response.status_code}'}