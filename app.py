import os
import warnings

# Configurações para suprimir avisos
os.environ["FLET_FORCE_WEB_VIEW"] = "true"
os.environ["FLET_LOG_LEVEL"] = "error"
os.environ["NO_AT_BRIDGE"] = "1"  # Desabilita o serviço de acessibilidade do GTK
warnings.filterwarnings("ignore")

# Importações regulares
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

def main(page: ft.Page):
    # Configurações da página
    page.window_width = 1200
    page.window_height = 900
    page.window_maximized = True  # Maximizar janela
    page.window_center()          # Centralizar janela
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

    # Substituir a tabela por uma ListView
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
                            ft.Text(f"Tipo: {calc.get('ida_volta', 'Apenas Ida')}", size=14),
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

    def gerar_pdf(e=None):
        try:
            print("Iniciando geração do PDF...")
            
            if not historico_calculos:
                page.show_snack_bar(ft.SnackBar(
                    content=ft.Text("Não há dados para gerar o PDF!")
                ))
                return

            print("Criando PDF...")
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Helvetica", size=12)
            
            print("Adicionando título...")
            pdf.cell(200, 10, text="Histórico de Cálculos de Frete", 
                    new_x="LMARGIN", new_y="NEXT", align='C')
            
            print("Adicionando cabeçalho...")
            headers = ["Data", "Origem", "Destino", "Distância", "Eixos", "Valor", "Tipo"]
            widths = [30, 35, 35, 25, 20, 25, 20]
            
            for header, width in zip(headers, widths):
                pdf.cell(width, 10, header, 1)
            pdf.ln()
            
            print("Adicionando dados...")
            for calc in historico_calculos:
                # Substituir caracteres especiais
                origem = str(calc.get("origem", "")).replace("→", "->")[:15]
                destino = str(calc.get("destino", "")).replace("→", "->")[:15]
                
                pdf.cell(30, 10, str(calc.get("data", "")), 1)
                pdf.cell(35, 10, origem, 1)
                pdf.cell(35, 10, destino, 1)
                pdf.cell(25, 10, f"{float(calc.get('distancia', 0)):.1f} km", 1)
                pdf.cell(20, 10, str(calc.get("eixos", "")), 1)
                pdf.cell(25, 10, f"R$ {float(calc.get('valor', 0)):.2f}", 1)
                pdf.cell(20, 10, str(calc.get("ida_volta", "Ida")).replace("→", "->"), 1)
                pdf.ln()
            
            print("Salvando arquivo...")
            arquivo_pdf = "historico_fretes.pdf"
            pdf.output(arquivo_pdf)
            print(f"PDF salvo em: {os.path.abspath(arquivo_pdf)}")
            
            print("Tentando abrir o arquivo...")
            sistema = platform.system()
            if sistema == 'Linux':
                os.system(f'xdg-open "{arquivo_pdf}"')
            elif sistema == 'Windows':
                os.startfile(arquivo_pdf)
            elif sistema == 'Darwin':
                os.system(f'open "{arquivo_pdf}"')
            
            page.show_snack_bar(ft.SnackBar(
                content=ft.Text("PDF gerado com sucesso!"),
                bgcolor=ft.colors.GREEN_700
            ))
            
        except Exception as e:
            print(f"Erro ao gerar PDF: {str(e)}")
            page.show_snack_bar(ft.SnackBar(
                content=ft.Text(f"Erro ao gerar PDF: {str(e)}"),
                bgcolor=ft.colors.RED_700
            ))
        finally:
            page.update()

    def mostrar_historico(e=None):
        def fechar_dialogo(e):
            page.dialog.open = False
            page.update()

        try:
            dlg = ft.AlertDialog(
                title=ft.Text("Histórico de Cálculos"),
                content=ft.Column(
                    [
                        ft.DataTable(
                            columns=[
                                ft.DataColumn(ft.Text("Data")),
                                ft.DataColumn(ft.Text("Origem")),
                                ft.DataColumn(ft.Text("Destino")),
                                ft.DataColumn(ft.Text("Distância")),
                                ft.DataColumn(ft.Text("Eixos")),
                                ft.DataColumn(ft.Text("Valor")),
                            ],
                            rows=[
                                ft.DataRow(
                                    cells=[
                                        ft.DataCell(ft.Text(calc["data"])),
                                        ft.DataCell(ft.Text(calc["origem"])),
                                        ft.DataCell(ft.Text(calc["destino"])),
                                        ft.DataCell(ft.Text(f"{calc['distancia']:.1f} km")),
                                        ft.DataCell(ft.Text(calc["eixos"])),
                                        ft.DataCell(ft.Text(f"R$ {calc['valor']:.2f}")),
                                    ],
                                ) for calc in historico_calculos
                            ],
                        ),
                        ft.Row(
                            [
                                ft.ElevatedButton(
                                    "Gerar PDF", 
                                    on_click=gerar_pdf,
                                    style=ft.ButtonStyle(
                                        color=ft.colors.WHITE,
                                        bgcolor=ft.colors.GREEN_700,
                                    )
                                ),
                                ft.ElevatedButton(
                                    "Fechar", 
                                    on_click=fechar_dialogo,
                                    style=ft.ButtonStyle(
                                        color=ft.colors.WHITE,
                                        bgcolor=ft.colors.RED_700,
                                    )
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.END,
                        ),
                    ],
                    scroll=ft.ScrollMode.AUTO,
                    height=400,
                ),
            )
            page.dialog = dlg
            dlg.open = True
            page.update()
        except Exception as e:
            page.show_snack_bar(ft.SnackBar(content=ft.Text(f"Erro ao abrir histórico: {str(e)}")))
            page.update()

    def calcular_distancia():
        try:
            origem = txt_origem.value
            destino = txt_destino.value
            
            if not origem or not destino:
                raise ValueError("Origem e destino são obrigatórios")

            # Adicionar ", Brasil" se não especificado
            if "brasil" not in origem.lower():
                origem += ", Brasil"
            if "brasil" not in destino.lower():
                destino += ", Brasil"

            # Obter coordenadas
            loc_origem = geolocator.geocode(origem)
            # Pequena pausa para evitar limite de requisições
            time.sleep(1)
            loc_destino = geolocator.geocode(destino)

            if not loc_origem or not loc_destino:
                raise ValueError("Localização não encontrada")

            # Calcular distância
            coords_origem = (loc_origem.latitude, loc_origem.longitude)
            coords_destino = (loc_destino.latitude, loc_destino.longitude)
            
            # Calcular distância em km
            distancia = geodesic(coords_origem, coords_destino).kilometers
            
            txt_distancia.value = f"{distancia:.1f}"
            page.update()
            return distancia

        except Exception as e:
            txt_resultado.value = f"Erro ao calcular distância: {str(e)}"
            txt_resultado.color = ft.colors.RED_700
            page.update()
            return None

    def atualizar_estatisticas():
        if historico_calculos:
            valores = [calc['valor'] for calc in historico_calculos]
            media = mean(valores)
            maximo = max(valores)
            minimo = min(valores)
            
            txt_estatisticas.value = (
                f"Estatísticas:\n"
                f"Média: R$ {media:.2f}\n"
                f"Máximo: R$ {maximo:.2f}\n"
                f"Mínimo: R$ {minimo:.2f}"
            )
            page.update()

    # Lista para armazenar múltiplos destinos
    destinos_lista = []

    # Switch para ida e volta
    sw_ida_volta = ft.Switch(
        label="Calcular Ida e Volta",
        value=False,
        tooltip="Dobra a quilometragem total"
    )

    # Lista visual de destinos
    lista_destinos = ft.ListView(
        expand=1,
        spacing=10,
        height=200,
        padding=20,
    )

    def atualizar_lista_destinos():
        lista_destinos.controls = []
        for i, destino in enumerate(destinos_lista):
            lista_destinos.controls.append(
                ft.Row(
                    controls=[
                        ft.Text(f"{i+1}. De: {destino['origem']} → Para: {destino['destino']} ({destino['distancia']:.1f} km)"),
                        ft.IconButton(
                            icon=ft.icons.DELETE,
                            tooltip="Remover destino",
                            data=i,
                            on_click=lambda e: remover_destino(e.control.data)
                        )
                    ]
                )
            )
        page.update()

    def remover_destino(index):
        destinos_lista.pop(index)
        atualizar_lista_destinos()
        calcular_total()

    def adicionar_destino(e):
        try:
            distancia = calcular_distancia()
            if not distancia:
                return

            destino = {
                "origem": txt_origem.value,
                "destino": txt_destino.value,
                "distancia": distancia
            }
            destinos_lista.append(destino)
            
            # Limpar campos para próximo destino
            txt_destino.value = ""
            txt_distancia.value = ""
            
            atualizar_lista_destinos()
            calcular_total()
            page.update()

        except Exception as e:
            txt_resultado.value = f"Erro ao adicionar destino: {str(e)}"
            txt_resultado.color = ft.colors.RED_700
            page.update()

    def calcular_total():
        if not destinos_lista:
            txt_resultado.value = "Adicione pelo menos um destino!"
            txt_resultado.color = ft.colors.RED_700
            page.update()
            return

        distancia_total = sum(d['distancia'] for d in destinos_lista)
        
        # Verificar se é ida e volta
        if sw_ida_volta.value:
            distancia_total *= 2
            txt_resultado.value = f"Calculando ida e volta ({distancia_total:.1f} km)"
        else:
            txt_resultado.value = f"Calculando apenas ida ({distancia_total:.1f} km)"

        valor = calcular_frete(distancia_total, dd_eixos.value)
        
        # Adicionar ao histórico
        calculo = {
            "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "origem": destinos_lista[0]['origem'],
            "destino": " → ".join(d['destino'] for d in destinos_lista),
            "distancia": distancia_total,
            "eixos": dd_eixos.value,
            "valor": valor,
            "ida_volta": "Ida e Volta" if sw_ida_volta.value else "Apenas Ida"
        }
        historico_calculos.append(calculo)
        
        # Salvar histórico
        with open('historico.json', 'w') as f:
            json.dump(historico_calculos, f)

        txt_resultado.value = (
            f"Distância total: {distancia_total:.1f} km\n"
            f"{'(Ida e Volta)' if sw_ida_volta.value else '(Apenas Ida)'}\n"
            f"Valor do frete: R$ {valor:.2f}"
        )
        txt_resultado.color = ft.colors.BLUE_700
        
        atualizar_historico()
        atualizar_estatisticas()
        page.update()

    def limpar_destinos():
        destinos_lista.clear()
        atualizar_lista_destinos()
        txt_resultado.value = ""
        txt_distancia.value = ""
        page.update()

    def alternar_tema(e):
        page.theme_mode = (
            ft.ThemeMode.LIGHT 
            if page.theme_mode == ft.ThemeMode.DARK 
            else ft.ThemeMode.DARK
        )
        page.update()

    # Botões
    btn_tema = ft.IconButton(
        icon=ft.icons.LIGHT_MODE,
        on_click=alternar_tema,
        tooltip="Alternar Tema"
    )

    btn_exportar = ft.ElevatedButton(
        text="Exportar PDF",
        on_click=gerar_pdf,
        style=ft.ButtonStyle(
            color=ft.colors.WHITE,
            bgcolor=ft.colors.GREEN_700,
            padding=20,
        )
    )

    btn_adicionar = ft.ElevatedButton(
        text="Adicionar Destino",
        on_click=adicionar_destino,
        style=ft.ButtonStyle(
            color=ft.colors.WHITE,
            bgcolor=ft.colors.BLUE_700,
            padding=20,
        )
    )

    btn_calcular_total = ft.ElevatedButton(
        text="Calcular Total",
        on_click=lambda _: calcular_total(),
        style=ft.ButtonStyle(
            color=ft.colors.WHITE,
            bgcolor=ft.colors.GREEN_700,
            padding=20,
        )
    )

    btn_limpar = ft.ElevatedButton(
        text="Limpar Destinos",
        on_click=lambda _: limpar_destinos(),
        style=ft.ButtonStyle(
            color=ft.colors.WHITE,
            bgcolor=ft.colors.RED_700,
            padding=20,
        )
    )

    btn_historico = ft.ElevatedButton(
        "Visualizar Histórico",
        on_click=mostrar_historico,
        style=ft.ButtonStyle(
            color=ft.colors.WHITE,
            bgcolor=ft.colors.BLUE_700,
            padding=20,
        )
    )

    def limpar_historico(e=None):
        try:
            # Limpa a lista em memória
            historico_calculos.clear()
            
            # Salva um array vazio no arquivo
            with open('historico.json', 'w') as f:
                json.dump([], f)
            
            # Atualiza a interface
            atualizar_historico()
            atualizar_estatisticas()
            
            page.show_snack_bar(ft.SnackBar(
                content=ft.Text("Histórico limpo com sucesso!"),
                bgcolor=ft.colors.GREEN_700
            ))
            page.update()
            
        except Exception as e:
            page.show_snack_bar(ft.SnackBar(
                content=ft.Text(f"Erro ao limpar histórico: {str(e)}"),
                bgcolor=ft.colors.RED_700
            ))
            page.update()

    # Adicionar botão na interface
    btn_limpar_historico = ft.ElevatedButton(
        "Limpar Histórico",
        on_click=limpar_historico,
        style=ft.ButtonStyle(
            color=ft.colors.WHITE,
            bgcolor=ft.colors.RED_700,
        )
    )

    # Layout
    page.add(
        ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row([
                        ft.Text("Calculadora de Frete ANTT", size=30, weight=ft.FontWeight.BOLD),
                        btn_tema
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Divider(),
                    ft.Row([txt_origem, txt_destino]),
                    ft.Row([txt_distancia, dd_eixos]),
                    ft.Row([sw_ida_volta]),
                    ft.Row([btn_adicionar, btn_calcular_total, btn_limpar]),
                    ft.Divider(),
                    ft.Text("Destinos Adicionados:", size=16, weight=ft.FontWeight.BOLD),
                    lista_destinos,
                    ft.Divider(),
                    txt_resultado,
                    txt_estatisticas,
                    ft.Row([
                        btn_historico,
                        btn_exportar,
                        btn_limpar_historico
                    ], alignment=ft.MainAxisAlignment.END),
                ],
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
            expand=True,
            padding=20,
        )
    )

    # Certifique-se de que o histórico é carregado corretamente
    if os.path.exists('historico.json'):
        try:
            with open('historico.json', 'r') as f:
                historico_calculos = json.load(f)
        except:
            historico_calculos = []
    else:
        historico_calculos = []

    # Inicialização
    atualizar_historico()
    atualizar_estatisticas()

ft.app(target=main)
