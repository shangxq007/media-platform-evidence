"""Strict external29 runtime binding for the approved second-attempt driver."""
from pathlib import Path
import hashlib, json, os, re

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT.parents[2]
HISTORICAL_O = Path('/home/user/Documents/workspace/audit-runs/EP19_H7_EXACT_CANDIDATE_GATE_OUTPUT_ISOLATION_CORRECTION_AND_REVALIDATION_V1')
HISTORICAL_D = HISTORICAL_O/'run-output-completeness-20260907T143346Z/baseline-sequence-20260908T070258Z'
PARENT = '689ab9456461a8d19a72d059f5157092efc43aff'
CANONICAL = '86d6aef94fd5e58da552e97c11473cff6eca734e'
SCHEMA = 'ep19-external29-runtime-binding-v1'

def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def unique(pairs):
    result={}
    for key,value in pairs:
        if key in result: raise RuntimeError('DUPLICATE_INPUT_KEY '+key)
        result[key]=value
    return result
def read(path): return json.loads(Path(path).read_text(), object_pairs_hook=unique)
def require(value, reason):
    if not value: raise RuntimeError(reason)
def exact_path(value):
    path=Path(value)
    require(path.is_absolute() and path.resolve()==path, 'NONEXACT_INPUT_PATH')
    return path

def load(config, expected_digest):
    config=exact_path(config)
    require(config.is_relative_to(ROOT.parent/'evidence'), 'CONFIG_OUTSIDE_INTEGRATION_EVIDENCE')
    require(re.fullmatch('[0-9a-f]{64}', expected_digest or '') and digest(config)==expected_digest,
            'CONFIG_SEAL_MISMATCH')
    value=read(config)
    required={'schema','root','clone_source','candidate','tree','immediate_parent',
              'canonical_comparison_base','control_root','matrix_sha256','inventories',
              'run_id','owner','owner_sha256','dependency','dependency_sha256',
              'qualification','qualification_sha256','adapter_qualification',
              'adapter_qualification_sha256','reviewed_delta','source_binding','product_patch_sha256'}
    require(set(value)==required and value['schema']==SCHEMA, 'STRICT_BINDING_SCHEMA')
    require(value['root']==str(ROOT), 'WRONG_ROOT')
    require(value['candidate']=='a29864343ed4f630b052c20d86c23b240f13cfd0' and
            value['tree']=='fd37409d0274662abbe86f69e3d963c05b379696', 'WRONG_CANDIDATE')
    require(value['immediate_parent']==PARENT and value['canonical_comparison_base']==CANONICAL,
            'WRONG_PARENT_OR_BASE')
    require(value['product_patch_sha256']=='bab6aee8346f7ef47ca94f1e3da629e7ae81df2f16202706ae4966864a485690',
            'WRONG_PRODUCT_PATCH')
    require(re.fullmatch(r'candidate-formal-002-[a-z0-9][a-z0-9_-]{1,48}', value['run_id'] or ''),
            'RUN_ID_MUST_BE_NEW_002_NAMESPACE')
    source=exact_path(value['clone_source']); require(source==TASK/'checkout' and source.is_dir(), 'WRONG_CLONE_SOURCE')
    control=exact_path(value['control_root']); require(control==ROOT/'candidate-inputs-v3', 'WRONG_CONTROL_ROOT')
    matrix=control/'GATE_EXECUTION_MATRIX.json'; require(digest(matrix)==value['matrix_sha256'], 'MATRIX_SEAL_MISMATCH')
    require(len(read(matrix)['order'])==29 and len(set(read(matrix)['order']))==29, 'EXACT_29_REQUIRED')
    inputs={path.name:digest(path) for path in sorted((control/'inputs').iterdir()) if path.is_file()}
    require(inputs==value['inventories'], 'INVENTORY_UNIVERSE_OR_HASH_CHANGED')
    for key in ('owner','dependency','qualification','adapter_qualification'):
        path=exact_path(value[key]); require(path.is_file() and digest(path)==value[key+'_sha256'], key.upper()+'_BINDING_CHANGED')
    delta=value['reviewed_delta']; require(set(delta)=={'path','sha256'}, 'DELTA_BINDING_SCHEMA')
    delta_path=exact_path(delta['path']); require(digest(delta_path)==delta['sha256'], 'DELTA_BINDING_CHANGED')
    actual={str(path):digest(path) for path in sorted(ROOT.rglob('*')) if path.is_file() and '__pycache__' not in path.parts and 'outputs' not in path.relative_to(ROOT).parts}
    require(actual==value['source_binding'], 'INTEGRATION_SOURCE_BINDING_CHANGED')
    return {**value, 'run_ids':[value['run_id']]}

def from_environment():
    require(bool(os.environ.get('H7_BINDING_CONFIG')) and bool(os.environ.get('H7_BINDING_SHA256')),
            'SEALED_CANDIDATE_INPUT_REQUIRED')
    return load(os.environ['H7_BINDING_CONFIG'], os.environ['H7_BINDING_SHA256'])

def closure():
    value=from_environment(); control=Path(value['control_root'])
    return [Path(os.environ['H7_BINDING_CONFIG']), Path(value['owner']), Path(value['dependency']),
            Path(value['qualification']), Path(value['adapter_qualification']), Path(value['reviewed_delta']['path']),
            control/'GATE_EXECUTION_MATRIX.json', *(control/'inputs'/name for name in value['inventories'])]
