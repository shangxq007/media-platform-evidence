"""Exact candidate Git -> checkout -> Gradle resources -> uncompressed ZIP assets."""
from pathlib import Path, PurePosixPath
import argparse, hashlib, json, os, stat, zipfile
from execution import SHA,TREE,git
from preservation import capture_files

STATIC='platform-app/src/main/resources/static/'
def sha(data):return hashlib.sha256(data).hexdigest()
def expected(root):
    root=Path(root)
    if git(root,'rev-parse','HEAD').decode().strip()!=SHA or git(root,'rev-parse','HEAD^{tree}').decode().strip()!=TREE:raise RuntimeError('WRONG_PACKAGING_CANDIDATE')
    rows=[]
    for raw in git(root,'ls-tree','-rz',SHA,'--',STATIC).split(b'\0'):
        if not raw:continue
        meta,path=raw.split(b'\t',1);mode,kind,blob=meta.decode().split();path=os.fsdecode(path)
        if kind!='blob' or mode not in ('100644','100755') or not path.startswith(STATIC):raise RuntimeError('UNSUPPORTED_STATIC_INPUT')
        data=git(root,'cat-file','blob',blob)
        rows.append({'git_path':path,'blob':blob,'mode':mode,'sha256':sha(data),'relative':path[len(STATIC):]})
    if not rows:raise RuntimeError('EMPTY_STATIC_UNIVERSE')
    files=capture_files([root/r['git_path'] for r in rows])
    for row in rows:
        if files[str(root/row['git_path'])]['sha256']!=row['sha256']:raise RuntimeError('CHECKOUT_STATIC_MISMATCH')
    return {'candidate':SHA,'tree':TREE,'rows':rows,'transforms':'NONE_SUPPORTED','frontend_external_output_consumed':False}

def validate_manifest(m):
    if m.get('candidate')!=SHA or m.get('tree')!=TREE or m.get('transforms')!='NONE_SUPPORTED':raise RuntimeError('WRONG_CANDIDATE_OR_UNSUPPORTED_TRANSFORM')
    rows=m['rows']
    if not rows or len({r['relative'] for r in rows})!=len(rows):raise RuntimeError('EMPTY_OR_DUPLICATE_STATIC_INPUT')
    for r in rows:
        if PurePosixPath(r['relative']).is_absolute() or '..' in PurePosixPath(r['relative']).parts or r['git_path']!=STATIC+r['relative']:raise RuntimeError('INVALID_STATIC_PATH')
    return {r['relative']:r['sha256'] for r in rows}

def resources(m,path):
    from preservation import Collector
    wanted=validate_manifest(m);r=Collector(roots=[path],expected_nonempty=[path]).capture()
    if r['result']!='COMPLETE':raise RuntimeError('RESOURCE_CAPTURE_INCOMPLETE '+repr(r['errors']))
    got={str(Path(p).relative_to(path)):v['sha256'] for p,v in r['entries'].items() if 'sha256' in v}
    if got!=wanted:raise RuntimeError('RESOURCE_MISSING_EXTRA_OR_HASH_MISMATCH')
    for row in m['rows']:
        if r['entries'][str(Path(path)/row['relative'])]['git_blob']!=row['blob']:raise RuntimeError('WRONG_GIT_BLOB')
    return {'result':'PASS','root':str(path),'sha256_by_relative_path':got}

def jar(m,path,rule):
    wanted=validate_manifest(m)
    if rule.get('task')!=':platform-app:bootJar' or rule.get('resources_task')!=':platform-app:processResources' or rule.get('transforms')!='NONE_SUPPORTED':raise RuntimeError('UNSUPPORTED_PACKAGING_RULE')
    with zipfile.ZipFile(path) as z:
        names=z.namelist()
        if len(names)!=len(set(names)):raise RuntimeError('DUPLICATE_ZIP_ENTRY')
        for n in names:
            p=PurePosixPath(n)
            if p.is_absolute() or '..' in p.parts or '\\' in n or str(p)!=n.rstrip('/'):raise RuntimeError('UNSAFE_ZIP_PATH')
            mode=z.getinfo(n).external_attr>>16
            if stat.S_ISLNK(mode):raise RuntimeError('ZIP_SYMLINK')
            if any(str(parent) in names and not str(parent).endswith('/') for parent in p.parents if str(parent)!='.'):raise RuntimeError('ZIP_FILE_DIRECTORY_CONFLICT')
        prefixes={n.split('static/',1)[0] for n in names if 'static/' in n and not n.endswith('/')}
        # A Spring Boot layout must agree with its actual manifest. Prefix is
        # discovered from entries first, then checked against packaging evidence.
        if len(prefixes)!=1:raise RuntimeError('MISSING_OR_AMBIGUOUS_STATIC_PREFIX')
        prefix=next(iter(prefixes))
        mf=z.read('META-INF/MANIFEST.MF').decode('utf-8').replace('\r\n','\n')
        declared=[line.split(': ',1)[1] for line in mf.splitlines() if line.startswith('Spring-Boot-Classes: ')]
        if declared!=[prefix] or rule.get('boot_classes')!=prefix:raise RuntimeError('ZIP_PREFIX_RULE_MISMATCH')
        got={n[len(prefix+'static/'):]:sha(z.read(n)) for n in names if n.startswith(prefix+'static/') and not n.endswith('/')}
        if got!=wanted:raise RuntimeError('JAR_MISSING_EXTRA_OR_HASH_MISMATCH')
        for row in m['rows']:
            body=z.read(prefix+'static/'+row['relative'])
            if hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()!=row['blob']:raise RuntimeError('WRONG_GIT_BLOB')
    return {'result':'PASS','jar':str(path),'jar_sha256':sha(Path(path).read_bytes()),'discovered_prefix':prefix,
            'entries':[{**r,'jar_entry':prefix+'static/'+r['relative'],'uncompressed_sha256':got[r['relative']]} for r in m['rows']],
            'crc_is_provenance':False,'frontend_external_output_consumed':False}

def actual(root,resource_root,archive=None,rule=None):
    m=expected(root);result={'candidate':SHA,'tree':TREE,'source_manifest':m,'resources':resources(m,Path(resource_root))}
    result['jar']=jar(m,archive,rule) if archive else {'result':'NOT_BUILT_CHECK_SCHEDULED_AFTER_BOOTJAR'}
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--resources',type=Path,required=True);p.add_argument('--jar',type=Path);p.add_argument('--rule',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    r=actual(a.root,a.resources,a.jar,json.loads(a.rule.read_text()) if a.rule else None)
    with a.output.open('x') as f:json.dump(r,f,indent=2);f.write('\n')
if __name__=='__main__':main()
