from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import flet as ft
import uvicorn

app = FastAPI()

# Configurar arquivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

def main(page: ft.Page):
    page.title = "Calculadora de Frete"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.scroll = "auto"
    
    # ... resto do seu código ...

@app.get("/")
async def read_root():
    return ft.app(target=main, view=ft.WEB_BROWSER)

if __name__ == "__main__":
    # Executar com uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8080, reload=True)
