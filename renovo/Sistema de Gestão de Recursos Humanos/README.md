# Sistema de Gestão de RH - RENOVO Montagens Industriais

Sistema completo para gestão de recursos humanos desenvolvido com Python e Flet.

## 🚀 Funcionalidades

### Gestão de Colaboradores
- ✅ Cadastro completo com todos os campos solicitados
- ✅ Foto do colaborador
- ✅ Edição e exclusão
- ✅ Pesquisa por nome ou CPF
- ✅ Lista de colaboradores cadastrados
- ✅ Duplo clique abre a ficha completa

### Ficha de Registro (PDF)
- ✅ Geração de PDF profissional com layout RENOVO
- ✅ Código do documento: FREG-RH-0001
- ✅ Todas as informações do colaborador
- ✅ Foto incluída no PDF

### Contratos de Experiência
- ✅ Controle de prazo inicial e prorrogação
- ✅ Alerta 5 dias antes do vencimento
- ✅ Status do contrato (Vigente/Vencido)

### Gestão de Férias
- ✅ Período aquisitivo e concessivo
- ✅ Fracionamento de férias
- ✅ Abono pecuniário (venda de 10 dias)
- ✅ Alerta 6 meses antes do vencimento

### Aniversariantes
- ✅ Lista de aniversariantes do mês
- ✅ Exportação para Excel

### Block-List
- ✅ Histórico de ex-colaboradores
- ✅ Verificação automática por CPF ao cadastrar
- ✅ Motivo de desligamento e observações
- ✅ Indicação se pode recontratar

### Empresas
- ✅ Cadastro de múltiplas empresas contratantes
- ✅ Vinculação de colaboradores às empresas

### Exportações
- ✅ Excel com lista de colaboradores
- ✅ Excel de contratos vencendo
- ✅ Excel de férias vencendo
- ✅ Excel de aniversariantes

### Backup
- ✅ Backup automático do banco de dados
- ✅ Mantém últimos 10 backups

## 📦 Instalação

1. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

2. **Execute a aplicação:**
```bash
# Desktop
flet run app.py

# Web (navegador)
flet run app.py --web --port 8080
```

## 📁 Estrutura do Projeto

```
rh_system/
├── app.py                  # Aplicação principal
├── main.py                 # Componentes e utilitários
├── database.py             # Módulo de banco de dados (SQLite)
├── formulario_cadastro.py  # Formulário de cadastro
├── pdf_generator.py        # Geração de PDF
├── excel_export.py         # Exportação Excel
├── requirements.txt        # Dependências
├── rh_database.db         # Banco de dados (criado automaticamente)
├── backups/               # Backups do banco
├── exports/               # Arquivos exportados (PDF, Excel)
└── photos/                # Fotos dos colaboradores
```

## 🖥️ Interface

### Menu Lateral
- **Colaboradores**: Lista todos os colaboradores ativos
- **Novo Colaborador**: Formulário de cadastro
- **Contratos Exp.**: Contratos de experiência vencendo
- **Férias**: Períodos de férias a vencer
- **Aniversariantes**: Aniversariantes do mês
- **Block-List**: Histórico de ex-colaboradores
- **Empresas**: Gestão de empresas contratantes
- **Exportar Excel**: Exporta lista de colaboradores
- **Backup**: Realiza backup do banco

### Alertas
O sistema exibe alertas automáticos na tela inicial para:
- Contratos de experiência próximos do vencimento (5 dias)
- Férias com período concessivo vencendo (6 meses)

## 📋 Campos do Cadastro

### Dados Pessoais
- Foto, Nome Completo, Endereço completo
- Data de Nascimento, Naturalidade, Sexo
- Estado Civil, Cônjuge, Deficiência
- Filiação (Mãe e Pai com CPF)
- Grau de Instrução, Curso, Contato

### Documentos
- CPF, RG, CTPS (Carteira de Trabalho)
- Título de Eleitor, CNH, PIS
- Reservista, Conselho Regional
- Exame Médico (ASO)

### Último Emprego
- Empresa anterior, CNPJ
- Datas de admissão e saída
- Primeiro registro, Contribuição sindical

### Dados do Contrato
- Data de Admissão, Função, Departamento
- Salário, Forma de Pagamento
- Prazo de Experiência e Prorrogação
- Horário de Trabalho, Intervalos
- Tipo de Contrato

### Benefícios
- Vale Transporte, Refeição, Alimentação
- Assistência Médica e Odontológica
- Seguro de Vida, Adiantamento

### Dados Bancários
- Tipo de Conta, Banco, Agência, Conta

### Dependentes
- Nome, Parentesco, Data de Nascimento, CPF

## 🛠️ Tecnologias

- **Python 3.10+**
- **Flet** - Interface gráfica multiplataforma
- **SQLite** - Banco de dados
- **ReportLab** - Geração de PDF
- **OpenPyXL** - Exportação Excel

## 📄 Licença

Desenvolvido para RENOVO Montagens Industriais.

---

© 2025 RENOVO Montagens Industriais - Todos os direitos reservados.
