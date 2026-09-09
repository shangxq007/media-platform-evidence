"""Syntax/AST plus guarded new pure tests only; no transport import/collection."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent/'adapter-v4'

def hashes():
    return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(SOURCE.iterdir()) if p.is_file()}

before = hashes()
attempt = ROOT/f'offline-attempt-{len(list(ROOT.glob("offline-attempt-*")))+1:02d}'
attempt.mkdir()
syntax = []
transport = []
for path in sorted(list(SOURCE.glob('*.py'))+list(ROOT.glob('*.py'))):
    tree = ast.parse(path.read_bytes(),filename=str(path))
    compile(tree,str(path),'exec')
    syntax.append(str(path.relative_to(ROOT.parent)))
    if path.name == 'transport_tests.py':
        for cls in tree.body:
            if isinstance(cls,ast.ClassDef):
                for method in cls.body:
                    if isinstance(method,(ast.FunctionDef,ast.AsyncFunctionDef)) and method.name.startswith('test_'):
                        transport.append({'id':f'transport_tests.{cls.name}.{method.name}','line':method.lineno,'status':'NOT_RUN_CAPABILITY_UNQUALIFIED'})
argv = [sys.executable,'-B','run_pure.py',str(attempt/'pure-results.json')]
result = subprocess.run(argv,cwd=SOURCE,capture_output=True,text=True)
(attempt/'pure.stdout.log').write_text(result.stdout)
(attempt/'pure.stderr.log').write_text(result.stderr)
(attempt/'pure.exit').write_text(str(result.returncode)+'\n')
report = json.loads((attempt/'pure-results.json').read_text()) if (attempt/'pure-results.json').exists() else None
record = {'invocation':['python3','-B',str(Path(__file__).resolve())], 'invocation_cwd':str(Path.cwd()),
          'syntax':{'method':'AST parse + compile in memory; no bytecode or source import','files':syntax,'passed':len(syntax)},
          'pure':{'argv':argv,'cwd':str(SOURCE),'native_exit':result.returncode,'report':report},
          'source_before':before,'source_after':hashes(),'source_stable':before==hashes(),
          'transport_inventory_method':'AST only; never imported/collected','transport_identities':transport}
(attempt/'verification.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'attempt':str(attempt),'syntax_passed':len(syntax),'pure_native_exit':result.returncode,'counts':report['counts'] if report else None,'transport_ast_count':len(transport),'source_stable':record['source_stable']}))
sys.exit(result.returncode if result.returncode else 0 if record['source_stable'] else 1)
