from functools import partial
from pathlib import Path

from kivy.clock import Clock
from kivy.properties import ListProperty, StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.screenmanager import ScreenManager

from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDButton, MDButtonText, MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen
from kivymd.uix.textfield import MDTextField, MDTextFieldHintText

from comunicacao import ClienteESP32, carregar_configuracao, pin_valido


PASTA = Path(__file__).resolve().parent


class BotaoVoltar(ButtonBehavior, MDLabel):
    pass


class ItemEstacionamento(MDBoxLayout):
    pass


class NomeEstacionamento(ButtonBehavior, MDLabel):
    pass


class BadgeVagas(MDBoxLayout):
    pass


class TelaPrincipal(MDScreen):
    pass


class TelaPin(MDScreen):
    mensagem = StringProperty("")

    def confirmar_pin(self, pin):
        app = MDApp.get_running_app()
        if not pin_valido(pin):
            self.mensagem = "Digite um PIN com 4 dígitos."
            return
        if app.erro_configuracao:
            self.mensagem = app.erro_configuracao
            return
        if pin not in app.conexoes:
            self.mensagem = "PIN não cadastrado em config.json."
            return

        if not any(item["pin"] == pin for item in app.estacionamentos):
            # Nenhuma contagem é inventada enquanto a primeira leitura não chega.
            app.estacionamentos = [*app.estacionamentos, {
                "pin": pin,
                "nome": f"Estacionamento {pin}",
                "vagas_ocupadas": None,
                "vagas_totais": None,
                "vagas_livres": None,
                "vagas": [],
                "conectado": False,
                "status": f"Conectando ao ESP32 pela {app.conexoes[pin]['porta']}…",
            }]
        self.mensagem = ""
        self.manager.current = "principal"
        self.ids.campo_pin.text = ""
        app.cliente.conectar(pin, app.conexoes[pin])


class Interface(MDApp):
    cor_fundo = ListProperty([1, 1, 1, 1])
    cor_texto = ListProperty([0.55, 0.55, 0.55, 1])
    cor_borda_card = ListProperty([0.2, 0.75, 0.45, 0.35])
    estacionamentos = ListProperty([])
    erro_configuracao = StringProperty("")

    def build(self):
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Green"
        self.conexoes = {}
        try:
            self.conexoes = carregar_configuracao(PASTA / "config.json")
        except (OSError, ValueError) as exc:
            self.erro_configuracao = f"Corrija config.json e reinicie o aplicativo: {exc}"
        self.cliente = ClienteESP32(self.receber_dados, self.registrar_falha)
        self._evento_atualizacao = None
        sm = ScreenManager()
        sm.add_widget(TelaPrincipal(name="principal"))
        sm.add_widget(TelaPin(name="pin"))
        return sm

    def on_start(self):
        self._evento_atualizacao = Clock.schedule_interval(self.cliente.processar_eventos, 0.1)

    def on_stop(self):
        if self._evento_atualizacao is not None:
            self._evento_atualizacao.cancel()
        self.cliente.encerrar()

    def conectar(self):
        self.root.get_screen("pin").mensagem = self.erro_configuracao
        self.root.current = "pin"

    def receber_dados(self, pin, dados):
        self._alterar_estacionamento(pin, {
            **dados, "conectado": True,
            "status": f"Conectado por USB — {self.conexoes[pin]['porta']}",
        })

    def registrar_falha(self, pin, mensagem):
        self._alterar_estacionamento(pin, {"conectado": False, "status": mensagem})

    def _alterar_estacionamento(self, pin, alteracoes):
        novos = [
            {**item, **alteracoes} if item["pin"] == pin else item
            for item in self.estacionamentos
        ]
        if novos != self.estacionamentos:
            # Trocar a lista dispara o ListProperty; mutar só o dicionário não basta.
            self.estacionamentos = novos

    def on_estacionamentos(self, *args):
        if self.root:
            self.atualizar_lista()

    def atualizar_lista(self):
        container = self.root.get_screen("principal").ids.lista_estacionamentos
        container.clear_widgets()
        for item in self.estacionamentos:
            linha = ItemEstacionamento()
            nome = NomeEstacionamento(
                text=f"{item['nome']}\n{item['status']}",
                halign="left",
                valign="center",
                theme_text_color="Custom",
                text_color=self.cor_texto,
                font_style="Body",
                role="small",
            )
            nome.bind(size=lambda inst, val: setattr(inst, "text_size", val))
            nome.bind(on_release=partial(self.abrir_estacionamento, item))
            linha.add_widget(nome)
            badge = BadgeVagas()
            total = item["vagas_totais"]
            texto = (
                f"{item['vagas_ocupadas']}/{total}"
                if item["conectado"] else f"--/{total if total is not None else '--'}"
            )
            badge.add_widget(MDLabel(
                text=texto,
                halign="center",
                valign="center",
                theme_text_color="Custom",
                text_color=self.cor_texto,
                bold=True,
            ))
            linha.add_widget(badge)
            container.add_widget(linha)

    def abrir_estacionamento(self, item, *args):
        print("Estacionamento:", item["nome"], "PIN:", item["pin"])
        print("Estado das vagas:", item["vagas"], "Conectado:", item["conectado"])


if __name__ == "__main__":
    Interface(kv_file=str(PASTA / "Interface.kv")).run()
