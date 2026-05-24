import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import io


def generate_system_plot(temperaturas, energia, recon_errors, threshold):

    fig, ax = plt.subplots()

    ax.plot(temperaturas, label="Temperatura")
    ax.plot(energia, label="Energia")
    ax.plot(recon_errors, label="Erro Autoencoder")

    ax.axhline(y=threshold, linestyle="--", label="Threshold")

    ax.set_title("ColdGuardian AI - Monitoramento")
    ax.legend()

    buffer = io.BytesIO()
    plt.savefig(buffer, format="png")
    plt.close(fig)

    buffer.seek(0)
    return buffer