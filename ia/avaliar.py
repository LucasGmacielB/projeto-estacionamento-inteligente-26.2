
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf

from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay
)

BASE = Path(__file__).resolve().parent
MODELOS = BASE / "modelos"
RESULTADOS = BASE / "resultados"
TESTE = BASE / "dataset" / "teste"

RESULTADOS.mkdir(exist_ok=True)

# Carrega o modelo treinado
modelo = tf.keras.models.load_model(
    MODELOS / "placas_cnn.keras"
)

# Carrega as classes
classes = (MODELOS / "classes.txt").read_text(
    encoding="utf-8"
).splitlines()

# Carrega o conjunto de teste
teste = tf.keras.utils.image_dataset_from_directory(
    TESTE,
    image_size=(32, 32),
    color_mode="grayscale",
    batch_size=32,
    label_mode="int",
    shuffle=False
)

if teste.class_names != classes:
    raise ValueError("Classes do teste diferentes das classes do modelo!")

# Avalia o modelo
perda, acuracia = modelo.evaluate(teste, verbose=1)

# Obtém previsões e respostas corretas
previsoes = modelo.predict(teste, verbose=1)
y_pred = np.argmax(previsoes, axis=1)

y_true = np.concatenate([
    rotulos.numpy()
    for _, rotulos in teste
])

# Relatório por classe
relatorio = classification_report(
    y_true,
    y_pred,
    labels=list(range(len(classes))),
    target_names=classes,
    zero_division=0
)

print("\n========== RESULTADOS ==========")
print(f"Imagens avaliadas: {len(y_true)}")
print(f"Acurácia: {acuracia * 100:.2f}%")
print(f"Perda: {perda:.4f}")
print("================================\n")
print(relatorio)

# Salva relatório
texto = (
    f"Imagens avaliadas: {len(y_true)}\n"
    f"Acurácia: {acuracia * 100:.2f}%\n"
    f"Perda: {perda:.4f}\n\n"
    f"{relatorio}"
)

(RESULTADOS / "avaliacao.txt").write_text(
    texto,
    encoding="utf-8"
)

# Gera matriz de confusão
matriz = confusion_matrix(
    y_true,
    y_pred,
    labels=list(range(len(classes)))
)

fig, ax = plt.subplots(figsize=(15, 15))

display = ConfusionMatrixDisplay(
    confusion_matrix=matriz,
    display_labels=classes
)

display.plot(
    ax=ax,
    cmap="Blues",
    xticks_rotation=90,
    values_format="d",
    colorbar=False
)

plt.title("Matriz de Confusão - CNN")
plt.tight_layout()

plt.savefig(
    RESULTADOS / "matriz_confusao.png",
    dpi=150
)

plt.close()

print("\nAvaliação concluída!")
print("Arquivos salvos na pasta resultados/")
