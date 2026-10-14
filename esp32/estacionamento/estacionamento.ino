#include <Arduino.h>

// USB/serial: uma linha JSON por leitura, a 115200 baud.
const char* PIN_ESTACIONAMENTO = "1234";
const char* NOME_ESTACIONAMENTO = "Shopping Polo";

// Dois sensores Flying-Fish: DO em D26/GPIO26 e D27/GPIO27.
// Alimentação informada: VCC em 3V3 e GND em GND comum.
// Os números são GPIOs, não posições físicas do conector.
const uint8_t PINOS_SENSORES[] = {26, 27};
const int NIVEL_OCUPADO = LOW;
const size_t TOTAL_VAGAS = sizeof(PINOS_SENSORES) / sizeof(PINOS_SENSORES[0]);
const unsigned long ESTABILIDADE_MS = 150;
const unsigned long INTERVALO_ENVIO_MS = 1000;

bool candidatos[TOTAL_VAGAS];
bool ocupadas[TOTAL_VAGAS];
bool prontas[TOTAL_VAGAS] = {};
unsigned long alteradaEm[TOTAL_VAGAS];
unsigned long ultimoEnvio = 0;
bool enviou = false;

// Escapa nomes com aspas, barras e caracteres de controle para JSON válido.
String textoJSON(const char* texto) {
  String resultado = "\"";
  for (const unsigned char* p = reinterpret_cast<const unsigned char*>(texto); *p; ++p) {
    if (*p == '"' || *p == '\\') {
      resultado += '\\';
      resultado += static_cast<char>(*p);
    } else if (*p < 0x20) {
      char escape[7];
      snprintf(escape, sizeof(escape), "\\u%04x", *p);
      resultado += escape;
    } else {
      resultado += static_cast<char>(*p);
    }
  }
  resultado += '"';
  return resultado;
}

bool lerSensores() {
  bool mudou = false;
  const unsigned long agora = millis();
  for (size_t i = 0; i < TOTAL_VAGAS; ++i) {
    const bool leitura = digitalRead(PINOS_SENSORES[i]) == NIVEL_OCUPADO;
    if (leitura != candidatos[i]) {
      candidatos[i] = leitura;
      alteradaEm[i] = agora;
    }
    if (agora - alteradaEm[i] >= ESTABILIDADE_MS) {
      if (!prontas[i] || ocupadas[i] != candidatos[i]) mudou = true;
      ocupadas[i] = candidatos[i];
      prontas[i] = true;
    }
  }
  return mudou;
}

void enviarVagas() {
  for (size_t i = 0; i < TOTAL_VAGAS; ++i) {
    if (!prontas[i]) {
      return;
    }
  }
  size_t quantidadeOcupadas = 0;
  for (size_t i = 0; i < TOTAL_VAGAS; ++i) {
    if (ocupadas[i]) ++quantidadeOcupadas;
  }
  String json;
  json.reserve(200 + TOTAL_VAGAS * 32);
  json = "{\"pin\":" + textoJSON(PIN_ESTACIONAMENTO);
  json += ",\"nome\":" + textoJSON(NOME_ESTACIONAMENTO);
  json += ",\"vagas_totais\":" + String(static_cast<unsigned int>(TOTAL_VAGAS));
  json += ",\"vagas_ocupadas\":" + String(static_cast<unsigned int>(quantidadeOcupadas));
  json += ",\"vagas_livres\":" + String(static_cast<unsigned int>(TOTAL_VAGAS - quantidadeOcupadas));
  json += ",\"vagas\":[";
  for (size_t i = 0; i < TOTAL_VAGAS; ++i) {
    if (i > 0) json += ',';
    json += "{\"id\":" + String(static_cast<unsigned int>(i + 1));
    json += ",\"ocupada\":";
    json += ocupadas[i] ? "true" : "false";
    json += '}';
  }
  json += "]}";
  Serial.println(json);
  ultimoEnvio = millis();
  enviou = true;
}

void setup() {
  Serial.begin(115200);
  for (size_t i = 0; i < TOTAL_VAGAS; ++i) {
    pinMode(PINOS_SENSORES[i], INPUT_PULLUP);
    candidatos[i] = digitalRead(PINOS_SENSORES[i]) == NIVEL_OCUPADO;
    alteradaEm[i] = millis();
  }
}

void loop() {
  const bool mudou = lerSensores();
  if (mudou || !enviou || millis() - ultimoEnvio >= INTERVALO_ENVIO_MS) {
    enviarVagas();
  }
  delay(5);
}
