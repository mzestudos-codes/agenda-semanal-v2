"""
Script para gerar imagens da agenda semanal a partir de uma planilha Excel.
Cada imagem contém ícones de empresas com eventos como:
- Divulgações
- Conferências
- Investor Day


As imagens são criadas com base nas informações da planilha 'NomesSemanal.xlsx'
e inseridas de volta nela automaticamente.


Requisitos:
- Pasta 'Icones' com ícones em PNG
- Pasta 'Fonte' com fontes TTF (ex: Lato)
- Pasta 'Fundo' com fundos de diferentes dimensões
- Pasta 'Excel' com a planilha Excel com estrutura pré-definida para o preenchimento da agenda
"""


import math
import tkinter as tk
import subprocess
from openpyxl import load_workbook
from openpyxl.drawing.image import Image as openpyxl_image
import os
from tkinter import messagebox
from PIL import Image, ImageDraw, ImageFont
import time
from datetime import datetime, timedelta


# Número máximo de linhas a serem lidas no Excel (5 por dia x 5 dias + espaços)
MAX_LINHAS = 40
# Mapeia os ícones disponíveis na pasta 'Icones', usando nomes em minúsculo para facilitar a comparação
icones_disponiveis = {arquivo.lower(): arquivo for arquivo in os.listdir("Icones")}


# Define o caminho do arquivo Excel, acessando a pasta "Excel" com o nome do arquivo
caminho_arquivo = os.path.join("Excel", "NomesSemanal.xlsx")
# Carrega a planilha Excel, com o parâmetro 'data_only=True' para ler apenas os valores visíveis (sem fórmulas)
wb = load_workbook(caminho_arquivo, data_only=True)
# Seleciona a planilha ativa (a primeira aba do Excel)
ws = wb.active

# Funções que extraem os dados de divulgações, conferências e Invertor Day da planilha Excel
def ler_nomes_das_divulgacoes():
    nomes_divulgacoes = []
    abertura = []




    linha_atual = 4
    while linha_atual <= MAX_LINHAS:
        # Lê 5 linhas de cada dia
        for _ in range(5):
            row = ws[linha_atual]
            nome = row[0].value if row[0].value is not None else None
            abertura_valor = row[9].value if row[9].value is not None else None
           
            nomes_divulgacoes.append(nome)
            abertura.append(abertura_valor)
            linha_atual += 1




        # Pula 3 linhas (as próximas 3 linhas depois das 5 linhas de empresas são linhas que não possuem
        # nomes de empresas, apenas o nome do dia da semana, categoria do evento (divulgação, conferência ou Investor Day) e um rótulo "nome da empresa"
        linha_atual += 3




    wb.close()
    return nomes_divulgacoes, abertura

def ler_nomes_das_conferencias():
    nomes_conferencias = []
    por = []
    ing = []

    linha_atual = 4
    while linha_atual <= MAX_LINHAS:
        # Lê 5 linhas de cada dia
        for _ in range(5):
            row = ws[linha_atual]
            nome_conf = row[2].value if row[2].value is not None else None
            por_valor = ("Por: " +  row[10].value) if row[10].value is not None else None
            ing_valor = ("Ing. " + row[11].value) if row[11].value is not None else None

            nomes_conferencias.append(nome_conf)
            por.append(por_valor)
            ing.append(ing_valor)
            linha_atual += 1

        # Pula 3 linhas (configs do próximo dia da semana)
        linha_atual += 3
       
    wb.close()
    return nomes_conferencias, por, ing

def ler_nomes_investor_day():
    nomes_investor_day = []
    modalidade = []
    horario = []


    linha_atual = 4
    while linha_atual <= MAX_LINHAS:
        # Lê 5 linhas de cada dia
        for _ in range(5):
            row = ws[linha_atual]
            investor_day_valor = row[5].value if row[5].value is not None else None
            modalidade_valor = row[12].value if row[12].value is not None else None
            horario_valor = row[13].value if row[13].value is not None else None




            nomes_investor_day.append(investor_day_valor)
            modalidade.append(modalidade_valor)
            horario.append(horario_valor)
            linha_atual += 1
        # Pula 3 linhas (configs do próximo dia da semana)
        linha_atual += 3
       
    wb.close()
    return nomes_investor_day, modalidade, horario

# Escolhe e carrega a imagem de fundo adequada com base na quantidade de ícones de cada tipo
def escolher_base(numDiv, numConf, numInv):
    # Monta dinamicamente o caminho do arquivo da imagem base, com base na quantidade de ícones:
    # Exemplo: se houver 3 divulgações, 2 conferências e 1 Investor Day,
    # o caminho será 'Fundo/Base3Divul2Conf1Inv.png'
    caminho = f'Fundo/Base{numDiv}Divul{numConf}Conf{numInv}Inv.png'
   
    # Abre a imagem correspondente usando PIL (Python Imaging Library)
    base_escolhida = Image.open(caminho)


    # Retorna a imagem base carregada para ser usada na montagem final da agenda do dia X
    return base_escolhida

# Cria a base de fundo
def criar_base(qtdDiv, qtdConf, qtdInv):
    # Calcula quantas linhas de ícones serão necessárias para cada tipo de evento
    # Cada linha comporta no máximo 5 ícones, por isso é feita a divisão e arredondamento para cima
    quantidade_total_nomes = [
        math.ceil(qtdDiv / 5),   # Número de linhas necessárias para ícones de divulgações
        math.ceil(qtdConf / 5),  # Número de linhas necessárias para ícones de conferências
        math.ceil(qtdInv / 5)    # Número de linhas necessárias para ícones de Investor Day
    ]

    # Define a posição vertical inicial para o primeiro bloco de ícones (Divulgações)
    posicao_y_inicial = 85
    # Define os deslocamentos verticais (x, y) para os títulos "Conferências" e "Investor Day"
    # Isso serve para posicionar corretamente os títulos desses blocos na imagem
    posicao_conferencia = (47, 30)
    posicao_investor_day = (47, 30)
   
    # Chama a função 'escolher_base' para carregar o fundo apropriado
    # com base no número de linhas de cada tipo de evento
    imagem = escolher_base(quantidade_total_nomes[0],
                  quantidade_total_nomes[1],
                  quantidade_total_nomes[2])

    # Configurações dos textos ‘Conferencias’ e ‘Investor Day’
    texto_divulg_conf_inv = ImageDraw.Draw(imagem)
    fonte = ImageFont.truetype("Fonte/Lato-SemiBold.ttf", 32)
    cor = "#000000"

    # O bloco 'match' define quais textos serão desenhados na imagem base
    # com base na quantidade de linhas (1 linha = até 5 itens) para cada tipo de evento:
    # Divulgações, Conferências e Investor Day.
    # A posição dos títulos na imagem muda conforme a combinação presente.
    match quantidade_total_nomes:
        # Apenas uma linha de algum dos tipos
        case [1,0,0]:
            # Icone das divulgações
            caminho_icone_divulgacoes = os.path.join("Icones/MZ", "icon-Divulgações@3x.png")
            icone_divulgacoes = Image.open(caminho_icone_divulgacoes)
            icone_divulgacoes_largura = 40  # substitua pelo valor desejado
            icone_divulgacoes_altura = 40  # substitua pelo valor desejado
            icone_divulgacoes_redimensionado = icone_divulgacoes.resize((icone_divulgacoes_largura, icone_divulgacoes_altura), Image.LANCZOS)
            imagem.paste(icone_divulgacoes_redimensionado, (47, 30), icone_divulgacoes_redimensionado)
            texto_divulg_conf_inv.text((47+55, 30), "Divulgações", font=fonte, fill=cor)
            # Adiciona a linha divisória
            x_inicio = 47  # Distancia da margem
            x_fim = x_inicio + 881  # Posição final da linha
            y_linha_divisoria = 110
            cor_linha_divisoria = '#E1E1E1'
            # Desenha a linha
            texto_divulg_conf_inv.line([x_inicio, y_linha_divisoria , x_fim, y_linha_divisoria ], fill=cor_linha_divisoria, width=2)
            
        case [0,1,0]:
            # Icone das conferencias
            caminho_icone_conferencias = os.path.join("Icones/MZ", "icon-conferencias@3x.png")
            icone_conferencias = Image.open(caminho_icone_conferencias)
            icone_conferencias_largura = 40  # substitua pelo valor desejado
            icone_conferencias_altura = 40  # substitua pelo valor desejado
            icone_conferencias_redimensionado = icone_conferencias.resize((icone_conferencias_largura, icone_conferencias_altura), Image.LANCZOS)
            imagem.paste(icone_conferencias_redimensionado, (47, 30), icone_conferencias_redimensionado)
            texto_divulg_conf_inv.text((47+55, 30), "Conferências", font=fonte, fill=cor)
            # Adiciona a linha divisória
            x_inicio = 47  # Distancia da margem
            x_fim = x_inicio + 881  # Posição final da linha
            y_linha_divisoria = 110
            cor_linha_divisoria = '#E1E1E1'
            # Desenha a linha
            texto_divulg_conf_inv.line([x_inicio, y_linha_divisoria , x_fim, y_linha_divisoria ], fill=cor_linha_divisoria, width=2)
            
        case [0,0,1]:
            # Icone dos investor_day
            caminho_icone_investor_day = os.path.join("Icones/MZ", "icon-investor-day@3x.png")
            icone_investor_day = Image.open(caminho_icone_investor_day)
            icone_investor_day_largura = 40  # substitua pelo valor desejado
            icone_investor_day_altura = 40  # substitua pelo valor desejado
            icone_investor_day_redimensionado = icone_investor_day.resize((icone_investor_day_largura, icone_investor_day_altura), Image.LANCZOS)
            imagem.paste(icone_investor_day_redimensionado, (47, 30), icone_investor_day_redimensionado)
            texto_divulg_conf_inv.text((47+55, 30), "Investor Days", font=fonte, fill=cor)
            # Adiciona a linha divisória
            x_inicio = 47  # Distancia da margem
            x_fim = x_inicio + 881  # Posição final da linha
            y_linha_divisoria = 110
            cor_linha_divisoria = '#E1E1E1'
            # Desenha a linha
            texto_divulg_conf_inv.line([x_inicio, y_linha_divisoria , x_fim, y_linha_divisoria ], fill=cor_linha_divisoria, width=2)

        # Combinação de dois tipos com uma linha cada  
        case [1,1,0]:            
            # Icone das divulgações
            caminho_icone_divulgacoes = os.path.join("Icones/MZ", "icon-Divulgações@3x.png")
            icone_divulgacoes = Image.open(caminho_icone_divulgacoes)
            icone_divulgacoes_largura = 40  # substitua pelo valor desejado
            icone_divulgacoes_altura = 40  # substitua pelo valor desejado
            icone_divulgacoes_redimensionado = icone_divulgacoes.resize((icone_divulgacoes_largura, icone_divulgacoes_altura), Image.LANCZOS)
            imagem.paste(icone_divulgacoes_redimensionado, (47, 30), icone_divulgacoes_redimensionado)
            texto_divulg_conf_inv.text((47+55, 30), "Divulgações", font=fonte, fill=cor)
            # Adiciona a linha divisória
            x_inicio = 47  # Distancia da margem
            x_fim = x_inicio + 881  # Posição final da linha
            y_linha_divisoria = 110
            cor_linha_divisoria = '#E1E1E1'
            # Desenha a linha
            texto_divulg_conf_inv.line([x_inicio, y_linha_divisoria , x_fim, y_linha_divisoria ], fill=cor_linha_divisoria, width=2)
            
            
            # Icone das conferências
            posicao_conferencia = (47, (210 + 115))
            caminho_icone_conferencias = os.path.join("Icones/MZ", "icon-conferencias@3x.png")
            icone_conferencias = Image.open(caminho_icone_conferencias)
            icone_conferencias_largura = 40  # substitua pelo valor desejado
            icone_conferencias_altura = 40  # substitua pelo valor desejado
            icone_conferencias_redimensionado = icone_conferencias.resize((icone_conferencias_largura, icone_conferencias_altura), Image.LANCZOS)
            imagem.paste(icone_conferencias_redimensionado, posicao_conferencia, icone_conferencias_redimensionado)
            texto_divulg_conf_inv.text((posicao_conferencia[0] + 55, posicao_conferencia[1]), "Conferências", font=fonte, fill=cor)
            # Adiciona a linha divisória
            x_inicio = 47  # Distancia da margem
            x_fim = x_inicio + 881  # Posição final da linha
            y_linha_divisoria = posicao_conferencia[1] + 70
            cor_linha_divisoria = '#E1E1E1'
            # Desenha a linha
            texto_divulg_conf_inv.line([x_inicio, y_linha_divisoria , x_fim, y_linha_divisoria ], fill=cor_linha_divisoria, width=2)
            
        case [0,1,1]:
            # Icone das conferencias
            caminho_icone_conferencias = os.path.join("Icones/MZ", "icon-conferencias@3x.png")
            icone_conferencias = Image.open(caminho_icone_conferencias)
            icone_conferencias_largura = 40  # substitua pelo valor desejado
            icone_conferencias_altura = 40  # substitua pelo valor desejado
            icone_conferencias_redimensionado = icone_conferencias.resize((icone_conferencias_largura, icone_conferencias_altura), Image.LANCZOS)
            imagem.paste(icone_conferencias_redimensionado, (47, 30), icone_conferencias_redimensionado)
            texto_divulg_conf_inv.text((47+55, 30), "Conferências", font=fonte, fill=cor)
            # Adiciona a linha divisória
            x_inicio = 47  # Distancia da margem
            x_fim = x_inicio + 881  # Posição final da linha
            y_linha_divisoria = 110
            cor_linha_divisoria = '#E1E1E1'
            # Desenha a linha
            texto_divulg_conf_inv.line([x_inicio, y_linha_divisoria , x_fim, y_linha_divisoria ], fill=cor_linha_divisoria, width=2)
            
            
            # Icone dos investor day
            posicao_investor_day = (47, (210 + 115))
            caminho_icone_investor_day= os.path.join("Icones/MZ", "icon-investor-day@3x.png")
            icone_investor_day = Image.open(caminho_icone_investor_day)
            icone_investor_day_largura = 40  # substitua pelo valor desejado
            icone_investor_day_altura = 40  # substitua pelo valor desejado
            icone_investor_day_redimensionado = icone_investor_day.resize((icone_investor_day_largura, icone_investor_day_altura), Image.LANCZOS)
            imagem.paste(icone_investor_day_redimensionado, posicao_investor_day, icone_investor_day_redimensionado)
            texto_divulg_conf_inv.text((posicao_investor_day[0] + 55, posicao_investor_day[1]), "Investor Days", font=fonte, fill=cor)
            # Adiciona a linha divisória
            x_inicio = 47  # Distancia da margem
            x_fim = x_inicio + 881  # Posição final da linha
            y_linha_divisoria = posicao_investor_day[1] + 70
            cor_linha_divisoria = '#E1E1E1'
            # Desenha a linha
            texto_divulg_conf_inv.line([x_inicio, y_linha_divisoria , x_fim, y_linha_divisoria ], fill=cor_linha_divisoria, width=2)
            
        case [1,0,1]:
            # Icone das divulgações
            caminho_icone_divulgacoes = os.path.join("Icones/MZ", "icon-Divulgações@3x.png")
            icone_divulgacoes = Image.open(caminho_icone_divulgacoes)
            icone_divulgacoes_largura = 40  # substitua pelo valor desejado
            icone_divulgacoes_altura = 40  # substitua pelo valor desejado
            icone_divulgacoes_redimensionado = icone_divulgacoes.resize((icone_divulgacoes_largura, icone_divulgacoes_altura), Image.LANCZOS)
            imagem.paste(icone_divulgacoes_redimensionado, (47, 30), icone_divulgacoes_redimensionado)
            texto_divulg_conf_inv.text((47+55, 30), "Divulgações", font=fonte, fill=cor)
            # Adiciona a linha divisória
            x_inicio = 47  # Distancia da margem
            x_fim = x_inicio + 881  # Posição final da linha
            y_linha_divisoria = 110
            cor_linha_divisoria = '#E1E1E1'
            # Desenha a linha
            texto_divulg_conf_inv.line([x_inicio, y_linha_divisoria , x_fim, y_linha_divisoria ], fill=cor_linha_divisoria, width=2)
            
            
            # Icone dos investor day
            posicao_investor_day = (47, (210 + 115))
            caminho_icone_investor_day= os.path.join("Icones/MZ", "icon-investor-day@3x.png")
            icone_investor_day = Image.open(caminho_icone_investor_day)
            icone_investor_day_largura = 40  # substitua pelo valor desejado
            icone_investor_day_altura = 40  # substitua pelo valor desejado
            icone_investor_day_redimensionado = icone_investor_day.resize((icone_investor_day_largura, icone_investor_day_altura), Image.LANCZOS)
            imagem.paste(icone_investor_day_redimensionado, posicao_investor_day, icone_investor_day_redimensionado)
            texto_divulg_conf_inv.text((posicao_investor_day[0] + 55, posicao_investor_day[1]), "Investor Days", font=fonte, fill=cor)
            # Adiciona a linha divisória
            x_inicio = 47  # Distancia da margem
            x_fim = x_inicio + 881  # Posição final da linha
            y_linha_divisoria = posicao_investor_day[1] + 70
            cor_linha_divisoria = '#E1E1E1'
            # Desenha a linha
            texto_divulg_conf_inv.line([x_inicio, y_linha_divisoria , x_fim, y_linha_divisoria ], fill=cor_linha_divisoria, width=2)
       
        # Todas as três categorias com uma linha cada
        case [1,1,1]:
            # Icone das divulgações
            caminho_icone_divulgacoes = os.path.join("Icones/MZ", "icon-Divulgações@3x.png")
            icone_divulgacoes = Image.open(caminho_icone_divulgacoes)
            icone_divulgacoes_largura = 40  # substitua pelo valor desejado
            icone_divulgacoes_altura = 40  # substitua pelo valor desejado
            icone_divulgacoes_redimensionado = icone_divulgacoes.resize((icone_divulgacoes_largura, icone_divulgacoes_altura), Image.LANCZOS)
            imagem.paste(icone_divulgacoes_redimensionado, (47, 30), icone_divulgacoes_redimensionado)
            texto_divulg_conf_inv.text((47+55, 30), "Divulgações", font=fonte, fill=cor)
            # Adiciona a linha divisória
            x_inicio = 47  # Distancia da margem
            x_fim = x_inicio + 881  # Posição final da linha
            y_linha_divisoria = 110
            cor_linha_divisoria = '#E1E1E1'
            # Desenha a linha
            texto_divulg_conf_inv.line([x_inicio, y_linha_divisoria , x_fim, y_linha_divisoria ], fill=cor_linha_divisoria, width=2)
            
            # Icone das conferências
            posicao_conferencia = (47, (210 + 115))
            caminho_icone_conferencias = os.path.join("Icones/MZ", "icon-conferencias@3x.png")
            icone_conferencias = Image.open(caminho_icone_conferencias)
            icone_conferencias_largura = 40  # substitua pelo valor desejado
            icone_conferencias_altura = 40  # substitua pelo valor desejado
            icone_conferencias_redimensionado = icone_conferencias.resize((icone_conferencias_largura, icone_conferencias_altura), Image.LANCZOS)
            imagem.paste(icone_conferencias_redimensionado, posicao_conferencia, icone_conferencias_redimensionado)
            texto_divulg_conf_inv.text((posicao_conferencia[0] + 55, posicao_conferencia[1]), "Conferências", font=fonte, fill=cor)
            # Adiciona a linha divisória
            x_inicio = 47  # Distancia da margem
            x_fim = x_inicio + 881  # Posição final da linha
            y_linha_divisoria = posicao_conferencia[1] + 70
            cor_linha_divisoria = '#E1E1E1'
            # Desenha a linha
            texto_divulg_conf_inv.line([x_inicio, y_linha_divisoria , x_fim, y_linha_divisoria ], fill=cor_linha_divisoria, width=2)
            
            
            # Icone dos investor day
            posicao_investor_day = (47, (210 + 120)*2)
            caminho_icone_investor_day= os.path.join("Icones/MZ", "icon-investor-day@3x.png")
            icone_investor_day = Image.open(caminho_icone_investor_day)
            icone_investor_day_largura = 40  # substitua pelo valor desejado
            icone_investor_day_altura = 40  # substitua pelo valor desejado
            icone_investor_day_redimensionado = icone_investor_day.resize((icone_investor_day_largura, icone_investor_day_altura), Image.LANCZOS)
            imagem.paste(icone_investor_day_redimensionado, posicao_investor_day, icone_investor_day_redimensionado)
            texto_divulg_conf_inv.text((posicao_investor_day[0] + 55, posicao_investor_day[1]), "Investor Days", font=fonte, fill=cor)
            # Adiciona a linha divisória
            x_inicio = 47  # Distancia da margem
            x_fim = x_inicio + 881  # Posição final da linha
            y_linha_divisoria = posicao_investor_day[1] + 70
            cor_linha_divisoria = '#E1E1E1'
            # Desenha a linha
            texto_divulg_conf_inv.line([x_inicio, y_linha_divisoria , x_fim, y_linha_divisoria ], fill=cor_linha_divisoria, width=2)

    return imagem, posicao_conferencia, posicao_investor_day

# Retorna apenas os dados (nome da empresa e detalhes) correspondentes a um dia específico da semana
def dados_do_dia(dia_atual, nomes_divulgacoes, abertura, nomes_conferencias, por, ing, nomes_investor_day, modalidade, horario):
    # Cada chamada a 'dividir_em_cinco_listas' transforma a lista original em uma lista de 5 sublistas,
    # onde cada sublista representa os dados de um dia da semana (segunda a sexta).


    div = dividir_em_cinco_listas(nomes_divulgacoes)   # Divide os nomes das empresas com divulgação de resultados
    aber = dividir_em_cinco_listas(abertura)           # Divide os dados de abertura (antes ou depois do mercado)
    conf = dividir_em_cinco_listas(nomes_conferencias) # Divide os nomes das empresas com conferências
    port = dividir_em_cinco_listas(por)                # Divide os dados dos horários em português
    ingl = dividir_em_cinco_listas(ing)                # Divide os dados dos horários em inglês
    inv = dividir_em_cinco_listas(nomes_investor_day)  # Divide os nomes das empresas com Investor Day
    modali = dividir_em_cinco_listas(modalidade)       # Divide os dados da modalidade (online/presencial)
    hora = dividir_em_cinco_listas(horario)            # Divide os horários das apresentações ou eventos


    # Retorna as sublistas do dia atual (índice de 0 a 4, representando segunda a sexta)
    return (
        div[dia_atual], aber[dia_atual], conf[dia_atual],
        port[dia_atual], ingl[dia_atual], inv[dia_atual],
        modali[dia_atual], hora[dia_atual]
    )

# Divide todas as empresas e informações extras em cinco listas, para cada dia da semana
def dividir_em_cinco_listas(lista):
    # Divide uma lista em 5 sublistas de 5 elementos cada, preenchendo com '' se necessário, se não houver 5 empresas
    sublistas = [lista[i:i + 5] for i in range(0, len(lista), 5)]




    # Garante que sempre haverá 5 sublistas
    while len(sublistas) < 5:
        sublistas.append([])  # Adiciona listas vazias se necessário




    # Garante que cada sublista tenha exatamente 5 elementos
    for i in range(5):
        while len(sublistas[i]) < 5:
            sublistas[i].append("")  # Preenche com string vazia




    return sublistas

# Filtra uma lista, removendo valores None e limitando a 5 elementos
def formatar_lista(lista):
    lista_filtrada = [] # Inicializa uma lista vazia para os resultados
   
    for value in lista: # Itera sobre cada elemento da lista original (de um dia especifico)
        if value is not None:
            lista_filtrada.append(value) # Adiciona à lista filtrada se for válido
        if len(lista_filtrada) == 5: # Verifica se já atingiu o limite de 5 itens
            break  # Interrompe o loop prematuramente se já tiver 5 elementos
       
    return lista_filtrada # Retorna a lista processada

# 🔹 Cria a imagem com os ícones
def criar_imagem(dia_atual):
    # Lê os dados das divulgações (nomes das empresas e tipo de abertura)
    nomes_divulgacoes, abertura = ler_nomes_das_divulgacoes()
    # Lê os dados das conferências (nomes e idiomas disponíveis)
    nomes_conferencias, por, ing = ler_nomes_das_conferencias()
    # Lê os dados dos eventos de Investor Day (nomes, modalidade e horários)
    nomes_investor_day, modalidade, horario = ler_nomes_investor_day()

    # Filtra os dados para pegar apenas os correspondentes ao dia da semana atual
    div, aber, conf, port, ingl, inv, modali, hora = dados_do_dia(dia_atual, nomes_divulgacoes, abertura, nomes_conferencias, por, ing, nomes_investor_day, modalidade, horario)
   
    # A função é chamada para remover valores Nulos e prezervar o máximo de até 5 empresas por categoria
    div = formatar_lista(div)
    aber = formatar_lista(aber)
    conf = formatar_lista(conf)
    port = formatar_lista(port)
    ingl = formatar_lista(ingl)
    inv = formatar_lista(inv)
    modali = formatar_lista(modali)
    hora = formatar_lista(hora)
   
    # Cria a base de fundo baseando-se na quantidade de linhas de cada tipo de evento
    imagem_base, posicao_conferencia, posicao_investor_day = criar_base(len(div), len(conf), len(inv))

    # Estabelece o racional de distância horizontal onde as imagens e textos vão começar (horizontal X)
    posicao_x_inicial = 47
    # Estabelece o racional de distância vertical onde as imagens e textos vão começar (vertical Y)
    posicao_y_inicial = 150
    distancia_entre_icones = 190  # Ajuste para a distância entre ícones


    contador = 0
    draw = ImageDraw.Draw(imagem_base) # Draw é um objeto que permite desenhar na imagem
    altura_linha = 12  # Ajuste para a distância entre ícone e texto


    # Função que lê a data da agenda e insere na imagem final
    adicionar_data(dia_atual, imagem_base)

    # Fonte para o texto abaixo dos ícones
    try:
        font_titulo = ImageFont.truetype("Fonte/Lato-SemiBold.ttf", 20)  # Ajuste o tamanho conforme necessário
        font_subtitulo = ImageFont.truetype("Fonte/Lato-Bold.ttf", 20)  # Ajuste o tamanho conforme necessário
    except IOError:
        # Caso a fonte não esteja disponível, usa a fonte padrão
        font = ImageFont.load_default()


    # Adiciona os ícones de empresas com divulgações de resultados
    for nome_divul, abert in zip(div, aber):
        
        contador += 1
        nome_icone = f"{nome_divul}.png"
        # Tratamento especial para o ícone "Veja+" que representa mais divulgações
        if nome_icone == "veja+.png":
            nome_icone = "VejaMaisDivulgacoes.png"
        nome_icone_lower = nome_icone.lower()  # Converte o nome para lowercase para comparar com o nome no dicionário (que está em lowercase)


        if nome_icone_lower in icones_disponiveis:
            caminho_icone_divul = os.path.join("Icones", icones_disponiveis[nome_icone_lower]) # Pega o nome da empresa com estilização original via dicionário
            imagem_sobreposta_divul = Image.open(caminho_icone_divul)
            caminho_icone_divul = os.path.splitext(os.path.basename(caminho_icone_divul))[0]
           
            # Se for o ícone "VejaMais", posiciona e pula para o próximo sem adicionar texto
            if nome_icone_lower == "vejamaisdivulgacoes.png":
                imagem_base.paste(imagem_sobreposta_divul, (posicao_x_inicial - 15, posicao_y_inicial), imagem_sobreposta_divul)
                posicao_x_inicial += distancia_entre_icones
                continue


            # Cola o ícone e adiciona textos de nome e abertura
            imagem_base.paste(imagem_sobreposta_divul, (posicao_x_inicial, posicao_y_inicial), imagem_sobreposta_divul)
            adicionar_textos(draw, caminho_icone_divul, abert, "", "", posicao_x_inicial, posicao_y_inicial, imagem_sobreposta_divul, font_titulo, font_subtitulo)


            # Pega o racional X e aumenta com a distância entre os ícones para comportar mais um, se houver, no espaçamento ideal
            posicao_x_inicial += distancia_entre_icones
       
    contador = 0 # Inicializa um contador para controlar a quantidade de ícones adicionados (não é usado diretamente nas posições).
    posicao_x_inicial = 47 # Define a posição horizontal inicial (X) onde os ícones começarão a ser inseridos na imagem.
   
    # Ajusta a posição vertical da linha de conferências dependendo da existência de divulgações
    if len(nomes_divulgacoes) != 0 and len(nomes_conferencias) == 0:
        posicao_y_inicial_2 = 30 # Se houver apenas divulgações (sem conferências), a linha de conferências será sobreposta à de divulgações
    elif len(nomes_conferencias) != 0:
        posicao_y_inicial_2 = 130 + posicao_conferencia[1]
        # Se houver conferências, reposiciona a linha mais abaixo, somando o deslocamento vertical definido em posicao_conferencia
               
               
               
    # Adiciona os ícones de conferências com horários em português e inglês
    for nome_conf, por, ing in zip(conf, port, ingl):  
        contador += 1  
        nome_icone = f"{nome_conf}.png"
        # Tratamento especial para o "Veja+" de conferências
        if nome_icone == "veja+.png":
            nome_icone = "VejaMaisConferencias.png"
        nome_icone_lower = nome_icone.lower()




        if nome_icone_lower in icones_disponiveis:
            caminho_icone_conf = os.path.join("Icones", icones_disponiveis[nome_icone_lower])
            imagem_sobreposta_conf = Image.open(caminho_icone_conf)
            caminho_icone_conf = os.path.splitext(os.path.basename(caminho_icone_conf))[0]
           
            # Ícone de "Veja Mais Conferências"
            if nome_icone_lower == "vejamaisconferencias.png":
                imagem_base.paste(imagem_sobreposta_conf, (posicao_x_inicial - 15, posicao_y_inicial_2), imagem_sobreposta_conf)
                posicao_x_inicial += distancia_entre_icones
                continue
         
            # Cola o ícone da conferência e textos de horários
            imagem_base.paste(imagem_sobreposta_conf, (posicao_x_inicial, posicao_y_inicial_2), imagem_sobreposta_conf)
            adicionar_textos(draw, caminho_icone_conf, "", por, ing, posicao_x_inicial, posicao_y_inicial_2, imagem_sobreposta_conf, font_titulo, font_subtitulo)


            posicao_x_inicial += distancia_entre_icones




    contador = 0 # Inicializa um contador para controlar a quantidade de ícones adicionados (não é usado diretamente nas posições).
    posicao_x_inicial = 47 # Define a posição horizontal inicial (X) onde os ícones começarão a ser inseridos na imagem.
    posicao_y_inicial_3 = 130 + posicao_investor_day[1]


    # Adiciona os ícones de eventos "Investor Day" com modalidade e horário
    for nome_inv, mod, hor in zip(inv, modali, hora):
        contador += 1
        nome_icone = f"{nome_inv}.png"
       
       # Tratamento para ícone "Veja+" de Investor Day
        if nome_icone == "veja+.png":
            nome_icone = "VejaMaisInvestorDay.png"
       
        nome_icone_lower = nome_icone.lower()




        if nome_icone_lower in icones_disponiveis:
            caminho_icone_inv = os.path.join("Icones", icones_disponiveis[nome_icone_lower])
            imagem_sobreposta_inv = Image.open(caminho_icone_inv)
            caminho_icone_inv = os.path.splitext(os.path.basename(caminho_icone_inv))[0]
               
            # Ícone de "Veja Mais Investor Day"
            if nome_icone_lower == "vejamaisinvestorday.png":
                imagem_base.paste(imagem_sobreposta_inv, (posicao_x_inicial - 15, posicao_y_inicial_3), imagem_sobreposta_inv)
                posicao_x_inicial += distancia_entre_icones
                continue
               
            # Cola o ícone de Investor Day e adiciona textos
            imagem_base.paste(imagem_sobreposta_inv, (posicao_x_inicial, posicao_y_inicial_3), imagem_sobreposta_inv)
            adicionar_textos(draw, caminho_icone_inv, "", mod, hor, posicao_x_inicial, posicao_y_inicial_3, imagem_sobreposta_inv, font_titulo, font_subtitulo)


            posicao_x_inicial += distancia_entre_icones

    return imagem_base

# 🔹 Adiciona a data na imagem final
def adicionar_data(dia_atual, imagem_base):
    # Fonte e cor para o número do dia (ex: "15" em "15 de Outubro")
    font_dia = ImageFont.truetype("Fonte/Lato-SemiBold.ttf", 32) # Fonte em negrito no tamanho 16
    cor_dia = '#33a0ff' 
   
    # Fonte e cor para o dia da semana (ex: "Segunda-feira")
    font_dia_semana = ImageFont.truetype("Fonte/Lato-SemiBold.ttf", 32) # Fonte semi-negrito no tamanho 16
    cor_dia_semana = '#33a0ff' 
   
    # Coordenadas
    posicao_x = 47 # Distancia da margem
    posicao_y = 30 # Altura antes do icone e dia da semana
    
    # Prepara o objeto para desenhar na imagem
    draw = ImageDraw.Draw(imagem_base)
   
    # ===== CARREGA AS DATAS =====
    lista_de_datas = [] # Cria a lista para receber as datas
    receber_datas(lista_de_datas) # Preenche a lista com datas do Excel
       
    # Divide uma lista em 2 sublistas de 2 elementos cada, dia do mês e da semana
    # Organiza as datas em pares: [['DD/MM', 'DiaSemana'], ...]
    data = [lista_de_datas[i:i + 2] for i in range(0, len(lista_de_datas), 2)]
   
    # ===== ELEMENTOS VISUAIS =====
    
    # Icone do calendário
    caminho_icone_calendario = os.path.join("Icones/MZ", "icon-calendar@3x.png") # Pega o nome da empresa com estilização original via dicionário
    icone_calendario = Image.open(caminho_icone_calendario)
    icone_calendario_largura = 40  # substitua pelo valor desejado
    icone_calendario_altura = 40    # substitua pelo valor desejado
    icone_calendario_redimensionado = icone_calendario.resize((icone_calendario_largura, icone_calendario_altura), Image.LANCZOS)
    imagem_base.paste(icone_calendario_redimensionado, ((posicao_x + 585), (posicao_y)), icone_calendario_redimensionado)
    
    # Adiciona o dia do mês
    posicao_x_dia = posicao_x + 633
    posicao_y_dia = posicao_y
    draw.text((posicao_x_dia, posicao_y_dia), data[dia_atual][0][8:10], font=font_dia, fill=cor_dia)
   
    # Adiciona o dia da semana
    posicao_x_dia_semana = posicao_x_dia + 45   # distância do dia do mês
    posicao_y_dia_semana = posicao_y
    draw.text((posicao_x_dia_semana, posicao_y_dia_semana), data[dia_atual][1].capitalize(), font=font_dia_semana, fill=cor_dia_semana)
   
# Extrai datas e dias da semana de células específicas do Excel e adiciona a uma lista
def receber_datas(lista):
    # Esta função lê valores de células pré-definidas na planilha Excel que contêm:
    # - Datas no formato DD/MM/AAAA (células ímpares: I2, I9, I17, I25, I33)
    # - Dias da semana por extenso (células pares: I3, I10, I18, I26, I34)
   
    # Adiciona data e dia da semana da SEGUNDA-FEIRA
    lista.append(str(ws['I2'].value))  # Data (ex: "15/04/2024")
    lista.append(str(ws['I3'].value))  # Dia (ex: "segunda-feira")
   
    # Adiciona data e dia da semana da TERÇA-FEIRA
    lista.append(str(ws['I9'].value))   # Observação: Há um salto de 6 linhas entre blocos (I2 → I9)
    lista.append(str(ws['I10'].value))
   
    # Adiciona data e dia da semana da QUARTA-FEIRA
    lista.append(str(ws['I17'].value))  # Padrão continua: +8 linhas do anterior (I9 → I17)
    lista.append(str(ws['I18'].value))
   
    # Adiciona data e dia da semana da QUINTA-FEIRA
    lista.append(str(ws['I25'].value))  # +8 linhas (I17 → I25)
    lista.append(str(ws['I26'].value))
   
    # Adiciona data e dia da semana da SEXTA-FEIRA
    lista.append(str(ws['I33'].value))  # +8 linhas (I25 → I33)
    lista.append(str(ws['I34'].value))


    return lista

# 🔹 Adiciona os textos (nome, por e ing)
def adicionar_textos(draw, nome, sub1, sub2, sub3, posicao_x_inicial, posicao_y_inicial, imagem_sobreposta, font_titulo, font_subtitulo):
    cor_titulo = "#202126"
    cor_subtitulo = "#8F8F8F"

    # Adiciona os subtítulos (abertura, português e inglês)
    subtitulo_abertura_largura, subtitulo_abertura_altura = draw.textbbox((0, 0), sub1, font=font_subtitulo)[2:4]
    subtitulo_por_largura, subtitulo_por_altura = draw.textbbox((0, 0), sub2, font=font_subtitulo)[2:4]
    subtitulo_ing_largura, subtitulo_ing_altura = draw.textbbox((0, 0), sub3, font=font_subtitulo)[2:4]
   
    posicao_x_subtitulo = posicao_x_inicial + (imagem_sobreposta.width - subtitulo_abertura_largura) // 2
    texto_posicao = (posicao_x_subtitulo, (posicao_y_inicial) + imagem_sobreposta.height + 12)
    draw.text(texto_posicao, sub1, font=font_subtitulo, fill=cor_subtitulo)

    posicao_x_subtitulo = posicao_x_inicial + (imagem_sobreposta.width - subtitulo_por_largura) // 2
    texto_posicao = (posicao_x_subtitulo, (posicao_y_inicial) + imagem_sobreposta.height + 12)
    draw.text(texto_posicao, sub2, font=font_subtitulo, fill=cor_titulo)

    posicao_x_subtitulo = posicao_x_inicial + (imagem_sobreposta.width - subtitulo_ing_largura) // 2
    texto_posicao = (posicao_x_subtitulo, (posicao_y_inicial + 30) + imagem_sobreposta.height + 12)
    draw.text(texto_posicao, sub3, font=font_subtitulo, fill=cor_subtitulo)

# 🔹 Adiciona a imagem ao Excel
def adicionar_imagem_no_excel():
    """
    Gera imagens da agenda financeira para cada dia da semana (segunda a sexta)
    e insere essas imagens em um arquivo Excel, substituindo quaisquer imagens existentes.
   
    Fluxo principal:
    1. Cria imagens temporárias para cada dia da semana
    2. Abre a planilha Excel
    3. Remove imagens antigas
    4. Insere as novas imagens nas posições pré-definidas
    5. Salva a planilha e limpa os arquivos temporários
   
    Tratamento de erros:
    - Interrompe a execução e mostra mensagem de erro se falhar ao criar qualquer imagem
    """
   
    # ===== CRIAÇÃO DAS IMAGENS TEMPORÁRIAS =====
    # Segunda-feira (índice 0)
    segunda_feira = criar_imagem(0)
    if not segunda_feira: # Verificação de erro
        messagebox.showerror("Aviso", "Erro ao criar a imagem de segunda-feira. Finalizando...")
        return
    caminho_imagem_0 = os.path.join("imagem_temp0.png")
    segunda_feira.save(caminho_imagem_0)
   
    # Terça-feira (índice 1)
    terca_feira = criar_imagem(1)
    if not terca_feira:
        messagebox.showerror("Aviso", "Erro ao criar a imagem de terça-feira. Finalizando...")
        return
    caminho_imagem_1 = os.path.join("imagem_temp1.png")
    terca_feira.save(caminho_imagem_1)
   
    # Quarta-feira (índice 2)
    quarta_feira = criar_imagem(2)
    if not quarta_feira:
        messagebox.showerror("Aviso", "Erro ao criar a imagem de quarta-feira. Finalizando...")
        return
   
    caminho_imagem_2 = os.path.join("imagem_temp2.png")
    quarta_feira.save(caminho_imagem_2)
   
    # Quinta-feira (índice 3)
    quinta_feira = criar_imagem(3)
    if not quinta_feira:
        messagebox.showerror("Aviso", "Erro ao criar a imagem de quinta-feira. Finalizando...")
        return
   
    caminho_imagem_3 = os.path.join("imagem_temp3.png")
    quinta_feira.save(caminho_imagem_3)
   
    # Sexta-feira (índice 4)
    sexta_feira = criar_imagem(4)
    if not sexta_feira:
        messagebox.showerror("Aviso", "Erro ao criar a imagem de segunda-feira. Finalizando...")
        return
   
    caminho_imagem_4 = os.path.join("imagem_temp4.png")
    sexta_feira.save(caminho_imagem_4)




    # Função load_workbook é chamada novamente sem o data_only=True,
    # porque estamos na parte de inserir as imagens e salvar a planilha.
    # Com o atributo data_only=True, as fórmulas somem.
    # Por isso, é necessário chamar a função novamente, mas sem o atributo
    caminho_arquivo = os.path.join("Excel", "NomesSemanal.xlsx")
    wb = load_workbook(caminho_arquivo)
    ws = wb.active


    # Remove todas as imagens existentes na planilha
    for img in ws._images[:]:
        ws._images.remove(img)


    # ===== INSERÇÃO DAS NOVAS IMAGENS =====
    # Configura posicionamento preciso de cada imagem:
    # - img0 (segunda): coluna P, linha 4
    # - img1 (terça): coluna W, linha 4
    # - [...] (demais dias com posições específicas)
    img0 = openpyxl_image(caminho_imagem_0)
    img1 = openpyxl_image(caminho_imagem_1)
    img2 = openpyxl_image(caminho_imagem_2)
    img3 = openpyxl_image(caminho_imagem_3)
    img4 = openpyxl_image(caminho_imagem_4)
    img0.anchor = 'P4'
    img1.anchor = 'AB4'
    img2.anchor = 'AN4'
    img3.anchor = 'AZ4'
    img4.anchor = 'BL4'
    ws.add_image(img0)
    ws.add_image(img1)
    ws.add_image(img2)
    ws.add_image(img3)
    ws.add_image(img4)


    # Salva as alterações no Excel
    wb.save(caminho_arquivo)


    # ===== LIMPEZA =====
    # Remove os arquivos temporários de imagem
    os.remove(caminho_imagem_0)
    os.remove(caminho_imagem_1)
    os.remove(caminho_imagem_2)
    os.remove(caminho_imagem_3)
    os.remove(caminho_imagem_4)

# 🔹 Abre o arquivo Excel
def abrir_excel():
    if os.path.exists(caminho_arquivo):
        try:
            os.startfile(caminho_arquivo)  # Abre o Excel no programa padrão
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir o arquivo.\n{e}")
    else:
        messagebox.showerror("❌ Erro", "O arquivo Excel não foi encontrado!")

# 🔹 Executa as funções
adicionar_imagem_no_excel()
abrir_excel()