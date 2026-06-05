"""Interface CLI estilo Claude Code — usa Rich + prompt-toolkit."""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
import pyfiglet
from datetime import datetime


console = Console()
session = PromptSession(style=Style.from_dict({"prompt": "#06B6D4 bold"}))

def show_banner():
    """Exibe banner ASCII colorido mantendo a estrutura original."""
    # Dividimos em partes para aplicar cores diferentes
    parte1 = pyfiglet.figlet_format("MISSION CONTROL AI", font="ansi_shadow")
    parte2 = pyfiglet.figlet_format("MOBILITY - SAT ", font="ansi_shadow")
    
    console.print(Text(parte1, style="bold #06B6D4")) # Ciano (Claude)
    console.print(Text(parte2, style="bold #F8910B")) # Laranja (Claude)
    
    console.print(Panel.fit(
        "Sistema de monitoramento e análise por IA generativa.\n"
        "Use /help para ver os comandos · /exit para sair.\n"
        "Modelo: gpt-oss:120b via Ollama Cloud",
        title="◆ MobilitySat", border_style="#F8910B"
    ))

def show_response(text):
    """Renderiza resposta da IA mantendo a estrutura original."""
    now = datetime.now().strftime("%H:%M")
    # Mantemos o border_style laranja como você pediu
    console.print(Panel(text, title="◆ Mobility\nSat",
                        subtitle=now, border_style="#F8910B"))
    

def run_cli(engine):
    """Loop principal da CLI."""
    show_banner()
    if not engine.is_ready():
        console.print(" ⚠ Engine status: AGUARDANDO IMPLEMENTAÇÃO ✗\n",
                    style="yellow")
    while True:
        try:
            user_input = session.prompt("❯ ").strip()
        except (KeyboardInterrupt, EOFError):
            break
        if not user_input:
            continue
        if user_input == "/exit":
            break
        if user_input == "/help":
            console.print("Comandos: /help /status /about /clear /exit")
            continue
        if user_input == "/status":
            show_response(engine.status_snapshot())
            continue
        if user_input == "/clear":
            console.clear(); show_banner(); continue
        
        # Qualquer outra entrada vai para o motor de análise
        resposta = engine.analyze(user_input)
        show_response(resposta)
