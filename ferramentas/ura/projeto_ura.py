"""Tarefas locais do projeto URA: gerar, comparar e verificar ambiente."""
from pathlib import Path
from datetime import datetime
from collections import Counter
import argparse
import hashlib
import json
import sys
from lxml import etree as E
from ura.gerar_xml_catalogo import Conversor
from ura.comparar_xml_ura import normalizar

ROOT = Path(__file__).resolve().parents[2]
FONTE = ROOT / 'Fonte' / 'PASCHOALOTTO-INSTITUCIONAL.xml'
REFERENCIA = ROOT / 'Referencia' / 'PASCHOALOTTO-INSTITUCIONAL.xml'
GERADO = ROOT / 'Gerado'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ler(path):
    return E.parse(str(path), E.XMLParser(resolve_entities=False, no_network=True)).getroot()


def verificar_referencias(raiz):
    beans = [x for x in raiz if x.tag == 'bean']
    ids = [x.get('id') for x in beans]
    if len(ids) != len(set(ids)):
        raise ValueError('IDs de beans duplicados')
    for bean in raiz.iter('bean'):
        if bean.get('parent') and bean.get('parent') not in ids:
            raise ValueError('Parent inexistente: ' + bean.get('parent'))
    for propriedade in raiz.iter('property'):
        if propriedade.get('ref') and propriedade.get('ref') != 'catalogFactory' and propriedade.get('ref') not in ids:
            raise ValueError('Referencia inexistente: ' + propriedade.get('ref'))


def comparar(path):
    return normalizar(ler(REFERENCIA)) == normalizar(ler(path))


def gerar():
    conversor = Conversor(FONTE)
    raiz = conversor.gerar()
    verificar_referencias(raiz)
    dados = E.tostring(raiz, encoding='ISO-8859-1', xml_declaration=True,
        pretty_print=True, doctype='<!DOCTYPE beans PUBLIC "-//SPRING//DTD BEAN//EN" "http://www.springframework.org/dtd/spring-beans-2.0.dtd">')
    E.fromstring(dados, E.XMLParser(resolve_entities=False, no_network=True))
    GERADO.mkdir(exist_ok=True)
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    nome = conversor.catalogo + '-' + stamp + '.xml'
    destino = GERADO / nome
    with destino.open('xb') as stream:
        stream.write(dados)
    igual = comparar(destino)
    contagem = Counter(x.get('parent') for x in raiz.iter('bean'))
    manifesto = {
        'arquivo': nome,
        'data_geracao_local': stamp,
        'fonte_sha256': sha(FONTE),
        'referencia_sha256': sha(REFERENCIA),
        'gerado_sha256': sha(destino),
        'servicos': len(conversor.raizes),
        'definicoes_comandos': len(conversor.definicoes),
        'chamadas': len(conversor.chamadas),
        'switches': contagem['switch'],
        'cases': contagem['case'],
        'whiles': contagem['while'],
        'igual_referencia_na_comparacao_estrutural': igual,
        'executado_no_motor_ura': False,
    }
    texto = json.dumps(manifesto, ensure_ascii=True, indent=2) + '\n'
    with destino.with_suffix('.relatorio.json').open('x', encoding='utf-8') as stream:
        stream.write(texto)
    (GERADO / 'ultima-geracao.json').write_text(texto, encoding='utf-8')
    print('GERACAO CONCLUIDA: ' + str(destino))
    print(f'Servicos: {len(conversor.raizes)} | Comandos: {len(conversor.definicoes)} | Chamadas: {len(conversor.chamadas)}')
    print('Comparacao com referencia: ' + ('IGUAL' if igual else 'DIFERENTE'))
    if not igual:
        print('A fonte tem diferencas da referencia. Revise no VS Code; isso nao impede gerar alteracoes intencionais.')
    print('Geracao local; nao houve importacao, publicacao ou execucao na URA.')
    return 0


def comparar_ultima():
    manifesto = json.loads((GERADO / 'ultima-geracao.json').read_text(encoding='utf-8'))
    nome = manifesto['arquivo']
    if Path(nome).name != nome:
        raise ValueError('Nome de arquivo invalido no manifesto')
    destino = GERADO / nome
    if sha(destino) != manifesto['gerado_sha256']:
        raise ValueError('O XML foi alterado apos a geracao. Gere novamente antes de comparar.')
    igual = comparar(destino)
    print('Arquivo: ' + str(destino))
    print('Comparacao estrutural com referencia: ' + ('IGUAL' if igual else 'DIFERENTE'))
    if sha(FONTE) != manifesto['fonte_sha256']:
        print('ATENCAO: a Fonte mudou desde a ultima geracao; o XML comparado representa a versao anterior.')
    return 0 if igual else 1


def verificar():
    import lxml
    print('Python: ' + sys.executable)
    print('Versao Python: ' + sys.version.split()[0])
    print('lxml: ' + lxml.__version__)
    for path in [FONTE, REFERENCIA]:
        if not path.is_file():
            raise FileNotFoundError(path)
        print('Arquivo encontrado: ' + str(path))
    print('Ambiente pronto para gerar.')
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('acao', choices=['gerar', 'comparar', 'verificar'])
    acao = parser.parse_args().acao
    try:
        return {'gerar': gerar, 'comparar': comparar_ultima, 'verificar': verificar}[acao]()
    except (ValueError, OSError, E.XMLSyntaxError) as exc:
        print('ERRO: ' + str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())