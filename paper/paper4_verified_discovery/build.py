from __future__ import annotations
import argparse,re,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def build(subject_sha:str,software_tests:int)->Path:
    if not re.fullmatch(r"[0-9a-f]{40}",subject_sha): raise ValueError("subject_sha must be a 40-character lowercase SHA")
    if software_tests<1: raise ValueError("software_tests must be positive")
    text=(ROOT/"main.tex").read_text(encoding="utf-8")
    anchor=r"\newcommand{\CC}{\texttt{CANNOT\_CHECK}}"
    text=text.replace(anchor,anchor+"\n"+rf"\newcommand{{\ImplementationSHA}}{{\texttt{{{subject_sha}}}}}"+"\n"+rf"\newcommand{{\SoftwareTests}}{{{software_tests}}}",1)
    add=(ROOT/"ASSURANCE_BOUND_ADDENDUM.tex").read_text(encoding="utf-8").strip()
    rel=(ROOT/"RELEASE_APPENDIX.tex").read_text(encoding="utf-8").strip()
    text=text.replace(r"\section{Novelty is bounded and defeasible}",add+"\n\n"+r"\section{Novelty is bounded and defeasible}",1)
    text=text.replace(r"\section{Preregistered evaluation}",rel+"\n\n"+r"\section{Preregistered evaluation}",1)
    text=text.replace("(2025). doi:10.1038/s41586-025-09833-y.","651, 607--613 (2026). doi:10.1038/s41586-025-09833-y.",1)
    temp=ROOT/"release_main.tex"; temp.write_text(text,encoding="utf-8")
    subprocess.run(["latexmk","-pdf","-interaction=nonstopmode","-halt-on-error","-file-line-error",temp.name],cwd=ROOT,check=True)
    out=ROOT/"final.pdf"; shutil.copy2(ROOT/"release_main.pdf",out); return out
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--subject-sha",required=True);p.add_argument("--software-tests",type=int,required=True);a=p.parse_args();print(build(a.subject_sha,a.software_tests))
