import flet as ft
from datetime import datetime
from fpdf import FPDF
import json
import platform
import subprocess
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from statistics import mean
import time
import os

def main(page: ft.Page):
    page.title = "Calculadora de Frete"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.scroll = "auto"
    
    # Inicializar o geocodificador
    geolocator = Nominatim(user_agent="calculadora_frete")

    # Lista para armazenar histórico
    historico_calculos = []

    # Carregar histórico salvo
    if os.path.exists('historico.json'):
        try:
            with open('historico.json', 'r') as f:
                historico_calculos = json.load(f)
                # Verificar e corrigir registros antigos
                historico_valido = []
                for calc in historico_calculos:
                    if all(key in calc for key in ["data", "origem", "destino", "distancia", "eixos", "valor"]):
                        historico_valido.append(calc)
                historico_calculos = historico_valido
                # Salvar histórico corrigido
                with open('historico.json', 'w') as f:
                    json.dump(historico_calculos, f)
        except:
            historico_calculos = []
    else:
        historico_calculos = []

    # Campos de entrada
    txt_origem = ft.TextField(
        label="Cidade de Origem",
        width=200,
        hint_text="Ex: São Paulo, SP"
    )

    txt_destino = ft.TextField(
        label="Cidade de Destino",
        width=200,
        hint_text="Ex: Rio de Janeiro, RJ"
    )

    txt_distancia = ft.TextField(
        label="Distância (km)",
        keyboard_type=ft.KeyboardType.NUMBER,
        prefix_text="km ",
        width=200,
        read_only=True
    )

    dd_eixos = ft.Dropdown(
        label="Quantidade de Eixos",
        options=[
            ft.dropdown.Option(str(i), f"{i} Eixos")
            for i in [2,3,4,5,6,7,9]
        ],
        value="2",
        width=200
    )

    # Texto para resultado
    txt_resultado = ft.Text(
        size=20,
        weight=ft.FontWeight.BOLD,
        color=ft.colors.BLUE_700,
    )

    # Estatísticas
    txt_estatisticas = ft.Text(
        size=16,
        color=ft.colors.GREY_700,
    )

    # Lista de histórico
    lista_historico = ft.ListView(
        expand=1,
        spacing=10,
        height=300,
        padding=20,
    )

    def atualizar_historico():
        lista_historico.controls = []
        for calc in historico_calculos[-10:]:  # Últimos 10 cálculos
            lista_historico.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(f"Data: {calc.get('data', '')}", size=14),
                            ft.Text(f"Valor: R$ {calc.get('valor', 0):.2f}", 
                                  size=16, 
                                  weight=ft.FontWeight.BOLD,
                                  color=ft.colors.BLUE_700),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Row([
                            ft.Text(f"De: {calc.get('origem', '')}", size=14),
                            ft.Text(f"Para: {calc.get('destino', '')}", size=14),
                        ]),
                        ft.Row([
                            ft.Text(f"Distância: {calc.get('distancia', 0):.1f} km", size=14),
                            ft.Text(f"Eixos: {calc.get('eixos', '')} eixos", size=14),
                        ]),
                        ft.Divider(),
                    ]),
                    bgcolor=ft.colors.WHITE,
                    border=ft.border.all(1, ft.colors.GREY_400),
                    border_radius=10,
                    padding=10,
                )
            )
        page.update()

    def calcular_frete(distancia, eixos):
        valores_por_eixo = {
            "2": 3.4712, "3": 4.3390, "4": 5.1559,
            "5": 5.5159, "6": 6.1069, "7": 6.8288,
            "9": 8.0526,
        }
        carga_descarga = 503.95
        valor_km = valores_por_eixo.get(eixos, 3.4712)
        return (distancia * valor_km) + carga_descarga

    def calcular_click(e):
        try:
            distancia = float(txt_distancia.value or 0)
            eixos = dd_eixos.value
            
            if distancia <= 0:
                txt_resultado.value = "Por favor, insira uma distância válida"
                txt_resultado.color = ft.colors.RED
                page.update()
                return
            
            valor = calcular_frete(distancia, eixos)
            
            # Adicionar ao histórico
            calculo = {
                "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "origem": txt_origem.value,
                "destino": txt_destino.value,
                "distancia": distancia,
                "eixos": eixos,
                "valor": valor
            }
            historico_calculos.append(calculo)
            
            # Salvar histórico
            with open('historico.json', 'w') as f:
                json.dump(historico_calculos, f)
            
            # Atualizar resultado
            txt_resultado.value = f"Valor do frete: R$ {valor:.2f}"
            txt_resultado.color = ft.colors.BLUE_700
            
            # Atualizar estatísticas
            if len(historico_calculos) > 0:
                media_valor = mean([calc["valor"] for calc in historico_calculos[-10:]])
                media_distancia = mean([calc["distancia"] for calc in historico_calculos[-10:]])
                txt_estatisticas.value = f"Média últimos 10 fretes: R$ {media_valor:.2f} | Distância média: {media_distancia:.1f} km"
            
            # Atualizar histórico
            atualizar_historico()
            
        except Exception as ex:
            txt_resultado.value = f"Erro ao calcular: {str(ex)}"
            txt_resultado.color = ft.colors.RED
            page.update()

    def calcular_distancia(e=None):
        try:
            origem = txt_origem.value
            destino = txt_destino.value
            
            if not origem or not destino:
                return
            
            # Obter coordenadas
            loc_origem = geolocator.geocode(origem)
            loc_destino = geolocator.geocode(destino)
            
            if not loc_origem or not loc_destino:
                txt_distancia.value = ""
                txt_resultado.value = "Não foi possível encontrar uma ou ambas as cidades"
                txt_resultado.color = ft.colors.RED
                page.update()
                return
            
            # Calcular distância
            coords_origem = (loc_origem.latitude, loc_origem.longitude)
            coords_destino = (loc_destino.latitude, loc_destino.longitude)
            distancia = geodesic(coords_origem, coords_destino).kilometers
            
            txt_distancia.value = f"{distancia:.1f}"
            page.update()
            
        except Exception as ex:
            txt_distancia.value = ""
            txt_resultado.value = f"Erro ao calcular distância: {str(ex)}"
            txt_resultado.color = ft.colors.RED
            page.update()

    # Configurar eventos
    txt_origem.on_blur = calcular_distancia
    txt_destino.on_blur = calcular_distancia

    # Botão calcular
    btn_calcular = ft.ElevatedButton(
        "Calcular Frete",
        on_click=calcular_click,
        bgcolor=ft.colors.BLUE_700,
        color=ft.colors.WHITE,
    )

    # Botão PDF
    def gerar_pdf(e=None):
        try:
            if not historico_calculos:
                page.show_snack_bar(ft.SnackBar(
                    content=ft.Text("Não há dados para gerar o PDF!")
                ))
                return
            
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            
            # Título
            pdf.cell(200, 10, txt="Histórico de Cálculos de Frete", ln=True, align='C')
            pdf.ln(10)
            
            # Cabeçalho
            headers = ["Data", "Origem", "Destino", "Distância", "Eixos", "Valor"]
            col_widths = [35, 35, 35, 25, 20, 30]
            
            for header, width in zip(headers, col_widths):
                pdf.cell(width, 10, header, 1)
            pdf.ln()
            
            # Dados
            for calc in historico_calculos:
                pdf.cell(35, 10, calc["data"], 1)
                pdf.cell(35, 10, calc["origem"], 1)
                pdf.cell(35, 10, calc["destino"], 1)
                pdf.cell(25, 10, f"{calc['distancia']:.1f} km", 1)
                pdf.cell(20, 10, str(calc["eixos"]), 1)
                pdf.cell(30, 10, f"R$ {calc['valor']:.2f}", 1)
                pdf.ln()
            
            # Salvar PDF
            pdf_path = "historico_fretes.pdf"
            pdf.output(pdf_path)
            
            # Abrir PDF
            if platform.system() == 'Darwin':       # macOS
                subprocess.run(['open', pdf_path])
            elif platform.system() == 'Windows':    # Windows
                os.startfile(pdf_path)
            else:                                   # Linux
                subprocess.run(['xdg-open', pdf_path])
                
            page.show_snack_bar(ft.SnackBar(
                content=ft.Text("PDF gerado com sucesso!")
            ))
            
        except Exception as ex:
            page.show_snack_bar(ft.SnackBar(
                content=ft.Text(f"Erro ao gerar PDF: {str(ex)}")
            ))

    btn_pdf = ft.ElevatedButton(
        "Gerar PDF",
        on_click=gerar_pdf,
        bgcolor=ft.colors.GREEN_700,
        color=ft.colors.WHITE,
    )

    # Layout
    page.add(
        ft.Container(
            content=ft.Column([
                ft.Text("Calculadora de Frete", size=30, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Row([txt_origem, txt_destino], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([txt_distancia, dd_eixos], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([btn_calcular, btn_pdf], alignment=ft.MainAxisAlignment.CENTER),
                txt_resultado,
                txt_estatisticas,
                ft.Divider(),
                ft.Text("Histórico", size=20, weight=ft.FontWeight.BOLD),
                lista_historico,
            ]),
            padding=20
        )
    )

    # Carregar histórico inicial
    atualizar_historico()

# Configuração específica para web
if __name__ == "__main__":
    os.environ["FLET_FORCE_WEB_VIEW"] = "true"
    ft.app(target=main, view=ft.WEB_BROWSER, port=8080)
