"""Read-only recovery and source bindings; no execution of historical modules."""
from pathlib import Path
import ast,hashlib,json,os,re
from execution import D,O,H,SHA,TREE,git
from coverage import digest

def source_recovery(root):
    root=Path(root);tracked=[os.fsdecode(x) for x in git(root,'ls-tree','-r','--name-only','-z',SHA).split(b'\0') if x]
    selected=[n for n in tracked if n.endswith(('.gradle','.gradle.kts')) or n in ['gradlew','gradle.properties','settings.gradle.kts','frontend/package.json','frontend/package-lock.json','frontend/vite.config.ts','.github/workflows/ci.yml'] or (n.startswith(('scripts/','typed-schema-module/test/','docs/architecture/governance/automated-guards/')) and n.endswith(('.py','.sh')))]
    files={n:digest(root/n) for n in selected};calls=[]
    for n in selected:
        text=(root/n).read_text()
        for i,line in enumerate(text.splitlines(),1):
            if re.search(r'(subprocess\.|ProcessBuilder|commandLine\(|^\s*(?:bash|python3|node|\./gradlew)\s|npm (?:run|ci)|vite build|/tmp/Faof2Graph)',line):calls.append({'path':n,'line':i,'text':line.strip()})
    return {'candidate':SHA,'tree':TREE,'source_files':files,'invocation_references':calls,
      'recovered_contract':{'resources':'platform-app applies org.springframework.boot; root applies java. No custom platform-app resource transforms or frontend Gradle task found in candidate Gradle files.',
       'backend_frontend':'run_full_deterministic_backend_suite.py runs only supplied Gradle test command. check-architecture-drift invokes Python source guards. Foundation regeneration negatives copy scripts/config into mktemp fixtures. No backend Gradle npm/vite producer hook present.',
       'full_suite':'Coordinator writes its own TSV manifest before exactly one Gradle invocation; unsupported write-manifest-only/shadow-result flags removed from external runner only.',
       'foundation':'pfirr1RemediationCheck -> jooqFoundationCheck + verifyPfirr1AuthenticationAuthority; verifyJooqRegenerationFailClosed -> typed-schema-module/test/regenerate-jooq-schema-fail-closed-test.sh -> disposable copied regenerate-jooq-schema.sh. No skipping.',
       'formal':'validate-faof2.sh hardcodes /tmp/Faof2Graph.glob/.vo; external bwrap binds run tmp over /tmp. Shared container engine remains separate scoped external runtime; :Z mount requires disabled SELinux or separate parent disposition.',
       'docker':'DOCKER_BUILD absent from authoritative 29-entry matrix. Prior matrix.py proposing 30 was never executed here; runtime_image_publish=false is recorded in input classifier.'},
      'historical_contract_sources':{str(p):digest(p) for p in [O/'inputs/original-native_runner.py',O/'inputs/original-shadow_monitor.py',O/'inputs/original-control.py',O/'inputs/MONITOR_CONTRACT.txt']},
      'authority':'Read-only source analysis, not gate results or independent acceptance'}
