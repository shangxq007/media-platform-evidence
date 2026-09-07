from pathlib import Path
p=Path('executor/runner.py');s=p.read_text().replace('import bindings,','import namespaces, artifacts, compile_inventory\nimport bindings,')
s=s.replace("REPOS=[D/'sources'/n for n in ('backend','frontend','shadow-fixture')]",'def repos(run):return namespaces.repos(run)')
s=s.replace('def identities():','def identities(run):').replace('for root in REPOS:', 'for root in repos(run):')
s=s.replace("scope=load(O/'PROTECTION_SCOPE.json');objects={}","scope=load(O/'PROTECTION_SCOPE.json');objects={}")
s=s.replace("for root in map(Path,scope['repositories']):",'for root in repos(run):')
s=s.replace("m=bindings.build(run);put", "namespaces.prepare(run)\n    m=bindings.build(run);put")
s=s.replace('engineering.source_recovery()',"engineering.source_recovery(run/'sources/backend')")
s=s.replace("'Existing candidate source clones retained.'", "'Fresh run-owned independent clones.'")
s=s.replace('Existing candidate source clones retained.', 'Fresh per-run independent clones; original checkouts never execute.')
s=s.replace('owned/runner.py','executor/runner.py')
s=s.replace('ids=identities();','ids=identities(run);')
s=s.replace("[run/'bindings.json',run/'prepare.json',run/'identity.json',run/'source-recovery.json']", "[run/'bindings.json',run/'prepare.json',run/'identity.json',run/'source-recovery.json',run/'namespaces.json']")
s=s.replace("env.update(EP19_RUN_ROOT=str(run),EP19_HELPER_ROOT=str(H),EP19_GATE_ID=name)","env.update(EP19_RUN_ROOT=str(run),EP19_HELPER_ROOT=str(H),EP19_GATE_ID=name,EP19_CANDIDATE=SHA)")
s=s.replace("environment('frontend' if name.startswith('FRONTEND_') else 'backend',run)","environment('frontend' if name.startswith('FRONTEND_') else 'shadow' if name=='SHADOW' else 'backend',run)")
s=s.replace("for lane in ('backend','frontend'):","for lane in ('backend','frontend','shadow'):")
s=s.replace("if name=='APPLICATION_PROBE':\n            cp=", "if name=='APPLICATION_PROBE':\n            artifacts.live_equal([run/'runtime/outputs/backend/classpath.txt'],results.values(),run)\n            cp=")
s=s.replace("dependency_files=coverage.seal(depfiles)","artifacts.live_equal(depfiles,results.values(),run)\n            dependency_files=coverage.seal(depfiles)")
s=s.replace("if name=='COMPILE' and not any(p.suffix=='.class' for p in generated):raise RuntimeError('COMPILE_REQUIRED_CLASSES_MISSING')", "if name=='COMPILE':\n            r['compile']=compile_inventory.validate(run,gate,repo)\n            put(gate/'compile-manifest.json',r['compile'])")
s=s.replace("r['result']='PASS';r['wrapper_exit']=0", "r['result']='VALIDATED_AWAITING_INDEPENDENT_COPY'")
a=s.index('    # Immutable copied evidence is used by dependencies;');b=s.index('\ndef compare_baseline',a)
s=s[:a]+'''    # Every accepted path (including mutable builds, JARs and producer events)
    # is independently copied before PASS. Failed evidence remains in-place.
    try:
        if r['result']=='VALIDATED_AWAITING_INDEPENDENT_COPY':
            evidence=artifacts.files(gate)
            evidence+=list(map(Path,r.get('acceptance',{}).get('outputs',{})))
            evidence+=generated
            for row in r.get('packaging',[]):evidence+=list(map(Path,row['files']))
            if name=='APPLICATION_CLASSPATH':
                for p in map(Path,(run/'runtime/outputs/backend/classpath.txt').read_text().strip().split(os.pathsep)):
                    evidence+=artifacts.files(p) if p.is_dir() else [p]
            def recheck(saved):
                for row in r.get('packaging',[]):
                    event=Path(row['event']);rule=load(saved[str(event/'rule.json')]);check=load(saved[str(event/'check.json')])
                    # Producer's Git -> checkout -> processResources mapping was
                    # checked in doLast; rebind it to the independently copied ZIP.
                    if rule['actual_task']==':platform-app:bootJar':
                        r.setdefault('preserved_packaging',[]).append(packaging.jar(check['source_manifest'],saved[rule['archive_file']],rule))
            artifacts.finalize(r,gate,evidence,recheck)
    except Exception as error:
        r.update(result='FAIL',wrapper_exit=1,error_type=type(error).__name__,reason=str(error),traceback=traceback.format_exc())
    put(gate/'receipt.json',r);return r
''' +s[b:]
# Rebound scope is a strict extension with output roots moved, no canonical relaxation.
s=s.replace("for key in ('repositories','metadata_roots','cross_lane','shared_git','shadow_root','shadow_declared'):","for key in ('cross_lane','shared_git','shadow_declared'):")
s=s.replace("if set(scope['allowed'])!={str(run/'runtime'),*old['allowed']}:problems.append('OUTPUT_SCOPE_EXPANDED')", "expected_roles=namespaces.scope_roles(dict(scope),run)\n        for key in ('repositories','metadata_roots','shadow_root','allowed'):\n            if scope[key]!=expected_roles[key]:problems.append('RUN_SCOPE_MAPPING_CHANGED '+key)")
s=s.replace("('prepare','bindings','identity','source-recovery','toolchain','scope','baseline')", "('prepare','bindings','identity','source-recovery','toolchain','scope','baseline','namespaces')")
p.write_text(s)
p=Path('executor/coverage.py');s=p.read_text().replace('controls=[p for p in D.iterdir() if p.is_file()]',"controls=[p for p in O.iterdir() if p.is_file()] + [D/'CODEX_BRIEF.md']")
s=s.replace('    return scope\n','    import namespaces\n    return namespaces.scope_roles(scope,run)\n',1)
p.write_text(s)
p=Path('executor/parsers.py');s=p.read_text();s=s.replace("if not (o/'frontend/index.html').is_file():raise RuntimeError('VITE_OUTPUT_INCOMPLETE')", "import vite_closure\n        result['closure']=vite_closure.validate(o/'frontend',resolution['base'],repo/'frontend',gate/'vite-closure.json')")
p.write_text(s)
p=Path('executor/vite_resolution.mjs');s=p.read_text().replace('build:{outDir}', 'build:{outDir,manifest:true}').replace('publicDir:c.publicDir','publicDir:c.publicDir,base:c.base,manifest:c.build.manifest');p.write_text(s)
# No new loose-object acceptance. Preserve original exclusions; unresolved append fails.
p=Path('executor/observe.py');s=p.read_text().replace("for e in pending:e['category']='AUTHORIZED_FRONTEND_REACHABLE_NEW_OBJECT_APPEND_WRITER_UNKNOWN'", "for e in pending:e['category']='REJECT_UNRESOLVED_SHARED_METADATA_SCOPE'")
p.write_text(s)
