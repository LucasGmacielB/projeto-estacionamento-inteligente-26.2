#include <Servo.h>

const bool modoDebug = true;

// Faixa em que o carro e considerado detectado (em cm)
const int distanciaMinima = 6;
const int distanciaMaxima = 20;

// Tempo maximo de espera pelo eco (em microssegundos).
// Sem objeto na frente o sensor ainda responde (~38000 us),
// entao "sem resposta" so acontece se o sensor estiver com problema
const unsigned long timeoutEcho = 40000;

const int fechado = 0;
const int aberto = 90;

const int leiturasParaConfirmar = 3;
const unsigned long tempoAberto = 5000;
const unsigned long intervaloDistancia = 500;
const unsigned long tempoFimComando = 100;

// Mede a distancia uma vez
long medirDistancia(byte trig, byte echo) {
  // Pulso de 10 microssegundos no TRIG faz o sensor emitir o som
  digitalWrite(trig, LOW);
  delayMicroseconds(2);
  digitalWrite(trig, HIGH);
  delayMicroseconds(10);
  digitalWrite(trig, LOW);

  // Tempo (em microssegundos) que o som levou para ir e voltar
  unsigned long tempo = pulseIn(echo, HIGH, timeoutEcho);

  // Sem resposta do sensor
  if (tempo == 0) {
    return -1;
  }

  // O som anda 0,0343 cm por microssegundo e faz ida e volta:
  // distancia = tempo / 2 * 0,0343  =  tempo / 58
  return tempo / 58;
}

// Faz 5 leituras e usa a do meio (mediana) para ignorar leituras erradas
long medirMediana(byte trig, byte echo) {
  long leituras[5];

  for (int i = 0; i < 5; i++) {
    leituras[i] = medirDistancia(trig, echo);
    delay(15);
  }

  // Coloca as 5 leituras em ordem crescente
  for (int i = 0; i < 4; i++) {
    for (int j = i + 1; j < 5; j++) {
      if (leituras[j] < leituras[i]) {
        long troca = leituras[i];
        leituras[i] = leituras[j];
        leituras[j] = troca;
      }
    }
  }

  // A terceira leitura (posicao 2) e a do meio
  return leituras[2];
}

struct Portao {
  const char* nome;
  byte ledVermelho;
  byte ledVerde;
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

  Portao(const char* nome, byte vermelho, byte verde, byte trig, byte echo, byte pinoServo)
    : nome(nome), ledVermelho(vermelho), ledVerde(verde), trig(trig), echo(echo),
      pinoServo(pinoServo), ocupado(false), aberta(false), sensorComErro(false),
      contador(0), distancia(-1), aberturaEm(0) {}

  void enviar(const char* evento) {
    Serial.print(evento);
    Serial.print(":");
    Serial.println(nome);
  }

  void sinalizar(bool liberado) {
    digitalWrite(ledVerde, liberado);
    digitalWrite(ledVermelho, !liberado);
  }

  void verificarSensor(bool comErro) {
    if (comErro == sensorComErro) {
      return;
    }
    sensorComErro = comErro;
    enviar(comErro ? "ERRO_SENSOR" : "SENSOR_OK");
  }

  void lerSensor() {
    distancia = medirMediana(trig, echo);
    verificarSensor(distancia < 0);

    if (sensorComErro) {
      return;
    }

    // Detectado quando a distancia esta dentro da faixa
    bool detectou = distancia >= distanciaMinima && distancia <= distanciaMaxima;

    if (detectou != ocupado) {
      contador++;
    } else if (contador > 0) {
      contador--;
    }

    if (contador < leiturasParaConfirmar) {
      return;
    }

    contador = 0;
    ocupado = detectou;
    enviar(ocupado ? "CARRO_DETECTADO" : "SENSOR_LIVRE");
  }

  void abrir() {
    aberturaEm = millis();

    if (aberta) {
      return;
    }

    aberta = true;
    servo.write(aberto);
    sinalizar(true);
    enviar("CANCELA_ABERTA");
  }

  void fechar() {
    aberta = false;
    servo.write(fechado);
    sinalizar(false);
    enviar("CANCELA_FECHADA");
  }

  void atualizar() {
    lerSensor();

    if (aberta && !ocupado && millis() - aberturaEm >= tempoAberto) {
      fechar();
    }
  }

  void mostrarDistancia() {
    Serial.print(nome);
    Serial.print("=");

    if (distancia < 0) {
      Serial.print("sem_resposta");
    } else {
      Serial.print(distancia);
      Serial.print("cm");
    }
  }

  void iniciar() {
    pinMode(ledVermelho, OUTPUT);
    pinMode(ledVerde, OUTPUT);
    pinMode(trig, OUTPUT);
    pinMode(echo, INPUT);
    servo.attach(pinoServo);
    servo.write(fechado);
    sinalizar(false);
  }
};

Portao entrada("ENTRADA", 2, 3, 4, 10, 5);
Portao saida("SAIDA", 7, 6, 9, 11, 8);

char comando[32];
byte tamanhoComando = 0;
unsigned long ultimoCaractere = 0;
unsigned long ultimaDistancia = 0;

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

void lerComandos() {
  while (Serial.available() > 0) {
    char c = Serial.read();
    ultimoCaractere = millis();

    if (c == '\n' || c == '\r') {
      if (tamanhoComando > 0) {
        executarComando();
      }
    } else if (tamanhoComando < sizeof(comando) - 1) {
      comando[tamanhoComando++] = toupper(c);
    }
  }

  if (tamanhoComando > 0 && millis() - ultimoCaractere >= tempoFimComando) {
    executarComando();
  }
}

void mostrarDistancias() {
  if (!modoDebug || millis() - ultimaDistancia < intervaloDistancia) {
    return;
  }

  ultimaDistancia = millis();
  Serial.print("# DISTANCIA ");
  entrada.mostrarDistancia();
  Serial.print(" ");
  saida.mostrarDistancia();
  Serial.println();
}

void setup() {
  Serial.begin(9600);
  entrada.iniciar();
  saida.iniciar();
  Serial.println("PRONTO");
}

void loop() {
  lerComandos();
  entrada.atualizar();
  lerComandos();
  saida.atualizar();
  mostrarDistancias();
}
