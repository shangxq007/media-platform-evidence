from pathlib import Path
D=Path(__file__).resolve().parents[1]

def validate_output(target,area,protected=(),reserved=()):
    target=Path(target);area=Path(area)
    if not target.is_absolute() or target!=target.resolve() or area!=area.resolve():
        raise RuntimeError('UNRESOLVED_OR_SYMLINK_OUTPUT')
    if target==area or not target.is_relative_to(area):
        raise RuntimeError('ESCAPING_OR_SHARED_OUTPUT')
    for p in [*protected,*reserved]:
        p=Path(p).resolve()
        if target==p or target.is_relative_to(p) or p.is_relative_to(target):
            raise RuntimeError('PROTECTED_OR_OVERLAPPING_OUTPUT')
    if target.exists() and not target.is_dir():raise RuntimeError('NON_DIRECTORY_OUTPUT')
    return target

def frontend_command(output):
    output=validate_output(output,D/'outputs',[D/'sources'],[D/'outputs/backend'])
    return ['npm','run','build','--','--outDir',str(output)]
