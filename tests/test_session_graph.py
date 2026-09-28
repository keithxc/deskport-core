#!/usr/bin/env python3
"""Compile the production bounded path validator as both C and C++."""
from pathlib import Path
import subprocess
import tempfile
root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='deskport-graph-') as directory:
    work=Path(directory)
    source='#include <assert.h>\n#include "'+str(root/'include/deskport/session_graph.h')+'"\nint main(void) {\n'
    a,b,c=('"'+value*64+'"' for value in ('a','b','c'))
    source+=f'const char* path[16]={{{a},{b}}};\n'
    source+=f'assert(dp_session_path_check(path,2,{c})==0);\n'
    source+=f'assert(dp_session_path_check(path,2,{a})==1);\n'
    source+=f'assert(dp_session_path_check(path,0,{c})==2);\n'
    source+=f'assert(dp_session_path_check(path,16,{c})==2);\n'
    source+=f'path[1]={a}; assert(dp_session_path_check(path,2,{c})==1);\n'
    source+=f'path[1]="invalid"; assert(dp_session_path_check(path,2,{c})==2);\n'
    source+='assert(!dp_session_identity_valid(0)); return 0; }\n'
    for compiler,suffix in [('cc','c'),('c++','cpp')]:
        file=work/f'test.{suffix}';file.write_text(source)
        subprocess.run([compiler,str(file),'-o',str(work/'test')],check=True)
        subprocess.run([str(work/'test')],check=True)
print('PASS: session path validation in C and C++')
