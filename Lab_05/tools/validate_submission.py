"""Check report identity, separate-lab layout and actual reliability evidence."""
from pathlib import Path
import json
import re
from xml.etree import ElementTree
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'


def validate() -> None:
    reports = [ROOT/'docs/Lab_05_Report_Variant_2.docx',ROOT/'Lab_05/report/report.docx']
    if ROOT.name == 'Lab_05':
        reports = [ROOT/'report/report.docx']
    for report in reports:
        with ZipFile(report) as archive:
            tree = ElementTree.fromstring(archive.read('word/document.xml'))
        text = ' '.join(''.join(t.itertext()) for t in tree.iter(W+'t')).casefold()
        for phrase in ('лабораторної роботи №5','варіант №2','бровді олександр',
                       'імпорт та експорт системи обліку книг','isbn','yaml','atomic',
                       'strict','tolerant','exception chaining','500 000','70.'):
            if phrase not in text:
                raise ValueError(f'Missing report requirement: {phrase}')
        assert set(re.findall(r'варіант\s*№?\s*(\d+)',text)) == {'2'}
        assert 'заставний денис' not in text
    assert {p.resolve() for p in ROOT.rglob('*.docx') if '.venv' not in p.parts} == {
        p.resolve() for p in reports}
    if len(reports) == 2:
        assert reports[0].read_bytes() == reports[1].read_bytes()
        for folder in ('src','data','tests','tools'):
            for p in (ROOT/folder).rglob('*'):
                if (p.is_file() and not any(part in p.parts for part in ('__pycache__','generated'))
                        and not any(part.endswith('.egg-info') for part in p.parts)):
                    assert p.read_bytes() == (ROOT/'Lab_05'/p.relative_to(ROOT)).read_bytes(),p
        evidence = json.loads((ROOT/'docs/results/experiments.json').read_text(encoding='utf-8'))
        strict,tolerant = evidence['policies']
        assert (strict['valid'],strict['invalid'],strict['exported']) == (1000,1,0)
        assert (tolerant['valid'],tolerant['invalid'],tolerant['exported']) == (1000,10,1000)
        assert evidence['atomic']['previous_preserved'] and evidence['atomic']['temporary_files'] == 0
        assert [x['records'] for x in evidence['benchmark']] == [10000,100000,500000]
        assert len(evidence['configuration']) == 6
    print('PASS: Lab_05, variant 2, book I/O, report identity and five reliability experiments.')


if __name__ == '__main__':
    validate()
