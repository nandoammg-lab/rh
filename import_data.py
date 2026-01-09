"""
Script de importacao de dados do banco SQLite original para MySQL
"""
import os
import sys
import sqlite3
from datetime import datetime
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.contrib.auth.models import User
from colaboradores.models import (
    Empresa, Colaborador, Dependente, Localizacao, Ferias, PeriodoFerias,
    ContratoExperiencia, Blocklist, Configuracao, HistoricoAlteracao,
    DocumentoColaborador, LogSistema
)

# Caminho do banco SQLite original
SQLITE_DB = r'c:\Users\Fernando\Documents\renovo\Sistema de Gestão de Recursos Humanos\rh_database.db'


def get_sqlite_connection():
    conn = sqlite3.connect(SQLITE_DB)
    conn.row_factory = sqlite3.Row
    return conn


def parse_date(value):
    """Converte string de data para objeto date"""
    if not value:
        return None
    try:
        if isinstance(value, str):
            # Tentar diferentes formatos
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S']:
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue
        return value
    except:
        return None


def parse_datetime(value):
    """Converte string de datetime para objeto datetime"""
    if not value:
        return None
    try:
        if isinstance(value, str):
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d']:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
        return value
    except:
        return None


def parse_decimal(value):
    """Converte valor para Decimal"""
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except:
        return None


def parse_bool(value):
    """Converte valor para boolean"""
    if value is None:
        return False
    return bool(value)


def import_empresas(cursor):
    """Importa empresas"""
    print("\n=== Importando Empresas ===")
    cursor.execute("SELECT * FROM empresas")
    rows = cursor.fetchall()

    for row in rows:
        empresa, created = Empresa.objects.update_or_create(
            id=row['id'],
            defaults={
                'razao_social': row['razao_social'] or '',
                'cnpj': row['cnpj'] or '',
                'endereco': row['endereco'],
                'numero': row['numero'],
                'complemento': row['complemento'],
                'bairro': row['bairro'],
                'cep': row['cep'],
                'cidade': row['cidade'],
                'uf': row['uf'],
                'telefone': row['telefone'],
                'email': row['email'],
                'ativa': parse_bool(row['ativa']) if 'ativa' in row.keys() else True,
            }
        )
        action = "Criada" if created else "Atualizada"
        print(f"  {action}: {empresa.razao_social}")

    print(f"  Total: {len(rows)} empresas")


def import_colaboradores(cursor):
    """Importa colaboradores"""
    print("\n=== Importando Colaboradores ===")
    cursor.execute("SELECT * FROM colaboradores")
    rows = cursor.fetchall()

    for row in rows:
        # Mapear campos
        data = {
            'nome_completo': row['nome_completo'] or '',
            'endereco': row['endereco'],
            'numero': row['numero'],
            'complemento': row['complemento'],
            'bairro': row['bairro'],
            'cep': row['cep'],
            'cidade': row['cidade'],
            'uf_endereco': row['uf_endereco'],
            'telefone': row['telefone'],
            'celular': row['celular'],
            'email': row['email'],
            'data_nascimento': parse_date(row['data_nascimento']),
            'naturalidade': row['naturalidade'],
            'uf_naturalidade': row['uf_naturalidade'],
            'sexo': row['sexo'],
            'grau_instrucao': row['grau_instrucao'],
            'curso_formacao': row['curso_formacao'],
            'data_conclusao': parse_date(row['data_conclusao']),
            'estado_civil': row['estado_civil'],
            'data_casamento': parse_date(row['data_casamento']),
            'nome_conjuge': row['nome_conjuge'],
            'deficiencia': row['deficiencia'],
            'nome_mae': row['nome_mae'],
            'cpf_mae': row['cpf_mae'],
            'nome_pai': row['nome_pai'],
            'cpf_pai': row['cpf_pai'],
            # Documentos
            'carteira_profissional': row['carteira_profissional'],
            'serie_carteira': row['serie_carteira'],
            'uf_carteira': row['uf_carteira'],
            'data_emissao_carteira': parse_date(row['data_emissao_carteira']),
            'rg': row['rg'],
            'data_emissao_rg': parse_date(row['data_emissao_rg']),
            'orgao_emissor_rg': row['orgao_emissor_rg'],
            'uf_rg': row['uf_rg'],
            'cpf': row['cpf'] or f'TEMP_{row["id"]}',
            'titulo_eleitor': row['titulo_eleitor'],
            'zona_eleitor': row['zona_eleitor'],
            'secao_eleitor': row['secao_eleitor'],
            'habilitacao': row['habilitacao'],
            'data_expedicao_cnh': parse_date(row['data_expedicao_cnh']),
            'tipo_cnh': row['tipo_cnh'],
            'validade_cnh': parse_date(row['validade_cnh']),
            'pis': row['pis'],
            'data_cadastramento_pis': parse_date(row['data_cadastramento_pis']),
            'reservista': row['reservista'],
            # Conselho Regional
            'conselho_regional': row['conselho_regional'],
            'sigla_conselho': row['sigla_conselho'],
            'numero_conselho': row['numero_conselho'],
            'regiao_conselho': row['regiao_conselho'],
            # Exame Medico
            'data_exame_medico': parse_date(row['data_exame_medico']),
            'tipo_exames': row['tipo_exames'],
            'nome_medico': row['nome_medico'],
            'crm': row['crm'],
            'uf_crm': row['uf_crm'],
            # Ultimo Emprego
            'cnpj_ultimo_emprego': row['cnpj_ultimo_emprego'],
            'empresa_ultimo_emprego': row['empresa_ultimo_emprego'],
            'data_admissao_ultimo': parse_date(row['data_admissao_ultimo']),
            'data_saida_ultimo': parse_date(row['data_saida_ultimo']),
            'matricula_ultimo': row['matricula_ultimo'],
            'primeiro_registro': row['primeiro_registro'],
            'data_ultima_contribuicao_sindical': parse_date(row['data_ultima_contribuicao_sindical']),
            # Dados da Empresa Atual
            'data_admissao': parse_date(row['data_admissao']),
            'funcao': row['funcao'],
            'departamento': row['departamento'],
            'salario': parse_decimal(row['salario']),
            'forma_pagamento': row['forma_pagamento'],
            'prazo_experiencia': row['prazo_experiencia'],
            'prorrogacao': row['prorrogacao'],
            'dias_trabalho': row['dias_trabalho'],
            'horario_trabalho': row['horario_trabalho'],
            'intervalo': row['intervalo'],
            'dias_folga': row['dias_folga'],
            'observacoes_contrato': row['observacoes_contrato'],
            'tipo_contrato': row['tipo_contrato'],
            # Beneficios
            'vale_transporte': parse_bool(row['vale_transporte']),
            'vt_valor_diario': parse_decimal(row['vt_valor_diario']),
            'vt_percentual_desconto': parse_decimal(row['vt_percentual_desconto']),
            'vale_refeicao': parse_bool(row['vale_refeicao']),
            'vr_valor_diario': parse_decimal(row['vr_valor_diario']),
            'vr_percentual_desconto': parse_decimal(row['vr_percentual_desconto']),
            'vale_alimentacao': parse_bool(row['vale_alimentacao']),
            'va_valor_diario': parse_decimal(row['va_valor_diario']),
            'va_percentual_desconto': parse_decimal(row['va_percentual_desconto']),
            'assistencia_medica': parse_bool(row['assistencia_medica']),
            'am_valor_desconto': parse_decimal(row['am_valor_desconto']),
            'assistencia_odontologica': parse_bool(row['assistencia_odontologica']),
            'ao_valor_desconto': parse_decimal(row['ao_valor_desconto']),
            'seguro_vida': parse_bool(row['seguro_vida']),
            'sv_valor_desconto': parse_decimal(row['sv_valor_desconto']),
            'adiantamento': parse_bool(row['adiantamento']),
            'percentual_adiantamento': parse_decimal(row['percentual_adiantamento']),
            'data_pagamento_adiantamento': row['data_pagamento_adiantamento'],
            # Dados Bancarios
            'tipo_conta': row['tipo_conta'],
            'banco': row['banco'],
            'agencia': row['agencia'],
            'conta': row['conta'],
            'observacoes_banco': row['observacoes_banco'],
            # Observacoes
            'observacoes_gerais': row['observacoes_gerais'],
            # Status
            'status': row['status'] or 'ATIVO',
            'data_desligamento': parse_date(row['data_desligamento']),
            'motivo_desligamento': row['motivo_desligamento'],
            'observacoes_desligamento': row['observacoes_desligamento'],
            'motivo_inativacao': row['motivo_inativacao'],
            'submotivo_inativacao': row['submotivo_inativacao'],
            'data_inativacao': parse_date(row['data_inativacao']),
        }

        # Empresa
        if row['empresa_id']:
            try:
                data['empresa'] = Empresa.objects.get(id=row['empresa_id'])
            except Empresa.DoesNotExist:
                pass

        colaborador, created = Colaborador.objects.update_or_create(
            id=row['id'],
            defaults=data
        )
        action = "Criado" if created else "Atualizado"
        print(f"  {action}: {colaborador.nome_completo}")

    print(f"  Total: {len(rows)} colaboradores")


def import_dependentes(cursor):
    """Importa dependentes"""
    print("\n=== Importando Dependentes ===")
    cursor.execute("SELECT * FROM dependentes")
    rows = cursor.fetchall()

    for row in rows:
        try:
            colaborador = Colaborador.objects.get(id=row['colaborador_id'])
            dep, created = Dependente.objects.update_or_create(
                id=row['id'],
                defaults={
                    'colaborador': colaborador,
                    'nome': row['nome'] or '',
                    'parentesco': row['parentesco'],
                    'data_nascimento': parse_date(row['data_nascimento']),
                    'cpf': row['cpf'],
                }
            )
            action = "Criado" if created else "Atualizado"
            print(f"  {action}: {dep.nome}")
        except Colaborador.DoesNotExist:
            print(f"  ERRO: Colaborador {row['colaborador_id']} nao encontrado para dependente {row['nome']}")

    print(f"  Total: {len(rows)} dependentes")


def import_localizacoes(cursor):
    """Importa localizacoes"""
    print("\n=== Importando Localizacoes ===")
    cursor.execute("SELECT * FROM localizacoes")
    rows = cursor.fetchall()

    for row in rows:
        try:
            colaborador = Colaborador.objects.get(id=row['colaborador_id'])
            loc, created = Localizacao.objects.update_or_create(
                id=row['id'],
                defaults={
                    'colaborador': colaborador,
                    'local_nome': row['local_nome'] or '',
                    'cidade': row['cidade'],
                    'uf': row['uf'],
                    'data_inicio': parse_date(row['data_inicio']) or datetime.now().date(),
                    'data_fim': parse_date(row['data_fim']),
                    'observacoes': row['observacoes'],
                }
            )
            action = "Criada" if created else "Atualizada"
            print(f"  {action}: {loc.local_nome}")
        except Colaborador.DoesNotExist:
            print(f"  ERRO: Colaborador {row['colaborador_id']} nao encontrado para localizacao {row['local_nome']}")

    print(f"  Total: {len(rows)} localizacoes")


def import_ferias(cursor):
    """Importa ferias"""
    print("\n=== Importando Ferias ===")
    cursor.execute("SELECT * FROM ferias")
    rows = cursor.fetchall()

    for row in rows:
        try:
            colaborador = Colaborador.objects.get(id=row['colaborador_id'])
            ferias, created = Ferias.objects.update_or_create(
                id=row['id'],
                defaults={
                    'colaborador': colaborador,
                    'periodo_aquisitivo_inicio': parse_date(row['periodo_aquisitivo_inicio']) or datetime.now().date(),
                    'periodo_aquisitivo_fim': parse_date(row['periodo_aquisitivo_fim']) or datetime.now().date(),
                    'periodo_concessivo_limite': parse_date(row['periodo_concessivo_limite']) or datetime.now().date(),
                    'dias_direito': row['dias_direito'] or 30,
                    'dias_gozados': row['dias_gozados'] or 0,
                    'dias_vendidos': row['dias_vendidos'] or 0,
                    'status': row['status'] or 'PENDENTE',
                }
            )
            action = "Criadas" if created else "Atualizadas"
            print(f"  {action}: Ferias ID {ferias.id} - {colaborador.nome_completo}")
        except Colaborador.DoesNotExist:
            print(f"  ERRO: Colaborador {row['colaborador_id']} nao encontrado para ferias")

    print(f"  Total: {len(rows)} registros de ferias")


def import_periodos_ferias(cursor):
    """Importa periodos de ferias"""
    print("\n=== Importando Periodos de Ferias ===")
    cursor.execute("SELECT * FROM periodos_ferias")
    rows = cursor.fetchall()

    for row in rows:
        try:
            ferias = Ferias.objects.get(id=row['ferias_id'])
            periodo, created = PeriodoFerias.objects.update_or_create(
                id=row['id'],
                defaults={
                    'ferias': ferias,
                    'data_inicio': parse_date(row['data_inicio']) or datetime.now().date(),
                    'data_fim': parse_date(row['data_fim']) or datetime.now().date(),
                    'dias': row['dias'] or 0,
                    'abono_pecuniario': parse_bool(row['abono_pecuniario']),
                    'observacoes': row['observacoes'],
                }
            )
            action = "Criado" if created else "Atualizado"
            print(f"  {action}: Periodo ID {periodo.id}")
        except Ferias.DoesNotExist:
            print(f"  ERRO: Ferias {row['ferias_id']} nao encontradas para periodo")

    print(f"  Total: {len(rows)} periodos de ferias")


def import_contratos_experiencia(cursor):
    """Importa contratos de experiencia"""
    print("\n=== Importando Contratos de Experiencia ===")
    cursor.execute("SELECT * FROM contratos_experiencia")
    rows = cursor.fetchall()

    for row in rows:
        try:
            colaborador = Colaborador.objects.get(id=row['colaborador_id'])
            contrato, created = ContratoExperiencia.objects.update_or_create(
                id=row['id'],
                defaults={
                    'colaborador': colaborador,
                    'data_inicio': parse_date(row['data_inicio']) or datetime.now().date(),
                    'prazo_inicial': row['prazo_inicial'] or 45,
                    'data_fim_inicial': parse_date(row['data_fim_inicial']) or datetime.now().date(),
                    'prorrogacao': row['prorrogacao'],
                    'data_fim_prorrogacao': parse_date(row['data_fim_prorrogacao']),
                    'status': row['status'] or 'VIGENTE',
                    'observacoes': row['observacoes'],
                }
            )
            action = "Criado" if created else "Atualizado"
            print(f"  {action}: Contrato ID {contrato.id} - {colaborador.nome_completo}")
        except Colaborador.DoesNotExist:
            print(f"  ERRO: Colaborador {row['colaborador_id']} nao encontrado para contrato")

    print(f"  Total: {len(rows)} contratos de experiencia")


def import_configuracoes(cursor):
    """Importa configuracoes"""
    print("\n=== Importando Configuracoes ===")
    cursor.execute("SELECT * FROM configuracoes")
    rows = cursor.fetchall()

    for row in rows:
        config, created = Configuracao.objects.update_or_create(
            chave=row['chave'],
            defaults={
                'valor': row['valor'],
            }
        )
        action = "Criada" if created else "Atualizada"
        print(f"  {action}: {config.chave}")

    print(f"  Total: {len(rows)} configuracoes")


def main():
    print("=" * 60)
    print("IMPORTACAO DE DADOS - SQLite para MySQL")
    print("=" * 60)
    print(f"Banco de origem: {SQLITE_DB}")

    conn = get_sqlite_connection()
    cursor = conn.cursor()

    try:
        # Importar na ordem correta (respeitando chaves estrangeiras)
        import_empresas(cursor)
        import_colaboradores(cursor)
        import_dependentes(cursor)
        import_localizacoes(cursor)
        import_ferias(cursor)
        import_periodos_ferias(cursor)
        import_contratos_experiencia(cursor)
        import_configuracoes(cursor)

        print("\n" + "=" * 60)
        print("IMPORTACAO CONCLUIDA COM SUCESSO!")
        print("=" * 60)

    except Exception as e:
        print(f"\nERRO durante a importacao: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


if __name__ == '__main__':
    main()
