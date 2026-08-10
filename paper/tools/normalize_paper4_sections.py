from __future__ import annotations
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/"paper4_verified_discovery"
SRC=ROOT/"main.tex"

def slug(title:str)->str:
    s=re.sub(r"[^a-z0-9]+","_",title.lower()).strip("_")
    return s[:64] or "section"

def main()->None:
    text=SRC.read_text(encoding="utf-8")
    if "\\input{sections/01_" in text:
        return
    abstract_end=text.index("\\end{abstract}")+len("\\end{abstract}")
    pre=text[:abstract_end]
    # Add exact-release identity without changing scientific source semantics.
    anchor=r"\newcommand{\CC}{\texttt{CANNOT\_CHECK}}"
    if r"\IfFileExists{build_identity.tex}" not in pre:
        identity=("\n\\IfFileExists{build_identity.tex}{\\input{build_identity.tex}}"
                  "{\\newcommand{\\SoftwareTests}{UNBOUND}\\newcommand{\\ImplementationSHA}{\\texttt{UNBOUND}}}\n")
        pre=pre.replace(anchor,anchor+identity,1)
    tail=text[abstract_end:]
    bib_i=tail.index("\\begin{thebibliography}")
    body=tail[:bib_i]
    bib=tail[bib_i:tail.rindex("\\end{document}")]
    bib=bib.replace("(2025). doi:10.1038/s41586-025-09833-y.","651, 607--613 (2026). doi:10.1038/s41586-025-09833-y.")
    matches=list(re.finditer(r"(?m)^\\section\{([^}]*)\}",body))
    secdir=ROOT/"sections"; secdir.mkdir(exist_ok=True)
    inputs=[]
    for i,m in enumerate(matches,1):
        end=matches[i].start() if i<len(matches) else len(body)
        title=m.group(1)
        fn=f"{i:02d}_{slug(title)}.tex"
        (secdir/fn).write_text(body[m.start():end].strip()+"\n",encoding="utf-8")
        inputs.append(f"\\input{{sections/{fn[:-4]}}}")
        if title=="Proof assurance and verifier trust":
            add=(ROOT/"ASSURANCE_BOUND_ADDENDUM.tex").read_text(encoding="utf-8").strip()+"\n"
            afn="06b_assurance_bound.tex"; (secdir/afn).write_text(add,encoding="utf-8"); inputs.append(f"\\input{{sections/{afn[:-4]}}}")
        if title=="RAKL integration":
            rel=(ROOT/"RELEASE_APPENDIX.tex").read_text(encoding="utf-8").strip()+"\n"
            rfn="11b_reference_implementation.tex"; (secdir/rfn).write_text(rel,encoding="utf-8"); inputs.append(f"\\input{{sections/{rfn[:-4]}}}")
            inputs.append("\\input{figures/figure_appendix}")
    (secdir/"99_references.tex").write_text(bib.strip()+"\n",encoding="utf-8")
    new=pre+"\n\n"+"\n".join(inputs)+"\n\\input{sections/99_references}\n\\end{document}\n"
    SRC.write_text(new,encoding="utf-8")
    (ROOT/"ASSURANCE_BOUND_ADDENDUM.tex").unlink(missing_ok=True)
    (ROOT/"RELEASE_APPENDIX.tex").unlink(missing_ok=True)

if __name__=="__main__": main()
