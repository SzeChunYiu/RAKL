from __future__ import annotations
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/"paper4_verified_discovery"; SRC=ROOT/"main.tex"
def slug(title:str)->str: return (re.sub(r"[^a-z0-9]+","_",title.lower()).strip("_")[:64] or "section")
def main()->None:
    text=SRC.read_text(encoding="utf-8")
    if "\\input{sections/01_" in text: return
    ae=text.index("\\end{abstract}")+len("\\end{abstract}"); pre=text[:ae]
    anchor=r"\newcommand{\CC}{\texttt{CANNOT\_CHECK}}"
    pre=pre.replace(anchor,anchor+"\n\\IfFileExists{build_identity.tex}{\\input{build_identity.tex}}{\\newcommand{\\SoftwareTests}{UNBOUND}\\newcommand{\\ImplementationSHA}{\\texttt{UNBOUND}}}\n",1)
    tail=text[ae:]; bi=tail.index("\\begin{thebibliography}"); body=tail[:bi]; bib=tail[bi:tail.rindex("\\end{document}")]
    bib=bib.replace("(2025). doi:10.1038/s41586-025-09833-y.","651, 607--613 (2026). doi:10.1038/s41586-025-09833-y.")
    ms=list(re.finditer(r"(?m)^\\section\{([^}]*)\}",body)); sd=ROOT/"sections"; sd.mkdir(exist_ok=True); inputs=[]
    for i,m in enumerate(ms,1):
        end=ms[i].start() if i<len(ms) else len(body); title=m.group(1); fn=f"{i:02d}_{slug(title)}.tex"
        (sd/fn).write_text(body[m.start():end].strip()+"\n",encoding="utf-8"); inputs.append(f"\\input{{sections/{fn[:-4]}}}")
        if title=="Proof assurance and verifier trust":
            afn="06b_assurance_bound.tex"; (sd/afn).write_text((ROOT/"ASSURANCE_BOUND_ADDENDUM.tex").read_text(encoding="utf-8").strip()+"\n",encoding="utf-8"); inputs.append(f"\\input{{sections/{afn[:-4]}}}")
        if title=="RAKL integration":
            rfn="11b_reference_implementation.tex"; (sd/rfn).write_text((ROOT/"RELEASE_APPENDIX.tex").read_text(encoding="utf-8").strip()+"\n",encoding="utf-8"); inputs += [f"\\input{{sections/{rfn[:-4]}}}","\\input{figures/figure_appendix}"]
    (sd/"99_references.tex").write_text(bib.strip()+"\n",encoding="utf-8")
    SRC.write_text(pre+"\n\n"+"\n".join(inputs)+"\n\\input{sections/99_references}\n\\end{document}\n",encoding="utf-8")
    (ROOT/"ASSURANCE_BOUND_ADDENDUM.tex").unlink(missing_ok=True); (ROOT/"RELEASE_APPENDIX.tex").unlink(missing_ok=True)
    (ROOT/"build.py").write_text('''from __future__ import annotations\nimport argparse,re,shutil,subprocess\nfrom pathlib import Path\nROOT=Path(__file__).resolve().parent\ndef build(subject_sha:str,software_tests:int)->Path:\n    if not re.fullmatch(r"[0-9a-f]{40}",subject_sha): raise ValueError("invalid SHA")\n    if software_tests<1: raise ValueError("software_tests must be positive")\n    (ROOT/"build_identity.tex").write_text(rf"\\\\newcommand{{\\\\SoftwareTests}}{{{software_tests}}}\\n\\\\newcommand{{\\\\ImplementationSHA}}{{\\\\texttt{{{subject_sha}}}}}\\n",encoding="utf-8")\n    subprocess.run(["latexmk","-pdf","-interaction=nonstopmode","-halt-on-error","-file-line-error","main.tex"],cwd=ROOT,check=True)\n    out=ROOT/"final.pdf";shutil.copy2(ROOT/"main.pdf",out);return out\nif __name__=="__main__":\n    p=argparse.ArgumentParser();p.add_argument("--subject-sha",required=True);p.add_argument("--software-tests",type=int,required=True);a=p.parse_args();print(build(a.subject_sha,a.software_tests))\n''',encoding="utf-8")
if __name__=="__main__": main()
