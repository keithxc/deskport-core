#!/usr/bin/env python3
"""Compile real C/C++ implementations against reviewed, shared golden vectors."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--apple-header', type=Path)
    group.add_argument('--qt-header', type=Path)
    args = parser.parse_args()
    cases = json.loads((ROOT / 'fixtures/workspace.json').read_text())
    adapter = 'apple' if args.apple_header else 'qt' if args.qt_header else 'core'
    header = args.apple_header or args.qt_header or ROOT / 'include/deskport/workspace.h'
    lines = [f'#include "{header.resolve()}"', '#include <stdio.h>', 'int main(void) {']
    for case in cases:
        def literal(value):
            return {'nan': 'NAN', 'inf': 'INFINITY'}.get(str(value), str(value))
        width, height, scale = map(literal, case['pixels'])
        expected = case[adapter]
        if adapter == 'qt':
            # Qt's public adapter takes integer pixels; nonfinite tests target C/Apple.
            if isinstance(case['pixels'][0], str) or isinstance(case['pixels'][1], str):
                continue
            call = f'DeskPortDisplay::forClient(QSize({width}, {height}), {scale})'
            values = ['s.pixels.width()', 's.pixels.height()', 's.scale']
            declaration = 'const auto'
        else:
            call = (f'DPWorkspaceForViewport(({width}) / ({scale}), ({height}) / ({scale}), {scale})'
                    if adapter == 'apple' else f'dp_workspace_from_pixels({width}, {height}, {scale})')
            values = ['s.width', 's.height', 's.scale']
            declaration = 'const DPWorkspace'
        checks = ' && '.join(f'{value} == {number}' for value, number in zip(values, expected))
        lines.append(f'{{ {declaration} s = {call}; if (!({checks})) {{ fprintf(stderr, "FAIL: {case["name"]}\\n"); return 1; }} }}')
    if adapter == 'core':
        for size, valid in [([640,360,1],1),([7680,4320,2],1),([638,360,1],0),([640,362,1],0),([1920,1080,3],0),([7684,4320,2],0),([640,356,1],0)]:
            lines.append(f'{{ DPWorkspace s = {{{",".join(map(str,size))}}}; if (dp_workspace_valid(s) != {valid}) return 2; }}')
    lines += ['return 0;', '}']
    with tempfile.TemporaryDirectory(prefix='deskport-core-') as tmp:
        work = Path(tmp)
        if adapter == 'qt':
            (work/'main.cpp').write_text('\n'.join(lines))
            (work/'test.pro').write_text('QT = core\nCONFIG += console c++17\nCONFIG -= app_bundle\nSOURCES = main.cpp\nTARGET = workspace\n')
            subprocess.run([os.environ.get('DESKPORT_QMAKE', 'qmake'), 'test.pro'],cwd=work,check=True,stdout=subprocess.DEVNULL)
            subprocess.run(['make','-j2'],cwd=work,check=True,stdout=subprocess.DEVNULL)
            subprocess.run([str(work/'workspace')],check=True)
        else:
            for language, compiler, standard in [('c',os.environ.get('CC','/usr/bin/clang' if sys.platform=='darwin' else 'cc'),'c11'),
                                                  ('cpp',os.environ.get('CXX','/usr/bin/clang++' if sys.platform=='darwin' else 'c++'),'c++17')]:
                # Apple adapter contains existing C compound literals; exercise it as C.
                if adapter == 'apple' and language == 'cpp': continue
                source=work/f'main.{language}'; source.write_text('\n'.join(lines))
                binary=work/language
                subprocess.run([compiler,f'-std={standard}','-Wall','-Wextra','-Werror','-pedantic',
                                '-fsanitize=undefined,address',str(source),'-lm','-o',str(binary)],check=True)
                subprocess.run([str(binary)],check=True)
    print(f'PASS: {adapter} workspace contract ({len(cases)} vectors; Qt skips nonfinite pixel inputs)')

if __name__ == '__main__': main()
