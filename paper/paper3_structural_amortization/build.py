from __future__ import annotations
import shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def build()->Path:
    text=(ROOT/"main.tex").read_text(encoding="utf-8").replace(r"\input{sections/99_references}",r"\input{figures/figure_appendix}"+"\n"+r"\input{sections/99_references}",1)
    temp=ROOT/"release_main.tex";temp.write_text(text,encoding="utf-8")
    subprocess.run(["latexmk","-pdf","-interaction=nonstopmode","-halt-on-error","-file-line-error",temp.name],cwd=ROOT,check=True)
    out=ROOT/"final.pdf";shutil.copy2(ROOT/"release_main.pdf",out);return out
if __name__=="__main__": print(build())
