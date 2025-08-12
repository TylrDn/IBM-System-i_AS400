from __future__ import annotations

import argparse
import logging
import subprocess
import sys
import time
from pathlib import Path
from tkinter import HORIZONTAL, LEFT, RIGHT, Button, Label, StringVar, Tk
from tkinter.ttk import Progressbar

from PIL import Image, ImageTk


parser = argparse.ArgumentParser(description="Payroll GUI wrapper")
parser.add_argument("--dry-run", action="store_true", help="Validate without uploading")
parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
args = parser.parse_args()

logging.basicConfig(
    level=logging.DEBUG if args.verbose else logging.INFO, format="%(message)s"
)
log = logging.getLogger(__name__)


def button_confirm() -> None:
    try:
        task = 10
        for x in range(task):
            time.sleep(1)
            progress_bar["value"] += 10
            percent.set(
                f"{int(((x + 1) / task) * 100)}% Iniciando Interfaz. Por Favor, Espere Hasta Que El Proceso Termine."
            )
            window.update_idletasks()
        script_path = Path(__file__).with_name("payroll_b.py").resolve()
        if not script_path.is_file():
            raise FileNotFoundError(f"Missing payroll_b script: {script_path}")
        cmd = [sys.executable, str(script_path)]
        if args.dry_run:
            cmd.append("--dry-run")
        if args.verbose:
            cmd.append("--verbose")
        completed_process = subprocess.run(
            cmd, check=True, capture_output=True, text=True, shell=False
        )
        log.debug(completed_process.stdout)
    except subprocess.CalledProcessError as exc:
        log.error("An error has occurred in payroll_b: %s", exc.stderr)
        raise
    else:
        log.info("Successful execution of payroll_b")
    window.quit()


def button_cancel() -> None:
    window.quit()


window = Tk()
window.geometry("500x500")
window.title("Interfaz Ajustes Salariales de Nomina SPI")

lbl = Label(window, text="¿Desea Confirmar la Ejecucion del Proceso?")
lbl.config(font=("Arial", 10))
lbl.pack()

percent = StringVar()
progress_bar = Progressbar(window, orient=HORIZONTAL, length=300, mode="determinate")
progress_bar.pack(pady=20)
Label(window, textvariable=percent).pack()

image = Image.open("icons8-payroll-64.png")
image_ = ImageTk.PhotoImage(image)
Label(window, image=image_).pack()

Button(window, text="      OK           ", command=button_confirm).pack(
    side=LEFT, padx=15, pady=20
)
Button(window, text="    Cancel     ", command=button_cancel).pack(
    side=RIGHT, padx=15, pady=20
)

window.resizable(False, False)
window.mainloop()
