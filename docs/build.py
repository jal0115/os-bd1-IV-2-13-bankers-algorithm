"""Compile the supplied Markdown manual using Pandoc and XeLaTeX."""
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parent
destination = Path(sys.argv[1]).resolve() if len(sys.argv)>1 else root/'IV-2-13_Manual.pdf'
tex = subprocess.check_output(['pandoc','IV-2-13_Manual.md','-t','latex','--wrap=none','--no-highlight'], cwd=root, text=True)
for heading in [r'\subsection{1.5 ',r'\subsection{1.7 ',r'\section{2. ',r'\subsection{2.5 ']:
    tex=tex.replace(heading,'\\clearpage\n'+heading)
key=r'\clearpage'+'\n'+r'\subsection{1.5 '
tex=tex.replace(key,r'''\begin{figure}[H]\centering
\includegraphics[width=.98\linewidth,height=74mm,keepaspectratio]{layout/book.png}
\caption{Номын жишээний нөөцийн хүснэгт ба хүсэлтийн талбар.}
\end{figure}
'''+key)
tex=tex.replace(r'\begin{figure}'+'\n',r'\begin{figure}[H]'+'\n')
tex=re.sub(r'\\includegraphics\[[^\]]+\]\{screenshots/',lambda m:r'\includegraphics[width=\linewidth,height=114mm,keepaspectratio]{screenshots/',tex)
tex=tex.replace('{verbatim}','{Cmd}')
tex=tex.replace(r'\subsection{2.7 ',r'''\begin{figure}[H]\centering
\includegraphics[width=.66\linewidth]{layout/error.png}
\caption{P0-ийн R0 хүсэлт 99, үлдсэн хэрэгцээ 7 үед харагдах мэдэгдэл.}
\end{figure}
\subsection{2.7 ''')
tables=iter([('Номын жишээний гурван хүсэлт',[.11,.22,.67]),('Түгээмэл алдаа ба шийдэл',[.36,.64]),('Хувилбар тус бүрийн туршилтын орчин',[.13,.59,.28])])
def table(m):
    title,widths=next(tables)
    data=m.group()
    weights=iter(widths)
    data=re.sub(r'\\real\{[\d.]+\}',lambda _:r'\real{'+str(next(weights))+'}',data)
    data=data.replace(r'\toprule\noalign{}',r'\toprule\rowcolor{black!6}',1)
    data=data.replace(r'\raggedright'+'\n',r'\raggedright\bfseries'+'\n')
    return r'\begingroup\small\captionof{table}{'+title+'}\n'+data+r'\endgroup'
tex=re.sub(r'\\begin\{longtable\}.*?\\end\{longtable\}',table,tex,flags=re.S)
with tempfile.TemporaryDirectory() as tmp:
    work=Path(tmp)
    (work/'body.tex').write_text(tex, encoding='utf-8')
    for name in ('layout','screenshots'):
        (work/name).symlink_to(root/name,target_is_directory=True)
    for _ in range(2):
        subprocess.run(['xelatex','-halt-on-error','-interaction=nonstopmode','layout/style.tex'],cwd=work,check=True)
    shutil.copyfile(work/'style.pdf',destination)
