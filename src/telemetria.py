"""
Módulo de telemetria — MobilitySat (GNSS e Mobilidade)
Simula os dados de um satélite GNSS similar ao GPS/Galileo.

Parâmetros monitorados:
  - drift_oscilador:   desvio do oscilador atômico (nanossegundos)
  - sincronizacao:     sincronização com a constelação (%)
  - precisao_sinal:    precisão do sinal L1/L5 (metros)
  - precisao_efemeride: erro na efeméride transmitida (metros)
  - margem_potencia:   margem de energia disponível (%)
"""

import random
from datetime import datetime


# ─── Limites normais de cada parâmetro ───────────────────────────────────────
# Estes valores definem o que é "saudável" para um satélite GNSS real.
LIMITES_NORMAIS = {
    "drift_oscilador":    {"min": 0.0,  "max": 10.0},   # ns — acima de 10 ns começa a degradar precisão
    "sincronizacao":      {"min": 95.0, "max": 100.0},  # % — abaixo de 95% os receptores perdem lock
    "precisao_sinal":     {"min": 0.5,  "max": 3.0},    # m — acima de 3 m a agricultura de precisão falha
    "precisao_efemeride": {"min": 0.0,  "max": 2.0},    # m — acima de 2 m o cálculo de posição fica impreciso
    "margem_potencia":    {"min": 20.0, "max": 100.0},  # % — abaixo de 20% entra modo de emergência
}


def coletar(modo: str = "normal") -> dict:
    """
    Gera uma leitura simulada da telemetria do satélite.

    Parâmetros:
      modo: "normal"   → valores dentro do range saudável
            "degradado" → um ou dois parâmetros levemente fora do normal
            "critico"   → falha grave em pelo menos um parâmetro

    Retorna um dicionário com todos os parâmetros + timestamp.
    """

    if modo == "normal":
        dados = {
            "drift_oscilador":    round(random.uniform(0.5, 8.0), 2),
            "sincronizacao":      round(random.uniform(97.0, 100.0), 2),
            "precisao_sinal":     round(random.uniform(0.5, 2.5), 2),
            "precisao_efemeride": round(random.uniform(0.1, 1.8), 2),
            "margem_potencia":    round(random.uniform(40.0, 95.0), 2),
        }

    elif modo == "degradado":
        dados = {
            "drift_oscilador":    round(random.uniform(10.0, 18.0), 2),   # ⚠️ levemente alto
            "sincronizacao":      round(random.uniform(90.0, 95.0), 2),   # ⚠️ caindo
            "precisao_sinal":     round(random.uniform(3.0, 5.0), 2),     # ⚠️ degradada
            "precisao_efemeride": round(random.uniform(1.8, 3.0), 2),
            "margem_potencia":    round(random.uniform(25.0, 40.0), 2),
        }

    elif modo == "critico":
        dados = {
            "drift_oscilador":    round(random.uniform(25.0, 50.0), 2),   # 🚨 crítico
            "sincronizacao":      round(random.uniform(60.0, 85.0), 2),   # 🚨 perda de lock
            "precisao_sinal":     round(random.uniform(8.0, 15.0), 2),    # 🚨 inutilizável
            "precisao_efemeride": round(random.uniform(5.0, 10.0), 2),    # 🚨 posição errada
            "margem_potencia":    round(random.uniform(5.0, 18.0), 2),    # 🚨 modo emergência
        }

    else:
        # Fallback — coleta normal
        dados = coletar("normal")

    dados["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    dados["modo_simulacao"] = modo
    return dados


def formatar_para_prompt(dados: dict) -> str:
    """
    Converte o dicionário de telemetria em texto estruturado para injetar no prompt da IA.
    A IA precisa receber os dados de forma clara para analisá-los corretamente.
    """
    return f"""
TELEMETRIA — MobilitySat GNSS | {dados['timestamp']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Drift do Oscilador Atômico : {dados['drift_oscilador']} ns      (normal: 0–10 ns)
  Sincronização Constelação  : {dados['sincronizacao']} %        (normal: ≥95%)
  Precisão do Sinal L1/L5   : {dados['precisao_sinal']} m        (normal: ≤3 m)
  Precisão da Efeméride     : {dados['precisao_efemeride']} m    (normal: ≤2 m)
  Margem de Potência        : {dados['margem_potencia']} %       (normal: ≥20%)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""".strip()