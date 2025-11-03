"""
Point d'entrée principal de l'application ReadPicture.

Lance l'interface graphique Tkinter.
"""

import tkinter as tk

from app.gui import App


def main() -> None:
    root = tk.Tk()
    root.geometry("700x600")
    app = App(master=root)
    app.mainloop()


if __name__ == "__main__":
    main() 