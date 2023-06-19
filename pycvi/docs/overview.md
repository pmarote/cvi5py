<!-- markdownlint-disable -->

# API Overview

## Modules

- [`sistemas`](./sistemas.md#module-sistemas): Pacote que contém módulos para interagir com os sistemas da Sefaz.
- [`sistemas.arquivosdigitais`](./sistemas.arquivosdigitais.md#module-sistemasarquivosdigitais): Módulo com definições do sistema ArquivosDigitais.
- [`sistemas.base`](./sistemas.base.md#module-sistemasbase): Módulo com definições que servem de base para outros sistemas.
- [`sistemas.cadesp`](./sistemas.cadesp.md#module-sistemascadesp): Módulo com definições do sistema Cadesp.
- [`sistemas.cassacaocontrib`](./sistemas.cassacaocontrib.md#module-sistemascassacaocontrib): Módulo com definições do sistema Cassação de Contribuintes.
- [`sistemas.classificacao`](./sistemas.classificacao.md#module-sistemasclassificacao): Módulo com definições do sistema Classificação de Contribuintes do ICMS.
- [`sistemas.consultasdfe`](./sistemas.consultasdfe.md#module-sistemasconsultasdfe): Módulo com definições do sistema Consultas DFe.
- [`sistemas.contafiscalicms`](./sistemas.contafiscalicms.md#module-sistemascontafiscalicms): Módulo com definições do sistema ContaFiscalICMS.
- [`sistemas.dec`](./sistemas.dec.md#module-sistemasdec): Módulo com definições do sistema Dec.
- [`sistemas.ecredac`](./sistemas.ecredac.md#module-sistemasecredac): Módulo com definições do sistema Ecredac.
- [`sistemas.etc`](./sistemas.etc.md#module-sistemasetc): Módulo com definições do sistema ETC.
- [`sistemas.folha`](./sistemas.folha.md#module-sistemasfolha): Módulo com definições do sistema Folha de Pagamento.
- [`sistemas.launchpad`](./sistemas.launchpad.md#module-sistemaslaunchpad): Módulo com definições do sistema BI LaunchPad.
- [`sistemas.nfe_credenciamento`](./sistemas.nfe_credenciamento.md#module-sistemasnfe_credenciamento): Módulo com definições do sistema NFE - Credenciamento.
- [`sistemas.pfe`](./sistemas.pfe.md#module-sistemaspfe): Módulo com definições do sistema PFE.
- [`sistemas.pgsf`](./sistemas.pgsf.md#module-sistemaspgsf): Módulo com definições do sistema PGSF.
- [`sistemas.pgsf_aiimweb`](./sistemas.pgsf_aiimweb.md#module-sistemaspgsf_aiimweb): Módulo com definições do sistema AIIMWEB.
- [`sistemas.sgipva`](./sistemas.sgipva.md#module-sistemassgipva): Módulo com definições do sistema SGIPVA.
- [`sistemas.sipet`](./sistemas.sipet.md#module-sistemassipet): Módulo com definições do sistema SIPET.
- [`sistemas.sped`](./sistemas.sped.md#module-sistemassped): Módulo com definições do sistema Sped.
- [`sistemas.spsempapel`](./sistemas.spsempapel.md#module-sistemasspsempapel): Módulo com definições do sistema SP Sem Papel.
- [`utils`](./utils.md#module-utils): Pacote que contém funções utilitárias.
- [`utils.cert`](./utils.cert.md#module-utilscert): Módulo com funções utilitárias para trablhar com certificados.
- [`utils.html`](./utils.html.md#module-utilshtml): Módulo com funções utilitárias para manipulação de arquivos HTML.
- [`utils.login`](./utils.login.md#module-utilslogin): Módulo com funções utilitárias para login em sistemas.
- [`utils.pdf`](./utils.pdf.md#module-utilspdf): Módulo com funções utilitárias para manopulação de arquivos PDF.
- [`utils.texto`](./utils.texto.md#module-utilstexto): Módulo com funções utilitárias para manipulação de strings.

## Classes

- [`arquivosdigitais.ArquivosDigitais`](./sistemas.arquivosdigitais.md#class-arquivosdigitais): Representa o sistema [ArquivosDigitais](https://www10.fazenda.sp.gov.br/ArquivosDigitais).
- [`base.AuthenticationError`](./sistemas.base.md#class-authenticationerror): Representa erros de autenticação nos sistemas.
- [`base.Sistema`](./sistemas.base.md#class-sistema): Classe base para sistemas.
- [`cadesp.Cadesp`](./sistemas.cadesp.md#class-cadesp): Representa o sistema [Cadesp](https://www.cadesp.fazenda.sp.gov.br/).
- [`cassacaocontrib.CassacaoContribuintes`](./sistemas.cassacaocontrib.md#class-cassacaocontribuintes): Representa o sistema [Cassação de Contribuintes](https://sefaznet11.intra.fazenda.sp.gov.br/cassacao/).
- [`classificacao.Classificacao`](./sistemas.classificacao.md#class-classificacao): Representa o sistema [Classificação de Contribuintes do ICMS](https://www3.fazenda.sp.gov.br/classificacao/).
- [`consultasdfe.ConsultasDfe`](./sistemas.consultasdfe.md#class-consultasdfe): Representa o sistema [Consultas DFe](https://www3.fazenda.sp.gov.br/One/ConsultaCupons).
- [`contafiscalicms.ContaFiscalICMS`](./sistemas.contafiscalicms.md#class-contafiscalicms): Representa o sistema [ContaFiscalICMS](https://www10.fazenda.sp.gov.br/ContaFiscalICMS/Pages/ContaFiscal.aspx).
- [`contafiscalicms.ContaFiscalICMSException`](./sistemas.contafiscalicms.md#class-contafiscalicmsexception)
- [`dec.Dec`](./sistemas.dec.md#class-dec): Representa o sistema [Dec](https://sefaznet11.intra.fazenda.sp.gov.br/DEC/).
- [`ecredac.Ecredac`](./sistemas.ecredac.md#class-ecredac): Representa o sistema [e-CredAc](https://www.fazenda.sp.gov.br/CreditoAcumulado).
- [`etc.Etc`](./sistemas.etc.md#class-etc): Representa um site de um espaço de trabalho do sistema [ETC](https://etc.intra.fazenda.sp.gov.br/).
- [`folha.FolhaPagamento`](./sistemas.folha.md#class-folhapagamento): Representa o sistema [Folha de Pagamento](https://www.fazenda.sp.gov.br/folha/).
- [`launchpad.LaunchPad`](./sistemas.launchpad.md#class-launchpad): Representa o sistema [BI LaunchPad](https://srvbo-v42.intra.fazenda.sp.gov.br).
- [`nfe_credenciamento.NfeCredenciamento`](./sistemas.nfe_credenciamento.md#class-nfecredenciamento): Representa o sistema [Nfe](https://nfe.fazenda.sp.gov.br/).
- [`pfe.GIARelatorio`](./sistemas.pfe.md#class-giarelatorio): An enumeration.
- [`pfe.GIASubRelatorio`](./sistemas.pfe.md#class-giasubrelatorio): An enumeration.
- [`pfe.Pfe`](./sistemas.pfe.md#class-pfe): Representa o sistema [PFE](https://www3.fazenda.sp.gov.br/CAWeb/pages/Default.aspx).
- [`pgsf.Pgsf`](./sistemas.pgsf.md#class-pgsf): Representa o sistema [Planejamento e Gestão de Serviços Fiscais (PGSF)](https://portal60.sede.fazenda.sp.gov.br/).
- [`pgsf.PgsfSituacaoOSF`](./sistemas.pgsf.md#class-pgsfsituacaoosf): An enumeration.
- [`pgsf_aiimweb.Aiimweb`](./sistemas.pgsf_aiimweb.md#class-aiimweb): Representa o sistema AIIMWEB.
- [`sgipva.Sgipva`](./sistemas.sgipva.md#class-sgipva): Representa o sistema [SGIPVA](https://sefaznet11.intra.fazenda.sp.gov.br/SGIPVAF2/).
- [`sipet.Sipet`](./sistemas.sipet.md#class-sipet): Representa o sistema [SIPET](https://www3.fazenda.sp.gov.br/SIPET).
- [`sped.Sped`](./sistemas.sped.md#class-sped): Representa o sistema [Sped](https://www.fazenda.sp.gov.br/sped).
- [`spsempapel.SpSemPapel`](./sistemas.spsempapel.md#class-spsempapel): Representa o sistema [SP Sem Papel](https://www.documentos.spsempapel.sp.gov.br/).

## Functions

- [`base.preparar_metodo`](./sistemas.base.md#function-preparar_metodo): Decorator que adiciona verificações aos métodos de um sistema.
- [`cert.listar_nomes_certs`](./utils.cert.md#function-listar_nomes_certs): Lista os nomes dos certificados instalados na máquina.
- [`html.converter_para_pdf`](./utils.html.md#function-converter_para_pdf): Converte um arquivo HTML em PDF.
- [`html.extrair_validadores_aspnet`](./utils.html.md#function-extrair_validadores_aspnet): Extrai os validadores de de uma página ASP.NET.
- [`html.find_all_deepest`](./utils.html.md#function-find_all_deepest): Lista todos os elementos de um soup que não possuem o mesmo elemento como descendente.
- [`html.salvar`](./utils.html.md#function-salvar): Salva um arquivo HTML.
- [`html.scrape_tabela`](./utils.html.md#function-scrape_tabela): "Raspa" (scrape) os dados de uma tabela HTML.
- [`login.login_identity_cert`](./utils.login.md#function-login_identity_cert): Realiza o login em um sistema com certificado por meio do Identity.
- [`pdf.dividir_pdf_por_tamanho`](./utils.pdf.md#function-dividir_pdf_por_tamanho): Separa um arquivo PDF em diversos arquivos menores.
- [`pdf.excluir_paginas_do_pdf`](./utils.pdf.md#function-excluir_paginas_do_pdf): Deleta um CONJUNTO DE PÁGINAS de um arquivo PDF.
- [`pdf.juntar_arquivos`](./utils.pdf.md#function-juntar_arquivos): Junta diversos arquivos em um único arquivo PDF.
- [`pdf.parse_pdf`](./utils.pdf.md#function-parse_pdf): Gera uma lista de linhas de texto extraídas de um arquivo PDF.
- [`texto.comparar_textos`](./utils.texto.md#function-comparar_textos): Compara e atribui um valor de similaridade entre dois textos.
- [`texto.formatar_cep`](./utils.texto.md#function-formatar_cep): Formata um número de CEP.
- [`texto.formatar_cnae`](./utils.texto.md#function-formatar_cnae): Formata um número de CNAE.
- [`texto.formatar_cnpj`](./utils.texto.md#function-formatar_cnpj): Formata um número de CNPJ.
- [`texto.formatar_cpf`](./utils.texto.md#function-formatar_cpf): Formata um número de CPF.
- [`texto.formatar_crc`](./utils.texto.md#function-formatar_crc): Formata um número de CRC (Conselho Regional de Contabilidade).
- [`texto.formatar_data`](./utils.texto.md#function-formatar_data): Formata uma data.
- [`texto.formatar_ie`](./utils.texto.md#function-formatar_ie): Formata um número de Inscrição Estadual (IE).
- [`texto.formatar_mes_referencia`](./utils.texto.md#function-formatar_mes_referencia): Formata um mês de referência.
- [`texto.formatar_nire`](./utils.texto.md#function-formatar_nire): Formata um número de NIRE.
- [`texto.formatar_osf`](./utils.texto.md#function-formatar_osf): Formata um número de OSF.
- [`texto.formatar_sigla_sempapel`](./utils.texto.md#function-formatar_sigla_sempapel): Formata uma sigla (não temporária) de um documento do SpSemPapel.
- [`texto.formatar_sigla_temp_sempapel`](./utils.texto.md#function-formatar_sigla_temp_sempapel): Formata uma sigla temporária de um documento do SpSemPapel.
- [`texto.formatar_usuario_sempapel`](./utils.texto.md#function-formatar_usuario_sempapel): Formata uma identificador de usuário do SpSemPapel.
- [`texto.limpar_texto`](./utils.texto.md#function-limpar_texto): Remove caracteres não imprimíveis de um texto, mantendo os espaços.


---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
