
from crawlers.trf3 import trf3
from crawlers.trf4 import trf4
from crawlers.tjac import tjac



class TribunaisHandlers:

    CODIGOS_TRIBUNAIS = {
        "4.03": trf3, 
        "4.04": trf4,
        "8.01": tjac
    }

    def __init__(self):
        pass

    def codigo_tribunal(self, num_cnj) -> str:
        """
        Extrai do número do processo no formato CNJ 
        o código do Tribunal ao qual ele pertencem.
        """
        chunks = num_cnj.split('.')
        codigo = f"{chunks[2]}.{chunks[3]}"
        return codigo

    def identificar_tribunal(self, codigo: str) -> str:
        """
        Identifica a qual tribunal pertencente o número do processo passado como 
        argumento do método. Se não for identificado o Tribunal, é lançado um erro. 
        Caso contrário, retorna o objeto do Tribunal correspondente.
        """
        tribunal = TribunaisHandlers.CODIGOS_TRIBUNAIS.get(codigo, '')
        if not tribunal:
            raise Exception('Tribunal não identificado!')
        return tribunal

    def consultar(self, num_cnj: str):
        """
        Identifica a qual tribunal pertencente o número do processo passado
        como argumento do método e chama o respectivo módulo de consulta.
        """
        codigo = self.codigo_tribunal(num_cnj)
        
        tribunal = self.identificar_tribunal(codigo)
        
        if isinstance(tribunal, str):
            return f"O Tribunal {tribunal} ainda não possui automação para consulta."
        movimentos_processuais = tribunal(num_cnj)
        
        return movimentos_processuais
