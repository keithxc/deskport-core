#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Standalone public-contract boundary fixtures; requires only this MIT directory."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent


def literal(value):
    if isinstance(value, bool):
        return str(int(value))
    if isinstance(value, int) and value > 2**63 - 1:
        return f'UINT64_C({value})'
    if isinstance(value, int) and value > 2**31 - 1:
        return f'INT64_C({value})'
    return str(value)


def workspace_literal(value):
    return '(DPWorkspace){' + ', '.join(map(literal, value)) + '}'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--java', action='store_true')
    parser.add_argument('--work', type=Path, help='Parent directory for isolated temporary outputs')
    parser.add_argument('--json', type=Path, help='Write a machine-readable test result')
    args = parser.parse_args()
    subprocess.run([sys.executable, str(ROOT / 'generate.py'), '--check'], check=True)
    cases = json.loads((ROOT / 'expansion-cases.json').read_text())
    content = json.loads((ROOT / 'content/ui.json').read_text())
    manifest = json.loads((ROOT / 'content/apple-keys.json').read_text())
    locales = json.loads((ROOT / 'content/locales.json').read_text())
    placeholders = re.compile(r'%(?:\d+\$)?(?:[-+#0 ]*\d*(?:\.\d+)?(?:hh|ll|[hlzjtL])?[diuoxXfFeEgGaAcsp@]|\d+)|\{[^{}]*\}')
    assert len(locales) == 22
    for key in manifest['newKeys']:
        values = content[key]
        assert set(values) == set(locales), key
        assert values['en'] == key, key
        for locale, value in values.items():
            assert isinstance(value, str) and value.strip(), (key, locale)
            assert sorted(placeholders.findall(key)) == sorted(placeholders.findall(value)), (key, locale)
    for canonical in manifest['reuse'].values():
        assert canonical in content and set(content[canonical]) == set(locales), canonical
    assert manifest['tuningGuidanceKey'] == 'Higher tuning values enlarge remote controls; lower values provide more desktop space.'
    assert len(manifest['newKeys']) + len(manifest['reuse']) == 40

    native = ['#include "deskport/workspace.h"', '#include "deskport/stream_budget.h"',
              '#include "deskport/session.h"', '#include "deskport/input.h"',
              '#include <assert.h>', '#include <float.h>', '#include <string.h>', 'int main(void) {']
    for case in cases['workspace']:
        entry, values = case['entry'], case['args']
        call = {
            'encoded': lambda: 'dp_workspace_from_encoded(' + ', '.join(map(literal, values)) + ')',
            'viewport': lambda: 'dp_workspace_from_viewport(' + ', '.join(map(literal, values)) + ')',
            'combined': lambda: 'dp_workspace_for_viewport(' + ', '.join(map(literal, values)) + ')',
            'tuned': lambda: 'dp_workspace_tuned(' + workspace_literal(values[:3]) + ', ' + literal(values[3]) + ')',
        }[entry]()
        expected = workspace_literal(case['expect'])
        native.append(f'/* {case["id"]} */ {{ DPWorkspace got = {call}; '
                      f'assert(dp_workspace_equal(got, {expected})); '
                      f'assert(dp_workspace_valid(got) == {int(case["expect"][2] != 0)}); }}')
    for case in cases['arithmeticAndSession']:
        call = case['fn'] + '(' + ', '.join(map(literal, case['args'])) + ')'
        native.append(f'/* {case["id"]} */ assert({call} == {literal(case["expect"])});')
    java = ['import com.deskport.core.DPContracts;', 'public class TestExpansion { public static void main(String[] args) {']
    for case in cases['typedPredicates']:
        name, values = case['fn'], case['args']
        native.append(f'assert(dp_contract_{name}(' + ', '.join(map(literal, values)) + f') == {int(case["expect"])});')
        java_name = name.split('_')[0] + ''.join(p.title() for p in name.split('_')[1:])
        java.append(f'assert DPContracts.{java_name}(' + ', '.join(str(v) + 'L' for v in values) + f') == {str(case["expect"]).lower()};')
    for case in cases['displayResults']:
        call = 'dp_display_result_valid(' + ', '.join([
            literal(case['pending']), literal(case['sequence']), workspace_literal(case['requested']),
            literal(case['width']), literal(case['height']), literal(case['error'])]) + ')'
        native.append(f'/* {case["id"]} */ assert({call} == {int(case["expect"])});')
    # Public names, independent pause/rate channels, and saver off/on/off.
    native += [
        'assert(strcmp(DP_MESSAGE_SESSION_STATUS, "session-status") == 0);',
        'assert(strcmp(DP_CAP_VIDEO_RATE, "videoRate") == 0 && DP_CAP_VIDEO_RATE_VERSION == 1);',
        'assert(DP_MOD_LEFT_CONTROL == 1 && DP_MOD_RIGHT_CONTROL == 16);',
        'assert(DP_BITRATE_MAX_FPS == 120);',
        'assert(DP_HID_KEY_NON_US_BACKSLASH == 0x64 && DP_HID_KEY_INTERNATIONAL_3 == 0x89);',
        'assert(DP_VK_LSHIFT == 0xa0 && DP_VK_RSHIFT == 0xa1 && DP_VK_OEM_102 == 0xe2);',
        'assert(dp_pause_result_valid(3, 3, 1, 1, 0));',
        'assert(dp_rate_result(8, 8, 3750, 3750, 1, 0) == DP_RATE_ACK_APPLIED);',
        'assert(dp_bitrate_start(15000, 40000, 1, 1) == 40000);',
        'assert(dp_bitrate_effective(15000, 40000, 0) == 40000);',
        'assert(dp_bitrate_effective(15000, 40000, 1) == 3750);',
        'assert(dp_bitrate_effective(15000, 40000, 0) == 40000);',
        'assert(dp_workspace_equal((DPWorkspace){0,0,0}, (DPWorkspace){0,0,0}));',
        'assert(!dp_workspace_equal((DPWorkspace){1920,1200,1}, (DPWorkspace){1920,1200,2}));',
        'assert(!dp_workspace_equal((DPWorkspace){1920,1200,1}, (DPWorkspace){1920,1080,1}));',
        'return 0; }',
    ]
    java += ['assert DPContracts.MESSAGE_SESSION_STATUS.equals("session-status");',
             'assert DPContracts.CAP_VIDEO_RATE.equals("videoRate") && DPContracts.CAP_VIDEO_RATE_VERSION == 1;',
             'assert DPContracts.MOD_LEFT_CONTROL == 1 && DPContracts.MOD_RIGHT_CONTROL == 16;',
             'assert DPContracts.BITRATE_MAX_FPS == 120;',
             'assert DPContracts.HID_KEY_NON_US_BACKSLASH == 0x64 && DPContracts.HID_KEY_INTERNATIONAL_3 == 0x89;',
             'assert DPContracts.VK_OEM_102 == 0xe2;', '}}']
    sdk = ['-isysroot', subprocess.check_output(['xcrun', '--sdk', 'macosx', '--show-sdk-path'], text=True).strip()] if sys.platform == 'darwin' else []
    languages = [('c', 'c11', 'CC', 'clang' if sys.platform == 'darwin' else 'cc'),
                 ('cpp', 'c++11', 'CXX', 'clang++' if sys.platform == 'darwin' else 'c++')]
    if sys.platform == 'darwin':
        languages.append(('m', 'c11', 'CC', 'clang'))
    if args.work:
        args.work.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='portable-expansion-', dir=args.work) as temp:
        work = Path(temp)
        # No parent project paths are available through the compiler's include path.
        include = work / 'include'
        shutil.copytree(ROOT / 'include', include)
        for extension, standard, env, default in languages:
            source = work / ('test.' + extension)
            # C++11 does not provide C compound literals; use aggregate values.
            text = '\n'.join(native).replace('(DPWorkspace){', 'DPWorkspace{') if extension == 'cpp' else '\n'.join(native)
            source.write_text(text + '\n')
            binary = work / ('test-' + extension)
            compiler = os.environ.get('DESKPORT_' + env, '/usr/bin/' + default if sys.platform == 'darwin' else default)
            subprocess.run([compiler, '-std=' + standard, '-Wall', '-Wextra', '-Werror', '-pedantic',
                            '-fsanitize=undefined,address,float-cast-overflow', *sdk, '-I' + str(include),
                            str(source), '-lm', '-o', str(binary)], check=True)
            subprocess.run([str(binary)], check=True, timeout=20)
        if args.java:
            source = work / 'TestExpansion.java'
            source.write_text('\n'.join(java) + '\n')
            subprocess.run(['javac', '-d', str(work), str(ROOT / 'java/com/deskport/core/DPContracts.java'), str(source)], check=True)
            subprocess.run(['java', '-ea', '-cp', str(work), 'TestExpansion'], check=True, timeout=20)
    report = {'schema': 1, 'status': 'passed', 'nativeLanguages': [x[1] + (' Objective-C' if x[0] == 'm' else '') for x in languages],
              'sanitizers': ['address', 'undefined', 'float-cast-overflow'], 'java': args.java,
              'fixtures': {key: len(cases[key]) for key in ('workspace', 'arithmeticAndSession', 'typedPredicates', 'displayResults')},
              'content': {'newKeys': len(manifest['newKeys']), 'reusedKeys': len(manifest['reuse']), 'locales': len(locales),
                          'placeholderParity': True, 'nativeSpeakerReview': 'pending'},
              'acceptance': 'standalone portable contracts only'}
    if args.json:
        args.json.write_text(json.dumps(report, indent=2) + '\n')
    print('PASS: portable expansion native boundary fixtures' + (' and Java' if args.java else '') + ', 40 product keys / 22 locales')


if __name__ == '__main__':
    main()
