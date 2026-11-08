"""Capture real execution and reliability evidence for the lab report."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import textwrap
from PIL import Image,ImageDraw,ImageFont

ROOT = Path(__file__).resolve().parents[1]


def capture(args: list[str]) -> str:
    result = subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',
                            env=dict(os.environ,PYTHONIOENCODING='utf-8'),check=False)
    if result.returncode:
        raise RuntimeError(result.stdout+result.stderr)
    return result.stdout+result.stderr


def image(name: str,command: str,output: str) -> None:
    folder = ROOT/'docs/screenshots'
    folder.mkdir(parents=True,exist_ok=True)
    font = ImageFont.truetype('C:/Windows/Fonts/consola.ttf',21)
    lines = []
    for line in (command+'\n\n'+output).expandtabs(4).splitlines():
        lines.extend(textwrap.wrap(line,width=88,subsequent_indent='  ') or [''])
    canvas = Image.new('RGB',(1200,len(lines)*29+48),'#16202b')
    draw = ImageDraw.Draw(canvas)
    for i,line in enumerate(lines):
        draw.text((24,24+i*29),line,font=font,fill='#edf2f7')
    canvas.save(folder/(name+'.png'))


def main() -> None:
    python = str(ROOT/'.venv/Scripts/python.exe')
    if not Path(python).exists():
        python = sys.executable
    results = ROOT/'docs/results'
    results.mkdir(parents=True,exist_ok=True)
    demo = capture([python,'-m','book_io','--config','config.yaml'])
    tests = capture([python,'-m','unittest','discover','-s','tests','-v'])
    (results/'application.txt').write_text(demo,encoding='utf-8')
    (results/'tests.txt').write_text(tests,encoding='utf-8')
    shutil.copy2(ROOT/'logs/application.log',results/'application.log')
    shutil.copy2(ROOT/'output/books.json',results/'books.json')
    image('application','python -m book_io --config config.yaml',demo)
    log = (results/'application.log').read_text(encoding='utf-8').splitlines()[-8:]
    image('log','Фрагмент application.log','\n'.join(log))
    data = json.loads((results/'experiments.json').read_text(encoding='utf-8'))
    text = 'Records  eager s  streaming s  eager MiB  streaming MiB\n'
    for row in data['benchmark']:
        a,b = row['eager'],row['streaming']
        text += f"{row['records']:7} {a['seconds']:8.4f} {b['seconds']:12.4f} {a['peak_bytes']/1048576:10.3f} {b['peak_bytes']/1048576:14.3f}\n"
    image('benchmark','Фактичне повне споживання CSV',text)
    # Preserve a readable chain while omitting long local paths in the figure.
    chain = (results/'exception_chain.txt').read_text(encoding='utf-8')
    chain = chain.replace(str(ROOT),'PROJECT')
    image('chain','Exception chaining',chain)


if __name__ == '__main__':
    main()
