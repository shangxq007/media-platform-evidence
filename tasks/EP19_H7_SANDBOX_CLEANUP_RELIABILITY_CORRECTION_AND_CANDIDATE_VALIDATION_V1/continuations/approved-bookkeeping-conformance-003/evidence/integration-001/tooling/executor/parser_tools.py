"""Byte-copy only required packages from candidate-owned existing dependencies."""
from pathlib import Path
import json,shutil
from execution import D,O
from coverage import put,digest

def prepare():
 dest=D/'tools';dest.mkdir(exist_ok=False);(dest/'node_modules').mkdir();(dest/'package.json').write_text('{"private":true}\n')
 src=O/'sources/frontend/frontend/node_modules';pending=[src/n for n in ['acorn','postcss','postcss-value-parser','parse5','vite']];done={}
 while pending:
  root=pending.pop();name=str(root.relative_to(src))
  if name in done:continue
  if not root.is_dir() or root.is_symlink():raise RuntimeError('PARSER_PACKAGE_MISSING_OR_LINK '+name)
  package=json.loads((root/'package.json').read_text());target=dest/'node_modules'/name
  shutil.copytree(root,target,copy_function=shutil.copy,dirs_exist_ok=True)
  done[name]={'version':package['version'],'source':str(root),'files':{str(p.relative_to(dest)):digest(p) for p in target.rglob('*') if p.is_file()}}
  deps=list(package.get('dependencies',{}))+[n for n in package.get('optionalDependencies',{}) if 'linux-x64' in n]
  for dep in deps:
   candidates=[p/'node_modules'/dep for p in [root,*root.parents] if p.is_relative_to(src.parent)]
   resolved=next((p for p in candidates if p.is_dir()),None)
   if resolved is None:
    if dep in package.get('optionalDependencies',{}):continue
    raise RuntimeError('DEPENDENCY_MISSING '+dep)
   pending.append(resolved)
 put(dest/'MANIFEST.json',done)
 return done
if __name__=='__main__':prepare()
