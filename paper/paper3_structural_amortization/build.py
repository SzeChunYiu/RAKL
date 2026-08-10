from __future__ import annotations
import argparse, shutil, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def build()->Path:
    subprocess.run(["latexmk","-pdf","-interaction=nonstopmode","-halt-on-error","-file-line-error","main.tex"],cwd=ROOT,check=True)
    out=ROOT/"final.pdf"; shutil.copy2(ROOT/"main.pdf",out); return out
if __name__=="__main__": print(build())
