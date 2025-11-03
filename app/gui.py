"""
Interface graphique principale pour l'application OCR.

Composants :
- Radio buttons pour sélectionner le processor (Tesseract / Google Cloud Vision)
- Bouton de sélection de fichiers
- Liste des fichiers sélectionnés
- Zone de logs
- Bouton de transcription

🔄 PIPELINE TRANSCRIPTION :
1. Sélection du processor selon le radio button actif
2. Pour chaque image : processor.run(image_path)
3. Affichage des résultats dans les logs
"""

from __future__ import annotations

import logging
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import List

from .processors import TesseractProcessor, GoogleCloudProcessor, DocumentAIProcessor, ChatGPTProcessor
from .processors.base_processor import BaseProcessor

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")


class App(ttk.Frame):
    """Interface graphique principale pour l'application OCR."""

    def __init__(self, master: tk.Tk | None = None):
        super().__init__(master)
        self.master.title("Transcripteur OCR de tableaux")
        self.pack(fill=tk.BOTH, expand=True)

        # -----------------------------------------------------------------
        # Attributs
        # -----------------------------------------------------------------
        self.selected_files: List[Path] = []
        self.processor_choice = tk.StringVar(value="tesseract")  # Par défaut Tesseract
        self.current_processor: BaseProcessor | None = None

        # -----------------------------------------------------------------
        # Widgets
        # -----------------------------------------------------------------
        self._create_widgets()
        self._update_processor()  # !: Initialise le processor par défaut au démarrage

    # ---------------------------------------------------------------------
    # Interface
    # ---------------------------------------------------------------------
    def _create_widgets(self) -> None:
        # Zone de sélection du processor
        processor_frame = ttk.LabelFrame(self, text="Moteur OCR", padding=10)
        processor_frame.pack(fill=tk.X, padx=10, pady=10)

        tesseract_radio = ttk.Radiobutton(
            processor_frame,
            text="Tesseract (local, gratuit)",
            variable=self.processor_choice,
            value="tesseract",
            command=self._update_processor,
        )
        tesseract_radio.pack(side=tk.LEFT, padx=5)

        google_radio = ttk.Radiobutton(
            processor_frame,
            text="Google Cloud Vision (API, générique)",
            variable=self.processor_choice,
            value="google_cloud",
            command=self._update_processor,
        )
        google_radio.pack(side=tk.LEFT, padx=5)

        document_ai_radio = ttk.Radiobutton(
            processor_frame,
            text="Document AI (API, tableaux)",
            variable=self.processor_choice,
            value="document_ai",
            command=self._update_processor,
        )
        document_ai_radio.pack(side=tk.LEFT, padx=5)

        chatgpt_radio = ttk.Radiobutton(
            processor_frame,
            text="ChatGPT Vision (API, performant)",
            variable=self.processor_choice,
            value="chatgpt",
            command=self._update_processor,
        )
        chatgpt_radio.pack(side=tk.LEFT, padx=5)

        # Zone supérieure : boutons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        self.select_btn = ttk.Button(btn_frame, text="Choisir image(s)", command=self._on_select)
        self.select_btn.pack(side=tk.LEFT, padx=5)

        self.transcribe_btn = ttk.Button(btn_frame, text="Transcrire", command=self._on_transcribe, state=tk.DISABLED)
        self.transcribe_btn.pack(side=tk.LEFT, padx=5)

        # Liste des fichiers sélectionnés
        self.file_list = tk.Listbox(self, height=8)
        self.file_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Zone de logs
        self.log_text = tk.Text(self, height=8, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=False, padx=10, pady=(0, 10))

    # ------------------------------------------------------------------
    # Processor Management
    # ------------------------------------------------------------------
    def _update_processor(self) -> None:
        """Met à jour le processor actif selon le choix de l'utilisateur."""
        try:
            choice = self.processor_choice.get()
            
            if choice == "tesseract":
                self.current_processor = TesseractProcessor(lang="fra", debug=True)
                self._log("✅ Tesseract activé (OCR local)")
                
            elif choice == "google_cloud":
                try:
                    self.current_processor = GoogleCloudProcessor(debug=True)
                    self._log("✅ Google Cloud Vision activé (API)")
                except RuntimeError as e:
                    self._log(f"❌ Erreur Google Cloud: {e}")
                    self._log("↩️  Retour à Tesseract")
                    self.processor_choice.set("tesseract")
                    self.current_processor = TesseractProcessor(lang="fra", debug=True)
                except NotImplementedError as e:
                    self._log(f"⚠️ {e}")
                    self._log("↩️  Retour à Tesseract")
                    self.processor_choice.set("tesseract")
                    self.current_processor = TesseractProcessor(lang="fra", debug=True)
                    
            elif choice == "document_ai":
                try:
                    self.current_processor = DocumentAIProcessor(debug=True)
                    self._log("✅ Document AI activé (API, spécialisé documents)")
                except RuntimeError as e:
                    self._log(f"❌ Erreur Document AI: {e}")
                    self._log("↩️  Retour à Tesseract")
                    self.processor_choice.set("tesseract")
                    self.current_processor = TesseractProcessor(lang="fra", debug=True)
                except ImportError as e:
                    self._log(f"❌ Package manquant: {e}")
                    self._log("↩️  Retour à Tesseract")
                    self.processor_choice.set("tesseract")
                    self.current_processor = TesseractProcessor(lang="fra", debug=True)
                    
            elif choice == "chatgpt":
                try:
                    self.current_processor = ChatGPTProcessor(debug=True)
                    self._log("✅ ChatGPT Vision activé (API, GPT-4o-mini)")
                except ValueError as e:
                    self._log(f"❌ Erreur ChatGPT: {e}")
                    self._log("↩️  Retour à Tesseract")
                    self.processor_choice.set("tesseract")
                    self.current_processor = TesseractProcessor(lang="fra", debug=True)
                except ImportError as e:
                    self._log(f"❌ Package manquant (openai): {e}")
                    self._log("↩️  Retour à Tesseract")
                    self.processor_choice.set("tesseract")
                    self.current_processor = TesseractProcessor(lang="fra", debug=True)
            
        except Exception as e:
            logger.exception("Erreur lors de la mise à jour du processor")
            self._log(f"❌ Erreur: {e}")
            # Fallback sur Tesseract
            self.current_processor = TesseractProcessor(lang="fra", debug=True)

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------
    def _on_select(self) -> None:
        files = filedialog.askopenfilenames(
            title="Choisir des images",
            filetypes=[
                ("Images", "*.png *.jpg *.jpeg *.bmp"),
                ("Tous les fichiers", "*.*"),
            ],
        )
        if files:
            self.selected_files = [Path(f) for f in files]
            self._refresh_file_list()
            self.transcribe_btn.config(state=tk.NORMAL)
        else:
            self.selected_files = []
            self._refresh_file_list()
            self.transcribe_btn.config(state=tk.DISABLED)

    def _on_transcribe(self) -> None:
        if not self.selected_files:
            messagebox.showwarning("Aucun fichier", "Veuillez d'abord sélectionner des images.")
            return

        if not self.current_processor:
            messagebox.showerror("Erreur", "Aucun processor actif. Impossible de transcrire.")
            return

        output_paths: List[Path] = []
        for img_path in self.selected_files:
            try:
                csv_path = self.current_processor.run(img_path)
                output_paths.append(csv_path)
                self._log(f"✅ {img_path.name} → {csv_path.name}")
            except Exception as exc:  # noqa: BLE001
                logger.exception("Erreur lors de l'OCR de %s", img_path)
                self._log(f"❌ {img_path.name}: {exc}")
        messagebox.showinfo("Terminé", f"{len(output_paths)} fichier(s) généré(s).")

    # ------------------------------------------------------------------
    # Utils UI
    # ------------------------------------------------------------------
    def _refresh_file_list(self) -> None:
        self.file_list.delete(0, tk.END)
        for p in self.selected_files:
            self.file_list.insert(tk.END, p.name)

    def _log(self, msg: str) -> None:
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED) 