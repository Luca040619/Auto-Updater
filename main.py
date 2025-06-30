from PyQt6.QtGui import QFontDatabase, QFont
from PyQt6.QtWidgets import QApplication, QDialog, QVBoxLayout
from qfluentwidgets import FluentWindow, setTheme, Theme, FluentIcon
from gui.home_page import HomePage
from gui.network_page import NetworkPage
from gui.first_launch_page import FirstLaunchPage  # importa la pagina di primo avvio
from utils.functions import config_path_exists

import sys

def main():
    app = QApplication(sys.argv)

    # Carica font Inter
    font_id = QFontDatabase.addApplicationFont("assets/fonts/Inter.ttf")
    fonts = QFontDatabase.applicationFontFamilies(font_id)
    if fonts:
        f = QFont(fonts[0])
        f.setPointSize(10)
        app.setFont(f)

    # Attiva tema sistema
    setTheme(Theme.AUTO)

    if not config_path_exists():
        # ===== Mostra schermata di primo avvio in una finestra modale =====
        first_launch = FirstLaunchPage()
        dialog = QDialog()
        dialog.setWindowTitle("Primo avvio")
        dialog.setMinimumSize(800, 600)
        dialog.setMaximumWidth(800)
        dialog.setMaximumHeight(800)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(first_launch)

        # Quando cliccano continua, chiudi dialog e mostra l'app
        def on_continue():
            dialog.accept()

        first_launch.continue_btn.clicked.connect(on_continue)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            sys.exit(0)  # esce se l'utente chiude senza accettare

    # ===== Avvia l'interfaccia principale =====
    window = FluentWindow()
    window.navigationInterface.setReturnButtonVisible(False)
    window.navigationInterface.setExpandWidth(200)
    window.setWindowTitle("Auto Updater")
    window.setMinimumSize(800, 670)
    window.setMicaEffectEnabled(True)

    window.addSubInterface(HomePage(), icon=FluentIcon.HOME, text="Home")
    window.addSubInterface(NetworkPage(), icon=FluentIcon.WIFI, text="Monitoraggio")
    #window.addSubInterface(SettingsPage(), icon="Settings", text="Impostazioni")

    window.resize(window.minimumSize())
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
