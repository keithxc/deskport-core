#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Exercise generated C/C++/Java against the same endpoint and setting fixtures."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--java', action='store_true', help='Require a JDK and test the Java consumer too')
    args = parser.parse_args()
    subprocess.run([sys.executable, str(ROOT / 'generate.py'), '--check'], check=True)
    cases = json.loads((ROOT / 'cases.json').read_text())
    c = ['#include "deskport/tuning.h"', '#include "deskport/view_size.h"', '#include <assert.h>', '#include <string.h>', 'int main(void) {']
    for w, h, density, expected in [
        (1440/3.5, 2828/3.5, 3.5, (824, 1616, 2)),
        (2828/3.5, 1440/3.5, 3.5, (1616, 824, 2)),
        (150, 300, 4, (640, 1280, 2)), (8000, 4500, 2, (7680, 4320, 2)),
        (1024, 768, 1, (1024, 768, 1)), (128, 100000, 1, (0, 0, 0)),
        (1280, 720, "NAN", (0, 0, 0)), (100, 800, 2, (0, 0, 0)),
    ]:
        x, y, scale = expected
        c.append(f'{{ int w, h; assert(dp_view_workspace({w}, {h}, {density}, &w, &h) == {scale}); '
                 f'assert(w == {x} && h == {y}); }}')
    for w, h, out_w, out_h in [(999, 501, 998, 500), (3840, 2160, 1920, 1080), (0, 300, 1280, 720)]:
        c.append(f'{{ int w, h; dp_view_video({w}, {h}, &w, &h); assert(w == {out_w} && h == {out_h}); }}')
    java = ['import com.deskport.core.DPCatalog;', 'public class TestCatalog { public static void main(String[] args) {']
    c.append('int width, height;')
    # Two zoom choices hit the same portrait floor. Rounding before the floor
    # previously selected neighboring display modes for the identical aspect.
    for base, zoom, expected in [
        ((824, 1416, 2), 1.0, (1200, 2064)), ((824, 1416, 2), 1.2, (1200, 2064)),
        ((1416, 824, 2), 1.2, (2064, 1200)), ((1920, 1200, 1), 1.2, (1600, 1000)),
        ((640, 1200, 1), 1.5, (640, 1200)), ((7680, 4320, 1), 0.5, (7680, 4320)),
        ((1920, 1200, 1), 0.5, (3840, 2400)), ((1920, 1200, 1), 99.0, (1920, 1200)),
        ((7680, 360, 2), 1.0, (0, 0)), ((641, 1200, 1), 1.0, (0, 0)),
        ((1920, 1200, 3), 1.0, (0, 0))]:
        args_text = ','.join(map(str, (*base, zoom)))
        c.append(f'assert(dp_tuned_desktop_size({args_text}, &width, &height) == {int(expected != (0, 0))});')
        c.append(f'assert(width == {expected[0]} && height == {expected[1]});')
    for case in cases['ports']:
        port, control = case['base'], case['control']
        c += [f'assert(dp_catalog_control_port({port}) == {control});',
              f'assert(dp_catalog_is_base_port({port}) == {int(control != 0)});']
        java += [f'assert DPCatalog.controlPort({port}) == {control};',
                 f'assert DPCatalog.isBasePort({port}) == {str(control != 0).lower()};']
    for case in cases['policies']:
        c += [f'assert(dp_catalog_display_policy_valid({case["value"]}) == {int(case["valid"])});']
        java += [f'assert DPCatalog.displayPolicyValid({case["value"]}) == {str(case["valid"]).lower()};']
    c += [f'assert(DP_CATALOG_TUNING_COUNT == {len(cases["tuningLabels"])});',
          f'assert(DP_CATALOG_TUNING_DEFAULT_INDEX == {cases["defaultTuningIndex"]});']
    java += [f'assert DPCatalog.tuningValues().length == {len(cases["tuningLabels"])};',
             f'assert DPCatalog.TUNING_DEFAULT_INDEX == {cases["defaultTuningIndex"]};']
    for index, label in enumerate(cases['tuningLabels']):
        c += [f'assert(strcmp(dp_catalog_tuning_labels[{index}], "{label}") == 0);',
              f'assert(dp_catalog_tuning_values[{index}] == {label});']
        java += [f'assert DPCatalog.tuningLabels()[{index}].equals("{label}");',
                 f'assert DPCatalog.tuningValues()[{index}] == {label};']
    c += ['return 0; }']
    java += ['double[] values = DPCatalog.tuningValues(); values[0] = 99;',
             'assert DPCatalog.tuningValues()[0] == 0.5;',
             'String[] labels = DPCatalog.tuningLabels(); labels[0] = "changed";',
             'assert DPCatalog.tuningLabels()[0].equals("0.5");', '}}']
    sdk = ['-isysroot', subprocess.check_output(['xcrun', '--sdk', 'macosx', '--show-sdk-path'], text=True).strip()] if sys.platform == 'darwin' else []
    with tempfile.TemporaryDirectory(prefix='deskport-catalog-') as temp:
        work = Path(temp)
        for compiler, ext, standard in [('CC', 'c', 'c11'), ('CXX', 'cpp', 'c++11')]:
            source = work / ('test.' + ext)
            source.write_text('\n'.join(c) + '\n')
            binary = work / ('test-' + ext)
            default = ('/usr/bin/clang' if ext == 'c' else '/usr/bin/clang++') if sys.platform == 'darwin' else ('cc' if ext == 'c' else 'c++')
            subprocess.run([os.environ.get('DESKPORT_' + compiler, default), '-std=' + standard, '-Wall', '-Wextra', '-Werror', '-fsanitize=undefined,address', *sdk, '-I' + str(ROOT / 'include'), str(source), '-lm', '-o', str(binary)], check=True)
            subprocess.run([str(binary)], check=True, timeout=15)
        if args.java:
            source = work / 'TestCatalog.java'
            source.write_text('\n'.join(java) + '\n')
            subprocess.run(['javac', '-d', str(work), str(ROOT / 'java/com/deskport/core/DPCatalog.java'), str(source)], check=True)
            subprocess.run(['java', '-ea', '-cp', str(work), 'TestCatalog'], check=True, timeout=15)
    print('PASS: portable catalog fixtures (C/C++' + ('/Java' if args.java else '') + ')')


if __name__ == '__main__':
    main()
