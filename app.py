import flet as ft
from flet import Page
from datetime import datetime
from fpdf import FPDF
import json
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

async def main(page: Page):
    page.title = "Calculadora de Frete"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.scroll = "auto"
    
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
        width=200,
        hint_text="Distância será calculada automaticamente",
        read_only=True
    )
    
    dd_eixos = ft.Dropdown(
        label="Número de Eixos",
        width=200,
        options=[
            ft.dropdown.Option("2"),
            ft.dropdown.Option("3"),
            ft.dropdown.Option("4"),
            ft.dropdown.Option("5"),
            ft.dropdown.Option("6"),
            ft.dropdown.Option("7"),
            ft.dropdown.Option("8"),
            ft.dropdown.Option("9")
        ]
    )
    
    txt_resultado = ft.Text(
        size=20,
        weight=ft.FontWeight.BOLD
    )
    
    # Layout
    await page.add_async(
        ft.Container(
            content=ft.Column([
                ft.Text("Calculadora de Frete", size=30, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Row([txt_origem, txt_destino], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([txt_distancia, dd_eixos], alignment=ft.MainAxisAlignment.CENTER),
                txt_resultado
            ]),
            padding=20
        )
    )

if __name__ == "__main__":
    ft.app(target=main, view=ft.WEB_BROWSER, port=8081)
