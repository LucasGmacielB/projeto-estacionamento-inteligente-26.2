
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow.keras import layers, models

BASE = Path(__file__).resolve().parent

DATASET = BASE / "dataset"
MODELOS = BASE / "modelos"
RESULTADOS = BASE / "resultados"

MODELOS.mkdir(exist_ok=True)
RESULTADOS.mkdir(exist_ok=True)

TAMANHO = (32, 32)
BATCH_SIZE = 32
EPOCAS = 20
SEED = 42

tf.keras.utils.set_random_seed(SEED)

# Carrega as imagens organizadas por pastas
treino = tf.keras.utils.image_dataset_from_directory(
    DATASET / "treino",
    image_size=TAMANHO,
    color_mode="grayscale",
    batch_size=BATCH_SIZE,
    label_mode="int",
    shuffle=True,
    seed=SEED
)

validacao = tf.keras.utils.image_dataset_from_directory(
    DATASET / "validacao",
    image_size=TAMANHO,
    color_mode="grayscale",
    batch_size=BATCH_SIZE,
    label_mode="int",
    shuffle=False
)

classes = treino.class_names

assert classes == validacao.class_names

# Salva a ordem das classes para usar na previsão
(MODELOS / "classes.txt").write_text(
    "\n".join(classes),
    encoding="utf-8"
)

treino = treino.prefetch(tf.data.AUTOTUNE)
validacao = validacao.prefetch(tf.data.AUTOTUNE)

# CNN criada e inicializada do zero
modelo = models.Sequential([
    layers.Input(shape=(32, 32, 1)),
    layers.Rescaling(1.0 / 255),

    layers.Conv2D(32, (3, 3), activation="relu", padding="same"),
    layers.MaxPooling2D((2, 2)),

    layers.Conv2D(64, (3, 3), activation="relu", padding="same"),
    layers.MaxPooling2D((2, 2)),

    layers.Conv2D(128, (3, 3), activation="relu", padding="same"),
    layers.MaxPooling2D((2, 2)),

    layers.Flatten(),
    layers.Dense(128, activation="relu"),
    layers.Dropout(0.3),
    layers.Dense(len(classes), activation="softmax")
])

modelo.compile(
    optimizer="adam",
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"]
)

modelo.summary()

callbacks = [
    tf.keras.callbacks.EarlyStopping(
        monitor="val_loss",
        patience=5,
        restore_best_weights=True
    )
]

historico = modelo.fit(
    treino,
    validation_data=validacao,
    epochs=EPOCAS,
    callbacks=callbacks
)

import json

with open(RESULTADOS / "historico.json", "w") as arquivo:
    json.dump(historico.history, arquivo, indent=4)

# Salva o modelo treinado
modelo.save(MODELOS / "placas_cnn.keras")

# Gráficos de treinamento
plt.figure(figsize=(10, 4))

plt.plot(historico.history["accuracy"], label="Treinamento")
plt.plot(historico.history["val_accuracy"], label="Validação")

plt.title("Acurácia da CNN")
plt.xlabel("Épocas")
plt.ylabel("Acurácia")
plt.legend()
plt.grid(True)

plt.savefig(RESULTADOS / "acuracia.png", bbox_inches="tight")
plt.close()

plt.figure(figsize=(10, 4))

plt.plot(historico.history["loss"], label="Treinamento")
plt.plot(historico.history["val_loss"], label="Validação")

plt.title("Perda da CNN")
plt.xlabel("Épocas")
plt.ylabel("Loss")
plt.legend()
plt.grid(True)

plt.savefig(RESULTADOS / "perda.png", bbox_inches="tight")
plt.close()

print("\nTreinamento concluído!")
print("Modelo salvo em modelos/placas_cnn.keras")
print("Gráficos salvos na pasta resultados/")