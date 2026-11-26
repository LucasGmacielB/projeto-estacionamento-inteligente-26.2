
#include <Servo.h>

const bool modoDebug = true;

// Faixa de deteccao do veiculo (cm)
const int distanciaMinima = 2;
const int distanciaMaxima = 15;

const unsigned long timeoutEcho = 40000;

// Angulos dos servos
const int fechado = 0;
const int aberto = 90;

// Configuracoes de tempo
const int leiturasParaConfirmar = 3;
const unsigned long tempoAberto = 5000;
const unsigned long intervaloDistancia = 500;
const unsigned long tempoFimComando = 100;


// Mede a distancia uma vez
long medirDistancia(byte trig, byte echo) {
  digitalWrite(trig, LOW);
  delayMicroseconds(2);

  digitalWrite(trig, HIGH);
  delayMicroseconds(10);

  digitalWrite(trig, LOW);

  unsigned long tempo = pulseIn(
    echo, HIGH, timeoutEcho
  );

  if (tempo == 0) {
    return -1;
  }

  return tempo / 58;
}


// Realiza 5 leituras e retorna a mediana
long medirMediana(byte trig, byte echo) {
  long leituras[5];

  for (int i = 0; i < 5; i++) {
    leituras[i] = medirDistancia(trig, echo);
    delay(60);
  }

  for (int i = 0; i < 4; i++) {
    for (int j = i + 1; j < 5; j++) {
      if (leituras[j] < leituras[i]) {
        long troca = leituras[i];
        leituras[i] = leituras[j];
        leituras[j] = troca;
      }
    }
  }

  return leituras[2];
}


// Estrutura de cada portao
struct Portao {
  const char* nome;

  byte trig;
  byte echo;
  byte pinoServo;

  Servo servo;

  bool ocupado;
  bool aberta;
  bool sensorComErro;

  int contador;
  long distancia;

  unsigned long aberturaEm;

  Portao(
    const char* nome,
    byte trig,
    byte echo,
    byte pinoServo
  )
    : nome(nome),
      trig(trig),
      echo(echo),
      pinoServo(pinoServo),
      ocupado(false),
      aberta(false),
      sensorComErro(false),
      contador(0),
      distancia(-1),
      aberturaEm(0) {}


  // Envia eventos para o Python
  void enviar(const char* evento) {
    Serial.print(evento);
    Serial.print(":");
    Serial.println(nome);
  }


  // Verifica o estado do sensor
  void verificarSensor(bool comErro) {
    if (comErro == sensorComErro) {
      return;
    }

    sensorComErro = comErro;

    enviar(
      comErro ? "ERRO_SENSOR" : "SENSOR_OK"
    );
  }


  // Detecta a presenca do veiculo
  void lerSensor() {
    distancia = medirMediana(trig, echo);

    verificarSensor(distancia < distanciaMinima);

    if (sensorComErro) {
      contador = 0;
      return;
    }

    bool detectou = distancia <= distanciaMaxima;

    // Exige leituras consecutivas
    if (detectou == ocupado) {
      contador = 0;
      return;
    }

    contador++;

    if (contador < leiturasParaConfirmar) {
      return;
    }

    contador = 0;
    ocupado = detectou;

    enviar(
      ocupado
        ? "CARRO_DETECTADO"
        : "SENSOR_LIVRE"
    );
  }


  // Abre a cancela
  void abrir() {
    if (!servo.attached()) {
      enviar("ERRO_SERVO");
      return;
    }

    aberturaEm = millis();

    if (aberta) {
      return;
    }

    servo.write(aberto);
    aberta = true;

    enviar("CANCELA_ABERTA");
  }


  // Fecha a cancela
  void fechar() {
    if (!servo.attached()) {
      enviar("ERRO_SERVO");
      return;
    }

    servo.write(fechado);
    aberta = false;

    enviar("CANCELA_FECHADA");
  }


  // Atualiza o estado do portao
  void atualizar() {
    lerSensor();

    if (
      aberta &&
      !sensorComErro &&
      !ocupado &&
      millis() - aberturaEm >= tempoAberto
    ) {
      fechar();
    }
  }


  // Exibe a distancia no monitor serial
  void mostrarDistancia() {
    Serial.print(nome);
    Serial.print("=");

    if (distancia < 0) {
      Serial.print("sem_resposta");
    } else {
      Serial.print(distancia);
      Serial.print("cm");
    }

    Serial.print(" [");

    if (sensorComErro) {
      Serial.print("ERRO");
    } else if (ocupado) {
      Serial.print("OCUPADO");
    } else {
      Serial.print("LIVRE");
    }

    Serial.print("]");
  }


  // Inicializa sensor e servo
  void iniciar() {
    pinMode(trig, OUTPUT);
    pinMode(echo, INPUT);

    digitalWrite(trig, LOW);

    servo.attach(pinoServo);

    if (servo.attached()) {
      servo.write(fechado);
      enviar("SERVO_INICIALIZADO");
    } else {
      enviar("ERRO_SERVO");
    }
  }
};


// CONFIGURACAO DOS PINOS
// Nome, TRIG, ECHO, SERVO

Portao entrada("ENTRADA", 4, 10, 5);
Portao saida("SAIDA", 9, 11, 8);


// COMUNICACAO SERIAL

char comando[32];

byte tamanhoComando = 0;

unsigned long ultimoCaractere = 0;
unsigned long ultimaDistancia = 0;


// Executa comandos recebidos do Python
void executarComando() {
  comando[tamanhoComando] = '\0';

  Serial.print("COMANDO_RECEBIDO:");
  Serial.println(comando);

  if (strcmp(comando, "ABRIR:ENTRADA") == 0) {
    entrada.abrir();

  } else if (strcmp(comando, "ABRIR:SAIDA") == 0) {
    saida.abrir();

  } else {
    Serial.print("ERRO_COMANDO:");
    Serial.println(comando);
  }

  tamanhoComando = 0;
}


// Le os comandos da porta serial
void lerComandos() {
  while (Serial.available() > 0) {
    char c = Serial.read();

    ultimoCaractere = millis();

    if (c == '\n' || c == '\r') {
      if (tamanhoComando > 0) {
        executarComando();
      }

    } else if (
      tamanhoComando < sizeof(comando) - 1
    ) {
      comando[tamanhoComando++] = toupper(c);
    }
  }

  if (
    tamanhoComando > 0 &&
    millis() - ultimoCaractere >= tempoFimComando
  ) {
    executarComando();
  }
}


// Exibe as distancias dos sensores
void mostrarDistancias() {
  if (
    !modoDebug ||
    millis() - ultimaDistancia < intervaloDistancia
  ) {
    return;
  }

  ultimaDistancia = millis();

  Serial.print("# DISTANCIA ");

  entrada.mostrarDistancia();

  Serial.print(" | ");

  saida.mostrarDistancia();

  Serial.println();
}


// Inicializacao
void setup() {
  Serial.begin(9600);

  entrada.iniciar();
  saida.iniciar();

  Serial.println("PRONTO");
}


// Loop principal
void loop() {
  lerComandos();

  entrada.atualizar();

  lerComandos();

  saida.atualizar();

  mostrarDistancias();
}
