# Projeto URA no VS Code

## Uso diario

1. Abra esta pasta inteira no VS Code (Arquivo > Abrir Pasta).
2. Edite o catalogo em Fonte/PASCHOALOTTO-INSTITUCIONAL.xml e salve (Ctrl+S).
3. Pressione Ctrl+Shift+B para executar **URA: Gerar XML**.
4. Confira o terminal: GERACAO CONCLUIDA e o caminho do arquivo.
5. O novo XML aparece em Gerado/, com data, hora e microssegundos no nome.

Cada geracao cria um arquivo novo. Nada e publicado ou enviado para a URA automaticamente.
Se o VS Code solicitar confianca na pasta, revise o projeto e confirme voce mesmo para permitir tarefas locais.

## Executar sem VS Code

No Windows, abra a pasta do projeto no Explorador de Arquivos e clique duas vezes em `Gerar XML.bat`. O XML e o relatorio serao criados em `Gerado/`, e a janela mostrara o resultado. O atalho usa o Python configurado nesta maquina ou, se ele nao estiver disponivel, tenta o launcher `py -3`. A execucao continua sendo local; nada e enviado ao Callflow automaticamente.

## Tarefas disponiveis

Pelo menu Terminal > Executar Tarefa:

- **URA: Gerar XML**: converte a Fonte, valida XML/referencias, cria arquivo versionado e compara com Referencia. E a tarefa padrao do Ctrl+Shift+B.
- **URA: Comparar ultima geracao**: confere novamente a equivalencia estrutural e retorna erro de tarefa se forem diferentes. Se a Fonte mudou desde a geracao, avisa para gerar novamente.
- **URA: Verificar ambiente**: verifica Python, lxml e presenca dos arquivos necessarios.

Na tarefa de geracao, DIFERENTE nao impede criar o XML: depois que voce editar a Fonte, essa diferenca pode ser intencional. Na tarefa exclusiva de comparacao, DIFERENTE retorna codigo 1 para destacar a divergencia. Isso e um resultado da comparacao, nao necessariamente erro da sua alteracao.

Para comparar visualmente: clique com o botao direito no XML de Referencia > Selecionar para Comparacao; depois no XML gerado > Comparar com o Selecionado. A formatacao dos arquivos pode produzir diferencas visuais, mesmo quando a comparacao estrutural retorna IGUAL.

## Organizacao

- Fonte/: catalogo editavel exportado do Opus, preservado durante a configuracao.
- XML/: arquivo original que voce forneceu, preservado.
- Referencia/: copia do XML original usada para comparacao. Atualize apenas quando decidir adotar uma nova referencia.
- Gerado/: XMLs versionados e relatorios de cada geracao. ultima-geracao.json aponta para o resultado mais recente.
- ferramentas/ura/: implementacao organizada do conversor, comparador e tarefas do projeto.
- ferramentas/*.py: entradas de compatibilidade para manter os comandos existentes.
- .vscode/tasks.json: comandos do VS Code.
- .vscode/settings.json: codificacao XML ISO-8859-1 e demais arquivos UTF-8.

## Git e arquivos locais

Os diretorios Fonte/, XML/ e Referencia/ ficam ignorados pelo Git porque os XMLs contem configuracoes de autenticacao. Eles continuam no disco local e sao necessarios para gerar e comparar o XML. Ao clonar este projeto, obtenha esses arquivos por um canal interno autorizado antes de executar o gerador. Nao publique credenciais; se uma credencial real foi exposta, solicite sua revogacao/rotacao ao responsavel pelo sistema.

A Fonte fornecida e ISO-8859-1 sem declaracao XML. O projeto configura essa codificacao para arquivos XML. Evite salvar a Fonte em UTF-8 sem adaptar o conversor. Os XMLs gerados possuem declaracao ISO-8859-1.

## Python configurado

O atalho python.exe do Windows nao estava funcional. As tarefas apontam explicitamente para o Python ja disponivel nesta maquina:

C:/Users/fabio.bezerra/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe

Esse caminho pertence ao runtime local do Codex. Se ele for removido ou se o projeto for levado para outra maquina, instale/configure um Python proprio, instale as dependencias de requirements.txt nesse interpretador e altere o campo command das tres tarefas em .vscode/tasks.json para o caminho do novo python.exe.

Exemplo com o interpretador desejado:

```powershell
& 'C:/caminho/do/python.exe' -m pip install -r requirements.txt
```

Nao e preciso ativar ambiente ou instalar extensao para executar as tarefas atuais. A extensao Python pode ser instalada por voce se desejar ferramentas de edicao/depuracao dos scripts Python.

## Limites

O conversor foi validado para os tipos de comando presentes neste catalogo. Tipos nao reconhecidos, chamadas remotas/multifuncao e referencias ausentes interrompem a geracao. Conteudo omitido pelo exportador Opus nao pode ser recuperado automaticamente.

Os comandos Java/DNK precisam existir no motor da URA. Validacao estrutural e de sintaxe nao substitui homologacao de audio, telefonia, eventos e execucao Java. XML executavel e catalogo Fonte sao formatos diferentes; nao importe o XML gerado como se fosse o catalogo Fonte.

Nesta primeira etapa os JavaScripts continuam dentro do catalogo. A separacao em arquivos .js e uma etapa futura, ainda nao implementada.

## Verificacao da configuracao

Foram executadas as tres tarefas usando os comandos do tasks.json. Duas geracoes criaram saidas distintas, ambas equivalentes estruturalmente a referencia. Os arquivos originais Fonte e XML permaneceram com o mesmo SHA256.
