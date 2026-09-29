from functools import partial

from kivy.metrics import dp
from kivy.properties import ListProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.screenmanager import ScreenManager

from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen


# simula um "banco de dados" de estacionamentos cadastrados: pin -> {nome, vagas_totais}
# TODO: no futuro isso vem do ESP32 / de um banco de verdade, nao fixo aqui
BANCO_DE_DADOS_TESTE = {
    "1234": {"nome": "Shopping Polo", "vagas_totais": 32},
    "5678": {"nome": "Shopping 2", "vagas_totais": 50},
    "9012": {"nome": "Shopping 3", "vagas_totais": 20},
}


class BotaoVoltar(ButtonBehavior, MDLabel):
    """Label clicavel usada como seta de 'voltar' em cada tela."""
    pass


class ItemEstacionamento(MDBoxLayout):
    """Linha de um estacionamento conectado: nome clicavel a esquerda,
    linha fina embaixo e um badge 'ocupadas/total' de vagas a direita.
    O visual (cor de fundo, linha) fica no kv."""
    pass


class NomeEstacionamento(ButtonBehavior, MDLabel):
    """Nome do estacionamento — clicavel, abre o estacionamento ao tocar."""
    pass


class BadgeVagas(MDBoxLayout):
    """Badge roxo mostrando 'vagas_ocupadas/vagas_totais'."""
    pass


class TelaPrincipal(MDScreen):
    pass


class TelaPin(MDScreen):
    def confirmar_pin(self, pin):
        app = MDApp.get_running_app()

        if len(pin) != 4:
            print("PIN invalido, precisa ter 4 digitos")
            return

        dados = BANCO_DE_DADOS_TESTE.get(pin)
        if dados is None:
            print("PIN nao encontrado")
            return

        # evita duplicar se o usuario conectar o mesmo pin de novo
        ja_conectado = any(item["pin"] == pin for item in app.estacionamentos)
        if not ja_conectado:
            app.estacionamentos.append({
                "pin": pin,
                "nome": dados["nome"],
                "vagas_ocupadas": 0,  # TODO: vira do ESP32 futuramente
                "vagas_totais": dados["vagas_totais"],
            })
            app.atualizar_lista()

        self.manager.current = "principal"


class Interface(MDApp):
    cor_fundo = ListProperty([1, 1, 1, 1])                 # fundo branco
    cor_texto = ListProperty([0.55, 0.55, 0.55, 1])         # cinza p/ textos secundarios
    cor_borda_card = ListProperty([0.2, 0.75, 0.45, 0.35])  # borda verde

    # fonte da verdade: cada item = {"pin", "nome", "vagas_ocupadas", "vagas_totais"}
    estacionamentos = ListProperty([])

    def build(self):
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Green"

        sm = ScreenManager()
        sm.add_widget(TelaPrincipal(name="principal"))
        sm.add_widget(TelaPin(name="pin"))
        return sm

    def conectar(self):
        self.root.current = "pin"

    def atualizar_lista(self):
        """Redesenha as linhas de estacionamento a partir de self.estacionamentos:
        nome clicavel a esquerda e badge 'ocupadas/total' de vagas a direita."""
        container = self.root.get_screen("principal").ids.lista_estacionamentos
        container.clear_widgets()

        for item in self.estacionamentos:
            linha = ItemEstacionamento()

            nome = NomeEstacionamento(
                text=item["nome"],
                halign="left",
                valign="center",
                theme_text_color="Custom",
                text_color=self.cor_texto,
            )
            # forca o texto a alinhar a esquerda dentro da largura real do label
            nome.bind(size=lambda inst, val: setattr(inst, "text_size", val))
            # partial "congela" o valor de item no momento da criacao,
            # evitando o bug classico de closure em loops
            nome.bind(on_release=partial(self.abrir_estacionamento, item))
            linha.add_widget(nome)

            badge = BadgeVagas()
            badge.add_widget(MDLabel(
                text=f"{item['vagas_ocupadas']}/{item['vagas_totais']}",
                halign="center",
                valign="center",
                theme_text_color="Custom",
                text_color=self.cor_texto,
                bold=True,
            ))
            linha.add_widget(badge)

            container.add_widget(linha)

    def abrir_estacionamento(self, item, *args):
        print("Abrindo:", item["nome"], "PIN:", item["pin"])
        # TODO: se quiser, navegue para uma tela de detalhes aqui


Interface().run()