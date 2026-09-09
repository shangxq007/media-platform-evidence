"""Materialize the finite parser runtime from its fixed, source-bound package tree."""
from pathlib import Path
import hashlib
import json

from binding_contract import HISTORICAL_O
import durability

DIRECT_PACKAGES=("acorn","postcss","postcss-value-parser","parse5")
SOURCE_ROOT=HISTORICAL_O/'sources/frontend/frontend/node_modules'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _resolve(requester,name,source_root):
    for parent in (requester,*requester.parents):
        if parent==source_root.parent:break
        candidate=parent/'node_modules'/name
        if candidate.is_dir() and not candidate.is_symlink():return candidate
    top=source_root/name
    if top.is_dir() and not top.is_symlink():return top
    return None


def source_graph(source_root=SOURCE_ROOT):
    """Enumerate the actual direct imports and every reachable package dependency once."""
    source_root=Path(source_root).absolute()
    pending=[(None,name,source_root/name,"direct-parser-import") for name in DIRECT_PACKAGES]
    nodes={};edges=[]
    while pending:
        caller,requested,root,kind=pending.pop(0)
        if not root.is_dir() or root.is_symlink():
            raise RuntimeError('PARSER_PACKAGE_MISSING_OR_LINK '+requested)
        package_path=root/'package.json'
        package=json.loads(package_path.read_text())
        canonical=package.get('name',requested)
        if canonical in nodes:
            existing=nodes[canonical]
            if existing['root']!=str(root):raise RuntimeError('PARSER_PACKAGE_VERSION_AMBIGUITY '+canonical)
        else:
            files={}
            for path in sorted(root.rglob('*')):
                if path.is_symlink():raise RuntimeError('PARSER_PACKAGE_SYMLINK '+str(path))
                if path.is_file():files[str(path.relative_to(root))]=digest(path)
                elif not path.is_dir():raise RuntimeError('PARSER_PACKAGE_SPECIAL '+str(path))
            nodes[canonical]={'requested_as':requested,'version':package.get('version'),
                              'root':str(root),'package_json':str(package_path),
                              'package_json_sha256':digest(package_path),'files':files}
            dependencies={**package.get('dependencies',{})}
            optional=package.get('optionalDependencies',{})
            for dependency in sorted(set(dependencies)|set(optional)):
                resolved=_resolve(root,dependency,source_root)
                if resolved is None:
                    if dependency in optional:continue
                    raise RuntimeError('PARSER_DEPENDENCY_MISSING '+canonical+' -> '+dependency)
                pending.append((canonical,dependency,resolved,'package-dependency'))
        edge={'caller':caller or 'vite_closure.mjs','callee':canonical,'requested':requested,'kind':kind}
        if edge not in edges:edges.append(edge)
    return {'source_root':str(source_root),'direct_packages':list(DIRECT_PACKAGES),
            'nodes':nodes,'edges':sorted(edges,key=lambda row:(row['caller'],row['callee'],row['requested'],row['kind']))}


def prepare(run,source_root=SOURCE_ROOT):
    """Durably copy only the bound graph into this run's isolated parser cache."""
    graph=source_graph(source_root)
    dest=Path(run)/'runtime/cache/frontend/parser-tools'
    durability.exclusive_directory(dest,0o700)
    durability.exclusive_directory(dest/'node_modules',0o700)
    durability.exclusive_bytes(dest/'package.json',b'{"private":true}\n',0o400)
    for name,row in sorted(graph['nodes'].items()):
        target=dest/'node_modules'/name
        durability.ensure_directory(target,0o700)
        root=Path(row['root'])
        for relative,wanted in sorted(row['files'].items()):
            source=root/relative
            payload=source.read_bytes()
            if hashlib.sha256(payload).hexdigest()!=wanted:raise RuntimeError('PARSER_SOURCE_CHANGED '+name+'/'+relative)
            durability.exclusive_bytes(target/relative,payload,0o400)
    raw=(json.dumps(graph,indent=2,sort_keys=True)+'\n').encode()
    durability.exclusive_bytes(dest/'MANIFEST.json',raw,0o400)
    return graph
