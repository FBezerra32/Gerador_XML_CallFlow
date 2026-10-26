"""Compara XMLs executaveis ignorando formatacao e ordem de propriedades."""
import argparse
from lxml import etree as E


def normalizar(no):
    filhos = [x for x in no if isinstance(x.tag, str)]
    if no.tag == 'beans':
        filhos.sort(key=lambda x: x.get('id', ''))
    elif no.tag == 'bean':
        filhos.sort(key=lambda x: (x.tag, x.get('name', '')))
    return (no.tag, tuple(sorted(no.attrib.items())),
            (no.text or '') if no.tag == 'value' else '',
            tuple(normalizar(x) for x in filhos))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('referencia')
    parser.add_argument('gerado')
    args = parser.parse_args()
    xml_parser = E.XMLParser(resolve_entities=False, no_network=True)
    referencia = E.parse(args.referencia, xml_parser).getroot()
    gerado = E.parse(args.gerado, xml_parser).getroot()
    if normalizar(referencia) != normalizar(gerado):
        parser.exit(1, 'DIFERENTES: ha divergencias alem da formatacao/ordenacao permitida.\n')
    print('IGUAIS na comparacao estrutural: servicos, comandos, propriedades, valores, scripts e ordem de execucao.')


if __name__ == '__main__':
    main()