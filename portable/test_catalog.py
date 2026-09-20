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
    c = ['#include "deskport/catalog.h"', '#include <assert.h>', '#include <string.h>', 'int main(void) {']
    java = ['import com.deskport.core.DPCatalog;', 'public class TestCatalog { public static void main(String[] args) {']
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
            subprocess.run([os.environ.get('DESKPORT_' + compiler, default), '-std=' + standard, '-Wall', '-Wextra', '-Werror', '-fsanitize=undefined,address', *sdk, '-I' + str(ROOT / 'include'), str(source), '-o', str(binary)], check=True)
            subprocess.run([str(binary)], check=True, timeout=15)
        if args.java:
            source = work / 'TestCatalog.java'
            source.write_text('\n'.join(java) + '\n')
            subprocess.run(['javac', '-d', str(work), str(ROOT / 'java/com/deskport/core/DPCatalog.java'), str(source)], check=True)
            subprocess.run(['java', '-ea', '-cp', str(work), 'TestCatalog'], check=True, timeout=15)
    print('PASS: portable catalog fixtures (C/C++' + ('/Java' if args.java else '') + ')')


if __name__ == '__main__':
    main()
