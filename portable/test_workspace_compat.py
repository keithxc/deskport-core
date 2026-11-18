#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Public workspace vectors compiled using isolated MIT headers only."""

# Guard direct test/build entrypoints before local imports or output creation.
import sys as _storage_sys
_storage_sys.dont_write_bytecode = True
_storage_sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[1]))
import build_storage as _build_storage
if __name__ == '__main__':
    _build_storage.bootstrap()

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent


def literal(value):
    return {'nan': 'NAN', 'NAN': 'NAN', 'inf': 'INFINITY'}.get(str(value), str(value))


def aggregate(value):
    return '(DPWorkspace){' + ','.join(map(str, value)) + '}'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--json', type=Path)
    args = parser.parse_args()
    data = json.loads((ROOT / 'fixtures/workspace-compat.json').read_text())
    checks = []

    def expect(call, value):
        checks.append(f'CHECK(dp_workspace_equal({call}, {aggregate(value)}));')

    for case in data['drawable']:
        w, h, d = map(literal, case['args'])
        expect(f'dp_workspace_from_drawable_pixels({w},{h},{d})', case['pixels'])
        expect(f'dp_workspace_from_drawable_viewport(({w})/({d}),({h})/({d}),{d})', case['viewport'])
        # Qt's existing failure sentinel belongs to its thin value adapter.
        expect(f'qt_proposal({w},{h},{d})', case['qt'])
    for case in data['ui']:
        w, h, d = map(literal, case['args'])
        expect(f'dp_workspace_from_viewport(({w})/({d}),({h})/({d}),{d})', case['expect'])
    for case in data['adjust']:
        base, tuning = case['args'][:3], literal(case['args'][3])
        expect(f'dp_workspace_adjust({aggregate(base)},{tuning})', case['expect'])
    for key, functions in [('host', ['for_host', 'for_macos', 'for_windows']), ('saver', ['for_saver'])]:
        for case in data[key]:
            for fn in functions:
                expect(f'dp_workspace_{fn}({aggregate(case["args"])})', case['expect'])
    for case in data['composition']:
        expect(f'dp_workspace_for_host(dp_workspace_adjust({aggregate(case["base"])},{case["factor"]}))', case['expect'])
    # Existing tuned preserves the original aspect and quantizes only once.
    expect('dp_workspace_tuned((DPWorkspace){824,1416,2},1.2)', [1200,2064,2])
    expect('dp_workspace_from_viewport(400,225,2)', [800,452,2])
    expect('dp_workspace_from_drawable_viewport(400,225,2)', [1920,1080,2])
    native = r'''
#include "deskport/workspace.h"
#include <float.h>
#include <limits.h>
#include <stdio.h>
#define CHECK(expression) do { if (!(expression)) { fprintf(stderr,"failed line %d: %s\n",__LINE__,#expression); return 1; } } while (0)
static DPWorkspace qt_proposal(double w, double h, double d) {
    DPWorkspace value = dp_workspace_from_drawable_pixels(w,h,d);
    DPWorkspace sentinel = {-1,-1,1};
    return value.scale ? value : sentinel;
}
int main(void) {
'''
    native += '\n'.join(checks)
    native += r'''
    DPWorkspace request = {1300,748,2}, portrait = {1080,1920,2};
    DPWorkspace modes[] = {{1920,1080,1},{1280,720,1},{1080,1920,1}};
    CHECK(dp_workspace_equal(dp_workspace_select_mode(request,NULL,0),request));
    CHECK(dp_workspace_equal(dp_workspace_select_mode(request,modes,0),request));
    CHECK(dp_workspace_equal(dp_workspace_select_mode(request,modes,3),modes[1]));
    CHECK(dp_workspace_equal(dp_workspace_select_mode(portrait,modes,3),modes[2]));
    DPWorkspace ties[] = {{1280,720,2},{1280,720,1}};
    CHECK(dp_workspace_equal(dp_workspace_select_mode(request,ties,2),ties[0]));
    DPWorkspace swapped[] = {{1280,720,1},{1280,720,2}};
    CHECK(dp_workspace_equal(dp_workspace_select_mode(request,swapped,2),swapped[0]));
    DPWorkspace square = {1000,1000,1};
    DPWorkspace distances[] = {{960,960,2},{1040,1040,1}};
    CHECK(dp_workspace_equal(dp_workspace_select_mode(square,distances,2),distances[0]));
    DPWorkspace reversed[] = {{1040,1040,1},{960,960,2}};
    CHECK(dp_workspace_equal(dp_workspace_select_mode(square,reversed,2),reversed[0]));
    DPWorkspace direction[] = {{1080,1920,1},{7680,4320,2}};
    CHECK(dp_workspace_equal(dp_workspace_select_mode(request,direction,2),direction[1]));
    DPWorkspace aspect[] = {{1300,800,1},{2560,1472,2},{2600,1496,1}};
    CHECK(dp_workspace_equal(dp_workspace_select_mode(request,aspect,3),aspect[2]));
    DPWorkspace boundary = {7680,4320,2}, minimum = {640,360,1};
    DPWorkspace many[96];
    for (int i=0;i<96;++i) many[i]=minimum;
    many[95]=boundary;
    CHECK(dp_workspace_equal(dp_workspace_select_mode(boundary,many,96),boundary));
    CHECK(dp_workspace_equal(dp_workspace_select_mode(minimum,many,96),minimum));
    const int counts[] = {-1,97,INT_MIN,INT_MAX};
    for (unsigned i=0;i<sizeof(counts)/sizeof(counts[0]);++i)
        CHECK(dp_workspace_equal(dp_workspace_select_mode(request,modes,counts[i]),(DPWorkspace){0,0,0}));
    CHECK(dp_workspace_equal(dp_workspace_select_mode(request,NULL,1),(DPWorkspace){0,0,0}));
    DPWorkspace bad[] = {{0,0,0},{639,360,1},{640,362,1},{7684,4320,2},
                         {640,4324,1},{640,360,0},{640,360,-1},{640,360,3},{INT_MAX,INT_MIN,2}};
    for (unsigned i=0;i<sizeof(bad)/sizeof(bad[0]);++i) {
        DPWorkspace with_bad[] = {{1280,720,1},bad[i]};
        CHECK(dp_workspace_equal(dp_workspace_select_mode(request,with_bad,2),(DPWorkspace){0,0,0}));
        CHECK(dp_workspace_equal(dp_workspace_select_mode(bad[i],modes,3),(DPWorkspace){0,0,0}));
        CHECK(dp_workspace_equal(dp_workspace_select_mode(bad[i],NULL,0),(DPWorkspace){0,0,0}));
        CHECK(dp_workspace_equal(dp_workspace_adjust(bad[i],1.3),(DPWorkspace){0,0,0}));
        CHECK(dp_workspace_equal(dp_workspace_for_host(bad[i]),(DPWorkspace){0,0,0}));
        CHECK(dp_workspace_equal(dp_workspace_for_saver(bad[i]),(DPWorkspace){0,0,0}));
    }
    many[95]=bad[0]; /* Validate the entire list even after an exact match. */
    CHECK(dp_workspace_equal(dp_workspace_select_mode(minimum,many,96),(DPWorkspace){0,0,0}));
    CHECK(dp_workspace_equal(dp_workspace_adjust(request,INFINITY),request));
    CHECK(dp_workspace_equal(dp_workspace_adjust(request,-INFINITY),request));
    CHECK(dp_workspace_equal(dp_workspace_adjust(request,DBL_MAX),request));
    CHECK(dp_workspace_equal(dp_workspace_from_drawable_pixels(DBL_MAX,DBL_MAX,0.5),(DPWorkspace){4320,4320,1}));
    CHECK(dp_workspace_equal(dp_workspace_from_drawable_viewport(DBL_MAX,DBL_MAX,8),(DPWorkspace){4320,4320,2}));
    CHECK(dp_workspace_equal(dp_workspace_from_drawable_pixels(DBL_MIN,DBL_MAX,1),(DPWorkspace){4,4320,1}));
    CHECK(dp_workspace_equal(dp_workspace_from_drawable_viewport(128,DBL_MAX,1),(DPWorkspace){0,0,0}));
    CHECK(dp_workspace_equal(dp_workspace_from_drawable_viewport(127.99,1000,2),(DPWorkspace){0,0,0}));
    const double bad_edges[] = {NAN,INFINITY,-INFINITY,0,-1};
    for (unsigned i=0;i<sizeof(bad_edges)/sizeof(bad_edges[0]);++i) {
        CHECK(dp_workspace_equal(dp_workspace_from_drawable_pixels(1920,bad_edges[i],2),(DPWorkspace){0,0,0}));
        CHECK(dp_workspace_equal(dp_workspace_from_drawable_viewport(960,bad_edges[i],2),(DPWorkspace){0,0,0}));
    }
    const double bad_density[] = {NAN,INFINITY,-INFINITY,0,-1,0.49,8.01,DBL_MAX};
    for (unsigned i=0;i<sizeof(bad_density)/sizeof(bad_density[0]);++i) {
        CHECK(dp_workspace_equal(dp_workspace_from_drawable_pixels(1920,1080,bad_density[i]),(DPWorkspace){0,0,0}));
        CHECK(dp_workspace_equal(dp_workspace_from_drawable_viewport(960,540,bad_density[i]),(DPWorkspace){0,0,0}));
    }
    /* Sweep bounds and every catalog factor; every nonzero result is wire-valid. */
    const int widths[] = {640,824,1920,7680};
    const int heights[] = {360,748,1920,4320};
    for (unsigned x=0;x<4;++x) for (unsigned y=0;y<4;++y) for (int scale=1;scale<=2;++scale) {
        DPWorkspace base = {widths[x],heights[y],scale};
        for (int j=0;j<DP_CATALOG_TUNING_COUNT;++j) {
            DPWorkspace adjusted=dp_workspace_adjust(base,dp_catalog_tuning_values[j]);
            CHECK(dp_workspace_valid(adjusted));
            DPWorkspace host=dp_workspace_for_host(adjusted);
            CHECK(dp_workspace_valid(host) || dp_workspace_equal(host,(DPWorkspace){0,0,0}));
        }
    }
    return 0;
}
'''
    languages = [('c','c11','CC','clang'), ('cpp','c++11','CXX','clang++')]
    sdk = []
    if sys.platform == 'darwin':
        languages.append(('m','c11','CC','clang'))
        sdk = ['-isysroot', subprocess.check_output(['xcrun','--sdk','macosx','--show-sdk-path'],text=True).strip()]
    args.work.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='workspace-compat-',dir=args.work) as temp:
        work = Path(temp)
        shutil.copytree(ROOT / 'include', work / 'include')
        shutil.copy2(ROOT / 'LICENSE', work / 'LICENSE')
        for extension, standard, env, default in languages:
            source = work / ('workspace.' + extension)
            source.write_text(native.replace('(DPWorkspace){','DPWorkspace{') if extension=='cpp' else native)
            binary = work / ('workspace-' + extension)
            compiler = os.environ.get('DESKPORT_' + env, '/usr/bin/' + default if sys.platform=='darwin' else default)
            command = [compiler,'-std='+standard,'-Wall','-Wextra','-Werror','-pedantic',
                       '-fsanitize=address,undefined,float-cast-overflow',*sdk,'-I'+str(work/'include'),str(source),'-lm','-o',str(binary)]
            subprocess.run(command,check=True)
            subprocess.run([str(binary)],check=True,timeout=30)
    report = {'status':'passed','nativeLanguages':[x[0] for x in languages],
              'sanitizers':['address','undefined','float-cast-overflow'],
              'publicGoldenVectors':{key:len(data[key]) for key in ('drawable','ui','adjust','host','saver','composition')},
              'goldenAssertions':len(checks),'modeSelection':'ordered, invalid, ties, rotation, scales, count 0..96',
              'protocolBoundSweep':320,'isolation':'copied MIT headers and license only',
              'acceptance':'standalone public API only'}
    if args.json:
        args.json.parent.mkdir(parents=True,exist_ok=True)
        args.json.write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: portable workspace compatibility '+json.dumps(report))


if __name__ == '__main__':
    main()
