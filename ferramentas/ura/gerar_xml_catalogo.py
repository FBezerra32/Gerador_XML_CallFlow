"""Converte o formato de catalogo Opus observado em XML Spring para a URA.

Uso: python gerar_xml_catalogo.py FONTE.xml SAIDA.xml
Dependencia: lxml. Nao acessa rede, nao importa no editor e nao publica na URA.
Formatos/comandos desconhecidos interrompem a geracao.
"""
from pathlib import Path
from lxml import etree as E
import argparse

ARVORE = 'br.com.opuscom.ibank.entity.ArvoreServico'
PARAMETRO = 'br.com.opuscom.ibank.entity.ParametrosComando'
WRAPPER = 'br.com.opuscom.ibank.business.transacional.ExportadorImportadorServicos_-ProjetoExportacaoWrapper'
CHAIN = 'opuscom.commons.chain.js.JavascriptChain'


class Conversor:
    def __init__(self, fonte):
        parser = E.XMLParser(encoding='ISO-8859-1', resolve_entities=False, no_network=True)
        self.tree = E.parse(str(fonte), parser)
        if self.tree.getroot().tag != WRAPPER:
            raise ValueError('Formato de catalogo nao suportado')
        self.raizes = list(self.tree.getroot().find('arvoreServicosRaiz'))
        self.raiz_set = set(self.raizes)
        self.catalogos = {self.qualificado(self.resolver(x.find('servico'))).split('.')[0] for x in self.raizes}
        if len(self.catalogos) != 1:
            raise ValueError('Esperado um unico catalogo')
        self.catalogo = next(iter(self.catalogos))
        self.definicoes = {}
        self.ids_servicos = {self.qualificado(self.resolver(x.find('servico'))) for x in self.raizes}
        self.chamadas = []

    def resolver(self, node):
        vistos = set()
        while node is not None and node.get('reference'):
            if node in vistos:
                raise ValueError('Referencia ciclica')
            vistos.add(node)
            resultado = node.xpath(node.get('reference'))
            if len(resultado) != 1:
                raise ValueError('Referencia nao resolvida: ' + node.get('reference'))
            node = resultado[0]
        return node

    def qualificado(self, servico):
        pasta = self.resolver(servico.find('pasta'))
        partes = pasta.findtext('path').split('/')
        if len(partes) < 2:
            raise ValueError('Caminho de pasta invalido')
        return '.'.join(partes[1:] + [servico.findtext('nome')])

    def dono(self, node):
        while node is not None and node not in self.raiz_set:
            node = node.getparent()
        if node is None:
            raise ValueError('Comando sem servico de origem')
        return self.resolver(node.find('servico'))

    def filhos(self, node):
        grupo = node.find('arvoreServicoFilhos')
        return sorted(list(grupo) if grupo is not None else [], key=lambda x: int(x.findtext('icOrdem', '0')))

    def propriedade(self, bean, nome, texto):
        propriedade = E.SubElement(bean, 'property', name=nome)
        E.SubElement(propriedade, 'value').text = E.CDATA(texto)

    def lista(self, bean, filhos):
        lista = E.SubElement(E.SubElement(bean, 'constructor-arg'), 'list')
        for filho in filhos:
            lista.append(self.converter_no(filho))

    def converter_no(self, node):
        comando = self.resolver(node.find('comando'))
        if comando is None:
            raise ValueError('No sem comando')
        classe = comando.get('class', '')
        nome = comando.findtext('nome')
        filhos = self.filhos(node)
        if classe.endswith('.ComandoSwitchCase'):
            tipo = comando.findtext('tipoSwitchCase')
            if nome == 'BeginService':
                bean = E.Element('bean', id=self.qualificado(self.resolver(node.find('servico'))), parent='workflow')
                self.lista(bean, filhos)
            elif tipo == '0' and nome == 'switch':
                bean = E.Element('bean', parent='switch')
                self.lista(bean, filhos)
                self.propriedade(bean, 'switchExpression', comando.findtext('valor', ''))
            elif tipo == '1' and nome == 'case':
                bean = E.Element('bean', parent='case')
                self.lista(bean, filhos)
                self.propriedade(bean, 'case', comando.findtext('valor', ''))
            elif tipo == '2' and nome == 'default':
                bean = E.Element('bean', parent='default')
                self.lista(bean, filhos)
            elif tipo == '3' and nome == 'while':
                bean = E.Element('bean', parent='while')
                self.propriedade(bean, 'whileExpression', comando.findtext('valor', ''))
                self.lista(bean, filhos)
            else:
                raise ValueError('Controle desconhecido: ' + str((nome, tipo)))
            return bean
        if classe.endswith('.ComandoCallServico'):
            if filhos:
                raise ValueError('Chamada com filhos nao suportada')
            tipo = comando.findtext('tipoLocalRemoto')
            if tipo not in ['0', '2']:
                raise ValueError('Chamada remota/multifuncao nao suportada: ' + str(tipo))
            destino = self.resolver(comando.find('servicoLocal'))
            if destino is None:
                raise ValueError('Servico chamado ausente na exportacao')
            nome_destino = self.qualificado(destino)
            self.chamadas.append(nome_destino)
            bean = E.Element('bean', parent='execute' if tipo == '0' else 'exception')
            E.SubElement(bean, 'property', name='name', value=nome_destino)
            E.SubElement(bean, 'property', name='catalogName', value=self.catalogo)
            return bean
        if classe:
            raise ValueError('Classe de comando desconhecida: ' + classe)
        if filhos:
            raise ValueError('Comando simples com filhos nao suportado')
        classe_java = comando.findtext('className')
        if not classe_java:
            raise ValueError('Comando sem className: ' + str(nome))
        escopo = self.qualificado(self.dono(comando)).rsplit('.', 1)[0]
        parent = escopo + '.' + nome
        anterior = self.definicoes.setdefault(parent, classe_java)
        if anterior != classe_java:
            raise ValueError('Definicoes conflitantes: ' + parent)
        bean = E.Element('bean', parent=parent)
        parametros = comando.find('parametrosComandos')
        if parametros is not None:
            for parametro in sorted(list(parametros), key=lambda x: int(x.findtext('icOrdem', '0'))):
                if parametro.tag != PARAMETRO:
                    raise ValueError('Parametro desconhecido: ' + parametro.tag)
                texto = parametro.findtext('valor', '')
                if texto == '':
                    continue
                texto = texto.strip()
                tipo = parametro.findtext('tipoParametro')
                if tipo == '7':
                    if texto not in ['Verdadeiro', 'Falso']:
                        raise ValueError('Booleano desconhecido: ' + texto)
                    texto = 'true' if texto == 'Verdadeiro' else 'false'
                elif tipo not in ['1', '3', '16', '19', '20']:
                    raise ValueError('Tipo de parametro desconhecido: ' + str(tipo))
                self.propriedade(bean, parametro.findtext('nome'), texto)
        return bean

    def gerar(self):
        workflows = [self.converter_no(x) for x in self.raizes]
        ausentes = set(self.chamadas) - self.ids_servicos
        if ausentes:
            raise ValueError('Servicos chamados fora do catalogo: ' + ', '.join(sorted(ausentes)))
        raiz = E.Element('beans', {'default-lazy-init': 'true'})
        for nome in ['workflow', 'switch', 'case', 'default']:
            E.SubElement(raiz, 'bean', id=nome, attrib={'class': CHAIN, 'abstract': 'true'})
        for nome, classe in [('execute', 'org.apache.commons.chain.generic.LookupCommand'),
                             ('executeMultifuncao', 'br.com.dnk.ura.command.impl.ExecuteMultifuncaoCommand'),
                             ('exception', 'opuscom.commons.chain.filter.ExceptionFilter')]:
            bean = E.SubElement(raiz, 'bean', id=nome, attrib={'class': classe, 'abstract': 'true'})
            E.SubElement(bean, 'property', name='catalogFactory', ref='catalogFactory')
            E.SubElement(bean, 'property', name='catalogName', value=self.catalogo)
        E.SubElement(raiz, 'bean', id='servicoRemoto', attrib={'class': 'opusibank.client.command.RemoteServiceCommand', 'abstract': 'true'})
        E.SubElement(raiz, 'bean', id='while', attrib={'class': CHAIN, 'abstract': 'true'})
        for nome, classe in sorted(self.definicoes.items()):
            E.SubElement(raiz, 'bean', id=nome, attrib={'class': classe, 'abstract': 'true'})
        for workflow in sorted(workflows, key=lambda x: x.get('id')):
            raiz.append(workflow)
        return raiz


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('fonte', type=Path)
    parser.add_argument('saida', type=Path)
    args = parser.parse_args()
    if args.saida.exists():
        parser.error('A saida ja existe. Use um novo nome para preservar arquivos.')
    conversor = Conversor(args.fonte)
    raiz = conversor.gerar()
    dados = E.tostring(raiz, encoding='ISO-8859-1', xml_declaration=True, pretty_print=True,
        doctype='<!DOCTYPE beans PUBLIC "-//SPRING//DTD BEAN//EN" "http://www.springframework.org/dtd/spring-beans-2.0.dtd">')
    E.fromstring(dados, E.XMLParser(resolve_entities=False, no_network=True))
    args.saida.write_bytes(dados)
    print(f'Gerados {len(conversor.raizes)} servicos, {len(conversor.definicoes)} comandos e {len(conversor.chamadas)} chamadas.')


if __name__ == '__main__':
    main()