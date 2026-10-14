"""Contrato JSON e recepção USB/serial do ESP32, sem bloquear o Kivy."""

import json
import re
from pathlib import Path
from threading import Event, Lock, Thread
from time import monotonic


def pin_valido(pin):
    return isinstance(pin, str) and re.fullmatch(r"[0-9]{4}", pin) is not None


def carregar_configuracao(caminho):
    """Relaciona cada PIN a uma porta serial e sua velocidade."""
    dados = json.loads(Path(caminho).read_text(encoding="utf-8-sig"))
    if not isinstance(dados, dict) or not dados:
        raise ValueError("Configure pelo menos um PIN em config.json.")
    resultado = {}
    portas = set()
    for pin, configuracao in dados.items():
        if not pin_valido(pin) or not isinstance(configuracao, dict):
            raise ValueError("Cada PIN deve ter 4 dígitos e uma configuração serial.")
        porta = configuracao.get("porta")
        velocidade = configuracao.get("baudrate", 115200)
        if not isinstance(porta, str) or not re.fullmatch(r"COM[1-9][0-9]*", porta, re.I):
            raise ValueError(f"Informe uma porta como COM3 para o PIN {pin}.")
        porta = porta.upper()
        if porta in portas:
            raise ValueError("Uma mesma porta serial não pode ser usada por dois PINs.")
        if type(velocidade) is not int or not 300 <= velocidade <= 4000000:
            raise ValueError(f"Velocidade serial inválida para o PIN {pin}.")
        portas.add(porta)
        resultado[pin] = {"porta": porta, "baudrate": velocidade}
    return resultado


def validar_dados(dados, pin_esperado):
    """Valida uma leitura inteira antes de permitir qualquer mudança na tela."""
    if not isinstance(dados, dict):
        raise ValueError("A resposta deve ser um objeto JSON.")
    if dados.get("pin") != pin_esperado:
        raise ValueError("O PIN recebido não corresponde ao estacionamento.")
    nome = dados.get("nome")
    if not isinstance(nome, str) or not nome.strip() or len(nome) > 80:
        raise ValueError("Nome do estacionamento inválido.")
    vagas = dados.get("vagas")
    if not isinstance(vagas, list) or not 1 <= len(vagas) <= 128:
        raise ValueError("A leitura precisa conter de 1 a 128 vagas.")
    ids = set()
    estados = []
    for vaga in vagas:
        if not isinstance(vaga, dict):
            raise ValueError("Vaga inválida.")
        identificador = vaga.get("id")
        if type(identificador) is not int or identificador <= 0 or identificador in ids:
            raise ValueError("Os IDs das vagas devem ser inteiros positivos e únicos.")
        if type(vaga.get("ocupada")) is not bool:
            raise ValueError("O estado de cada vaga deve ser true ou false.")
        ids.add(identificador)
        estados.append({"id": identificador, "ocupada": vaga["ocupada"]})
    total = len(estados)
    ocupadas = sum(vaga["ocupada"] for vaga in estados)
    contagens = {
        "vagas_totais": total,
        "vagas_ocupadas": ocupadas,
        "vagas_livres": total - ocupadas,
    }
    for campo, valor in contagens.items():
        if type(dados.get(campo)) is not int or dados[campo] != valor:
            raise ValueError(f"{campo} não corresponde aos estados das vagas.")
    return {
        "pin": pin_esperado,
        "nome": nome.strip(),
        "vagas": sorted(estados, key=lambda vaga: vaga["id"]),
        **contagens,
    }


class SeparadorLinhas:
    """Preserva fragmentos e limita memória mesmo com uma linha sem terminador."""

    def __init__(self, limite=16384):
        self.limite = limite
        self._buffer = bytearray()
        self._descartando = False

    def alimentar(self, dados):
        linhas = []
        for trecho in dados.splitlines(keepends=True):
            terminou = trecho.endswith(b"\n")
            if not self._descartando:
                self._buffer.extend(trecho)
                if len(self._buffer) > self.limite:
                    self._buffer.clear()
                    self._descartando = True
                elif terminou:
                    linhas.append(bytes(self._buffer).strip())
                    self._buffer.clear()
            if terminou:
                self._descartando = False
        return linhas


def abrir_porta_serial(porta, baudrate):
    import serial

    # Configura as linhas de controle antes de abrir para não manter a placa em reset.
    conexao = serial.Serial(port=None, baudrate=baudrate, timeout=0.2)
    conexao.port = porta
    conexao.dtr = False
    conexao.rts = False
    conexao.open()
    return conexao


class ClienteESP32:
    """Um leitor por PIN; somente processar_eventos chama os callbacks da interface."""

    def __init__(self, ao_receber, ao_falhar, abrir_porta=abrir_porta_serial,
                 tempo_sem_dados=5, intervalo_reconexao=2):
        self._abrir_porta = abrir_porta
        self._ao_receber = ao_receber
        self._ao_falhar = ao_falhar
        self.tempo_sem_dados = tempo_sem_dados
        self.intervalo_reconexao = intervalo_reconexao
        self._parar = Event()
        self._lock = Lock()
        self._eventos = {}
        self._leitores = {}

    def conectar(self, pin, configuracao):
        if self._parar.is_set() or pin in self._leitores:
            return
        leitor = Thread(target=self._ler, args=(pin, dict(configuracao)), daemon=True)
        self._leitores[pin] = leitor
        leitor.start()

    def _publicar(self, pin, sucesso, valor):
        if not self._parar.is_set():
            with self._lock:
                # Só o evento mais recente de cada PIN é necessário para a tela.
                self._eventos[pin] = (sucesso, valor)

    def _ler(self, pin, configuracao):
        porta = configuracao["porta"]
        while not self._parar.is_set():
            conexao = None
            try:
                conexao = self._abrir_porta(porta, configuracao["baudrate"])
                separador = SeparadorLinhas()
                ultima_leitura = monotonic()
                avisou_silencio = False
                while not self._parar.is_set():
                    trecho = conexao.read(min(conexao.in_waiting or 1, 1024))
                    for linha in separador.alimentar(trecho):
                        # O ESP32 pode emitir mensagens de boot antes do primeiro JSON.
                        if not linha.startswith(b"{"):
                            continue
                        try:
                            dados = validar_dados(json.loads(linha), pin)
                        except (ValueError, UnicodeError) as exc:
                            self._publicar(pin, False, f"Dados inválidos na {porta}: {exc}")
                        else:
                            ultima_leitura = monotonic()
                            avisou_silencio = False
                            self._publicar(pin, True, dados)
                    if not avisou_silencio and monotonic() - ultima_leitura > self.tempo_sem_dados:
                        self._publicar(pin, False,
                            f"Sem dados na {porta}. Grave o firmware USB a 115200 baud.")
                        avisou_silencio = True
            except ImportError:
                self._publicar(pin, False, "Instale pyserial: python -m pip install pyserial")
            except (OSError, ValueError):
                self._publicar(pin, False,
                    f"Falha na {porta}. Confira o USB e feche o Monitor Serial/Plotter.")
            finally:
                if conexao is not None:
                    try:
                        conexao.close()
                    except OSError:
                        pass
            self._parar.wait(self.intervalo_reconexao)

    def processar_eventos(self, dt=0):
        with self._lock:
            eventos = self._eventos
            self._eventos = {}
        if self._parar.is_set():
            return
        for pin, (sucesso, valor) in eventos.items():
            callback = self._ao_receber if sucesso else self._ao_falhar
            callback(pin, valor)

    def encerrar(self):
        self._parar.set()
        for leitor in self._leitores.values():
            leitor.join(timeout=1)
        with self._lock:
            self._eventos.clear()
