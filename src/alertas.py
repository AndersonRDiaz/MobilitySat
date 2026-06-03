"""
Módulo de alertas — MobilitySat
Contém as regras de decisão implementadas em Python (não delegadas à IA).

Conceito importante: a lógica de "é crítico ou não" deve estar no código,
não no prompt. A IA serve para EXPLICAR e CONTEXTUALIZAR, não para decidir.
"""


# ─── Thresholds (limites que disparam alertas) ────────────────────────────────

THRESHOLDS = {
    "drift_oscilador": {
        "aviso":   10.0,   # ns — começa a degradar precisão
        "critico": 20.0,   # ns — inutilizável para GNSS de alta precisão
    },
    "sincronizacao": {
        "aviso":   95.0,   # % — receptores começam a perder lock
        "critico": 85.0,   # % — perda generalizada de sinal
    },
    "precisao_sinal": {
        "aviso":   3.0,    # m — agricultura de precisão começa a falhar
        "critico": 8.0,    # m — frotas e veículos autônomos não podem operar
    },
    "precisao_efemeride": {
        "aviso":   2.0,    # m — cálculo de posição degradado
        "critico": 5.0,    # m — erros graves de navegação
    },
    "margem_potencia": {
        "aviso":   25.0,   # % — atenção ao consumo
        "critico": 15.0,   # % — acionar modo de economia de emergência
    },
}


# ─── Ações automáticas para situações críticas ───────────────────────────────

def acao_automatica(parametro: str, nivel: str) -> str | None:
    """
    Retorna uma ação automática quando um parâmetro entra em estado crítico.
    Estas ações seriam executadas de forma autônoma num sistema real.
    """
    acoes = {
        ("drift_oscilador", "critico"):    "🔄 Iniciando resincronização do oscilador atômico via referência ground...",
        ("sincronizacao", "critico"):      "📡 Ativando protocolo de reconexão à constelação GNSS...",
        ("precisao_sinal", "critico"):     "⚙️  Alternando para modo de transmissão de backup (L5 prioritário)...",
        ("precisao_efemeride", "critico"): "🛰️  Solicitando uplink de efemérides corrigidas ao centro de controle...",
        ("margem_potencia", "critico"):    "⚡ MODO DE EMERGÊNCIA ATIVADO — desligando subsistemas não essenciais...",
    }
    return acoes.get((parametro, nivel))


# ─── Função principal de avaliação ───────────────────────────────────────────

def avaliar(dados: dict) -> dict:
    """
    Recebe os dados de telemetria e retorna um relatório de alertas.

    Retorna:
      {
        "nivel_geral": "normal" | "aviso" | "critico",
        "alertas": [ { "parametro", "valor", "nivel", "mensagem", "acao" } ],
        "resumo": "texto curto para exibir no terminal"
      }
    """
    alertas = []

    # ── Drift do oscilador (quanto maior, pior) ──────────────────────────────
    drift = dados["drift_oscilador"]
    if drift >= THRESHOLDS["drift_oscilador"]["critico"]:
        alertas.append(_montar_alerta(
            "drift_oscilador", drift, "critico",
            f"Drift de {drift} ns está CRÍTICO — erro de posicionamento de até {drift * 30:.0f} cm acumulado."
        ))
    elif drift >= THRESHOLDS["drift_oscilador"]["aviso"]:
        alertas.append(_montar_alerta(
            "drift_oscilador", drift, "aviso",
            f"Drift de {drift} ns — monitorar. Agricultura de precisão pode ser afetada."
        ))

    # ── Sincronização (quanto menor, pior) ───────────────────────────────────
    sinc = dados["sincronizacao"]
    if sinc < THRESHOLDS["sincronizacao"]["critico"]:
        alertas.append(_montar_alerta(
            "sincronizacao", sinc, "critico",
            f"Sincronização em {sinc}% — receptores terrestres estão perdendo lock. Frotas cegas."
        ))
    elif sinc < THRESHOLDS["sincronizacao"]["aviso"]:
        alertas.append(_montar_alerta(
            "sincronizacao", sinc, "aviso",
            f"Sincronização em {sinc}% — instabilidade detectada. Risco de degradação de serviço."
        ))

    # ── Precisão do sinal (quanto maior, pior) ───────────────────────────────
    prec_sinal = dados["precisao_sinal"]
    if prec_sinal >= THRESHOLDS["precisao_sinal"]["critico"]:
        alertas.append(_montar_alerta(
            "precisao_sinal", prec_sinal, "critico",
            f"Precisão {prec_sinal} m — veículos autônomos e frotas NÃO podem operar com segurança."
        ))
    elif prec_sinal >= THRESHOLDS["precisao_sinal"]["aviso"]:
        alertas.append(_montar_alerta(
            "precisao_sinal", prec_sinal, "aviso",
            f"Precisão {prec_sinal} m — agricultura de precisão degradada. Plantadeiras autônomas afetadas."
        ))

    # ── Precisão da efeméride (quanto maior, pior) ───────────────────────────
    prec_ef = dados["precisao_efemeride"]
    if prec_ef >= THRESHOLDS["precisao_efemeride"]["critico"]:
        alertas.append(_montar_alerta(
            "precisao_efemeride", prec_ef, "critico",
            f"Efeméride com erro de {prec_ef} m — cálculo de órbita transmitido está incorreto."
        ))
    elif prec_ef >= THRESHOLDS["precisao_efemeride"]["aviso"]:
        alertas.append(_montar_alerta(
            "precisao_efemeride", prec_ef, "aviso",
            f"Efeméride com erro de {prec_ef} m — monitorar degradação de posicionamento."
        ))

    # ── Margem de potência (quanto menor, pior) ──────────────────────────────
    potencia = dados["margem_potencia"]
    if potencia < THRESHOLDS["margem_potencia"]["critico"]:
        alertas.append(_montar_alerta(
            "margem_potencia", potencia, "critico",
            f"Potência em {potencia}% — risco de desligamento de subsistemas de transmissão."
        ))
    elif potencia < THRESHOLDS["margem_potencia"]["aviso"]:
        alertas.append(_montar_alerta(
            "margem_potencia", potencia, "aviso",
            f"Potência em {potencia}% — reduzir carga nos próximos ciclos de sombra."
        ))

    # ── Determinar nível geral ────────────────────────────────────────────────
    niveis = [a["nivel"] for a in alertas]
    if "critico" in niveis:
        nivel_geral = "critico"
    elif "aviso" in niveis:
        nivel_geral = "aviso"
    else:
        nivel_geral = "normal"

    # ── Montar resumo legível ─────────────────────────────────────────────────
    if nivel_geral == "normal":
        resumo = "✅ Todos os parâmetros dentro do nominal. Missão operando normalmente."
    elif nivel_geral == "aviso":
        resumo = f"⚠️  {len(alertas)} alerta(s) de atenção detectado(s). Monitoramento recomendado."
    else:
        criticos = sum(1 for a in alertas if a["nivel"] == "critico")
        resumo = f"🚨 {criticos} alerta(s) CRÍTICO(s)! Ação imediata necessária."

    return {
        "nivel_geral": nivel_geral,
        "alertas": alertas,
        "resumo": resumo,
    }


def formatar_alertas_para_prompt(resultado: dict) -> str:
    """Converte o relatório de alertas em texto para injetar no prompt da IA."""
    if not resultado["alertas"]:
        return "ALERTAS: Nenhum alerta ativo. Missão nominal."

    linhas = ["ALERTAS DETECTADOS:"]
    for a in resultado["alertas"]:
        emoji = "🚨" if a["nivel"] == "critico" else "⚠️ "
        linhas.append(f"  {emoji} [{a['nivel'].upper()}] {a['parametro']}: {a['mensagem']}")
        if a.get("acao"):
            linhas.append(f"     → Ação automática: {a['acao']}")

    return "\n".join(linhas)


# ─── Auxiliar interno ─────────────────────────────────────────────────────────

def _montar_alerta(parametro: str, valor: float, nivel: str, mensagem: str) -> dict:
    acao = acao_automatica(parametro, nivel)
    return {
        "parametro": parametro,
        "valor": valor,
        "nivel": nivel,
        "mensagem": mensagem,
        "acao": acao,
    }