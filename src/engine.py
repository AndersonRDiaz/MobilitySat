import os
from pathlib import Path
from dotenv import load_dotenv
from ollama import Client

from src import telemetria, alertas

load_dotenv()

TRILHA = "mobilitysat"

client = Client(
    host="https://api.ollama.com",
    headers={'Authorization': 'Bearer ' + os.environ.get('OLLAMA_API_KEY', '')}
)

# ─── Função de chamada ao LLM ────────────────────────────────────────────────

def llm(prompt: str, system: str | None = None, max_tokens: int = 900, temperature: float = 0.3) -> str:
    """Envia um prompt ao modelo gpt-oss:120b via Ollama Cloud. """
    mensagens = []
    if system:
        mensagens.append({"role": "system", "content": system})
    mensagens.append({"role": "user", "content": prompt})
    try:
        resposta = client.chat(
            model="gpt-oss:120b", messages=mensagens,
            options={"num_predict": max_tokens, "temperature": temperature},
            stream=False,
        )
        return resposta["message"]["content"].strip()
    except Exception as e:
        return f"⚠️  Erro ao consultar IA: {e}"


# ─── Carregamento do system prompt ───────────────────────────────────────────
def _carregar_system_prompt() -> str:
    """Lê o system prompt do arquivo prompts/system_prompt.md."""
    caminho = Path("prompts/system_prompt.md")
    if caminho.exists():
        return caminho.read_text(encoding="utf-8")
    # Fallback mínimo caso o arquivo não exista
    return (
        "Você é o Mission Control AI, sistema de monitoramento do satélite GNSS MobilitySat. "
        "Analise os dados de telemetria e explique o impacto terrestre de cada anomalia."
    )

# ─── Classe principal ─────────────────────────────────────────────────────────
class MissionEngine:
    """ Motor central do MobilitySat.
    Mantém o modo de simulação atual e o histórico das últimas leituras. """
    def __init__(self):
        self.trilha = TRILHA
        self.system_prompt = _carregar_system_prompt()
        self.modo_simulacao = "normal"          # "normal" | "degradado" | "critico"
        self.historico_telemetria: list[dict] = []   # últimas leituras para contexto temporal
        self._dados_atuais: dict = {}
        self._resultado_alertas: dict = {}


    # ── Método obrigatório pelo enunciado ────────────────────────────────────
    def is_ready(self) -> bool:
        return True


    # ── Snapshot do status atual ─────────────────────────────────────────────
    def status_snapshot(self) -> str:
        """ Retorna um texto formatado com a telemetria atual + alertas ativos. 
        Chamado pelo comando /status na CLI. """

        dados = telemetria.coletar(self.modo_simulacao)
        resultado = alertas.avaliar(dados)
        self._dados_atuais = dados
        self._resultado_alertas = resultado

        # Guardar no histórico (máx 5 leituras para não estourar o prompt)
        self.historico_telemetria.append(dados)
        if len(self.historico_telemetria) > 5:
            self.historico_telemetria.pop(0)

        linhas = [
            f"🛰️  MobilitySat — Status em {dados['timestamp']}",
            f"Modo de simulação: {dados['modo_simulacao'].upper()}",
            "",
            telemetria.formatar_para_prompt(dados),
            "",
            resultado["resumo"],
        ]

        if resultado["alertas"]:
            linhas.append("")
            for a in resultado["alertas"]:
                emoji = "🚨" if a["nivel"] == "critico" else "⚠️ "
                linhas.append(f"  {emoji} {a['mensagem']}")
                if a.get("acao"):
                    linhas.append(f"     {a['acao']}")

        return "\n".join(linhas)
    

    # ── Análise principal com IA ──────────────────────────────────────────────
    def analyze(self, pergunta_usuario: str) -> str:
        """
        Ponto central de integração. Recebe a pergunta do operador,
        coleta telemetria fresca, avalia alertas e consulta a IA com tudo isso.
        """

        # Comandos especiais de modo de simulação
        if pergunta_usuario.startswith("/modo "):
            return self._trocar_modo(pergunta_usuario.split(" ", 1)[1].strip())

        # 1. Coletar dados atuais src.telemetria.coletar()
        dados = telemetria.coletar(self.modo_simulacao)
        resultado = alertas.avaliar(dados)

        # Guardar para uso no status_snapshot
        self._dados_atuais = dados
        self._resultado_alertas = resultado

        # Atualizar histórico
        self.historico_telemetria.append(dados)
        if len(self.historico_telemetria) > 5:
            self.historico_telemetria.pop(0)

        # 2. Montar contexto de histórico (memória temporal) src.alertas.avaliar(dados)
        historico_txt = ""
        if len(self.historico_telemetria) > 1:
            historico_txt = "\nHISTÓRICO RECENTE (últimas leituras):\n"
            for h in self.historico_telemetria[:-1]:  # todas menos a atual
                historico_txt += (
                    f"  [{h['timestamp']}] drift={h['drift_oscilador']}ns | "
                    f"sinc={h['sincronizacao']}% | "
                    f"sinal={h['precisao_sinal']}m | "
                    f"potência={h['margem_potencia']}%\n"
                )

        # 3. Montar o prompt completo com dados reais injetados
        prompt = f"""
            {telemetria.formatar_para_prompt(dados)}

            {alertas.formatar_alertas_para_prompt(resultado)}
            {historico_txt}
            NÍVEL GERAL: {resultado['nivel_geral'].upper()}

            PERGUNTA DO OPERADOR: {pergunta_usuario}

            Responda de forma clara e objetiva. Conecte sempre a análise técnica ao impacto
            terrestre (frotas logísticas, agricultura de precisão, veículos autônomos).
            """.strip()

        # 4. Consultar o modelo (prompt, system=self.system_prompt)
        resposta = llm(prompt, system=self.system_prompt)
        return resposta
    
    

    # ── Troca de modo de simulação ───────────────────────────────────────────
    def _trocar_modo(self, novo_modo: str) -> str:
        modos_validos = ["normal", "degradado", "critico"]
        if novo_modo not in modos_validos:
            return f"⚠️  Modo inválido. Use: /modo normal | /modo degradado | /modo critico"
        self.modo_simulacao = novo_modo
        return f"✅ Modo de simulação alterado para: {novo_modo.upper()}"
