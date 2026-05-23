def generate_diagnostic(result):

    if result["status"] == "NORMAL":
        return (
            "Sistema operando normalmente."
        )

    elif result["status"] == "ATENCAO":
        return (
            "Foram detectadas pequenas anomalias "
            "operacionais. Recomenda-se monitoramento."
        )

    else:
        return (
            "Risco elevado detectado. "
            "O sistema apresenta comportamento "
            "compatível com perda de eficiência térmica."
        )