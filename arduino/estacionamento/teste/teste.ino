
#include <Servo.h>

// SERVOS
Servo servoEntrada;
Servo servoSaida;

// SENSOR ENTRADA
const int trigEntrada = 4;
const int echoEntrada = 10;
const int pinoServoEntrada = 5;

// SENSOR SAIDA
const int trigSaida = 9;
const int echoSaida = 11;
const int pinoServoSaida = 8;

// CONFIGURACOES
const int distanciaMinima = 6;
const int distanciaMaxima = 20;

const int fechado = 0;
const int aberto = 90;

bool entradaAberta = false;
bool saidaAberta = false;

unsigned long entradaLivreDesde = 0;
unsigned long saidaLivreDesde = 0;

const unsigned long tempoParaFechar = 2000;

// MEDE DISTANCIA
long medirDistancia(int trig, int echo) {
  digitalWrite(trig, LOW);
  delayMicroseconds(2);

  digitalWrite(trig, HIGH);
  delayMicroseconds(10);

  digitalWrite(trig, LOW);

  unsigned long duracao = pulseIn(echo, HIGH, 40000UL);

  if (duracao == 0) {
    return -1;
  }

  return duracao / 58;
}

void setup() {
  Serial.begin(9600);

  pinMode(trigEntrada, OUTPUT);
  pinMode(echoEntrada, INPUT);

  pinMode(trigSaida, OUTPUT);
  pinMode(echoSaida, INPUT);

  servoEntrada.attach(pinoServoEntrada);
  servoSaida.attach(pinoServoSaida);

  servoEntrada.write(fechado);
  servoSaida.write(fechado);

  Serial.println("TESTE SENSORES + SERVOS INICIADO");
}

void loop() {
  long distanciaEntrada = medirDistancia(
    trigEntrada, echoEntrada
  );

  delay(60);

  long distanciaSaida = medirDistancia(
    trigSaida, echoSaida
  );

  bool carroEntrada =
    distanciaEntrada >= distanciaMinima &&
    distanciaEntrada <= distanciaMaxima;

  bool carroSaida =
    distanciaSaida >= distanciaMinima &&
    distanciaSaida <= distanciaMaxima;

  // ENTRADA
  if (carroEntrada) {
    entradaLivreDesde = 0;

    if (!entradaAberta) {
      servoEntrada.write(aberto);
      entradaAberta = true;

      Serial.println("ENTRADA: CANCELA ABERTA");
    }
  } else if (distanciaEntrada >= 0 && entradaAberta) {
    if (entradaLivreDesde == 0) {
      entradaLivreDesde = millis();
    }

    if (millis() - entradaLivreDesde >= tempoParaFechar) {
      servoEntrada.write(fechado);
      entradaAberta = false;
      entradaLivreDesde = 0;

      Serial.println("ENTRADA: CANCELA FECHADA");
    }
  }

  // SAIDA
  if (carroSaida) {
    saidaLivreDesde = 0;

    if (!saidaAberta) {
      servoSaida.write(aberto);
      saidaAberta = true;

      Serial.println("SAIDA: CANCELA ABERTA");
    }
  } else if (distanciaSaida >= 0 && saidaAberta) {
    if (saidaLivreDesde == 0) {
      saidaLivreDesde = millis();
    }

    if (millis() - saidaLivreDesde >= tempoParaFechar) {
      servoSaida.write(fechado);
      saidaAberta = false;
      saidaLivreDesde = 0;

      Serial.println("SAIDA: CANCELA FECHADA");
    }
  }

  // MONITORAMENTO
  Serial.print("Entrada: ");
  Serial.print(distanciaEntrada);
  Serial.print(" cm | Saida: ");
  Serial.print(distanciaSaida);
  Serial.println(" cm");

  delay(200);
}
