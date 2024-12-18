import flet
from flet import Page, TextField, Dropdown, Column, Row, Text, FontWeight, MainAxisAlignment, Divider

def main(page: Page):
    page.title = "Calculadora de Frete"
    page.window_width = 800
    page.window_height = 600
    page.window_resizable = True
    page.padding = 20
    
    # Campos de entrada
    txt_origem = TextField(
        label="Cidade de Origem",
        width=300,
        height=50,
        hint_text="Ex: São Paulo, SP"
    )
    
    txt_destino = TextField(
        label="Cidade de Destino",
        width=300,
        height=50,
        hint_text="Ex: Rio de Janeiro, RJ"
    )
    
    dd_eixos = Dropdown(
        label="Número de Eixos",
        width=200,
        options=[
            flet.dropdown.Option("2"),
            flet.dropdown.Option("3"),
            flet.dropdown.Option("4"),
            flet.dropdown.Option("5"),
            flet.dropdown.Option("6"),
            flet.dropdown.Option("7"),
            flet.dropdown.Option("8"),
            flet.dropdown.Option("9")
        ]
    )
    
    # Layout
    page.add(
        Column(
            controls=[
                Text("Calculadora de Frete", size=30, weight=FontWeight.BOLD),
                Divider(),
                Row(
                    [txt_origem, txt_destino],
                    alignment=MainAxisAlignment.CENTER
                ),
                Row(
                    [dd_eixos],
                    alignment=MainAxisAlignment.CENTER
                )
            ],
            spacing=20,
            alignment=MainAxisAlignment.START,
        )
    )

if __name__ == "__main__":
    flet.app(target=main)
