"""Version 3: typed completeness gate for the recorded boundary format.
Pure offline validation. No input mutation, observation, coercion or fallback.
The original semantic function is retained below as _semantic for auditability.
"""

def verify(trace, expected, actual_restoration):
    errors = []

    def field(obj, key, kind, path, *, nullable=False, minimum=None):
        at = path + '.' + key
        if key not in obj:
            errors.append('MISSING:' + at)
            return None
        value = obj[key]
        if value is None:
            if not nullable:
                errors.append('NULL:' + at)
            return None
        if type(value) is not kind:
            errors.append('TYPE:' + at)
            return None
        if kind is str and not value:
            errors.append('VALUE:' + at + ':nonempty')
        if minimum is not None and value < minimum:
            errors.append('VALUE:' + at + ':minimum_' + str(minimum))
        return value

    def object_value(value, path):
        if type(value) is not dict:
            errors.append(('NULL:' if value is None else 'TYPE:') + path)
            return False
        return True

    def snapshot(value, path, armed=False):
        if not object_value(value, path):
            return
        if armed:
            field(value, 'documentId', str, path)
        for key in ('store', 'lifetime'):
            field(value, key, int, path, minimum=1)
        field(value, 'revision', int, path, minimum=0)
        field(value, 'refs', list, path)
        field(value, 'primary', dict, path, nullable=not armed)

    if not object_value(trace, 'trace') or not object_value(expected, 'expected'):
        return {'passed': False, 'errors': errors}
    snapshot(expected, 'expected', armed=True)
    field(trace, 'documentId', str, 'trace')
    rows = field(trace, 'rows', list, 'trace')
    if type(actual_restoration) is not bool:
        errors.append(('NULL:' if actual_restoration is None else 'TYPE:') + 'actual_restoration')
    event_types = {'early-pagehide': 'pagehide', 'late-pagehide': 'pagehide',
                   'freeze': 'freeze', 'early-pageshow': 'pageshow'}
    critical = {'early-pagehide', 'notify', 'late-pagehide', 'freeze'}
    if rows is not None:
        for index, row in enumerate(rows):
            path = 'trace.rows[' + str(index) + ']'
            if not object_value(row, path):
                continue
            field(row, 'seq', int, path, minimum=1)
            kind = field(row, 'kind', str, path)
            document = field(row, 'documentId', str, path)
            if document is not None and document != expected.get('documentId'):
                errors.append('SEMANTIC:' + path + '.documentId:expected_document')
            if kind in critical:
                armed = field(row, 'armed', dict, path)
                if armed is not None:
                    snapshot(armed, path + '.armed', armed=True)
                stores = field(row, 'stores', list, path)
                if stores is not None:
                    for j, store in enumerate(stores):
                        snapshot(store, path + '.stores[' + str(j) + ']')
            if kind in event_types:
                event = field(row, 'event', dict, path)
                if event is not None:
                    field(event, 'id', int, path + '.event', minimum=1)
                    recorded_type = field(event, 'type', str, path + '.event')
                    if recorded_type is not None and recorded_type != event_types[kind]:
                        errors.append('VALUE:' + path + '.event.type:expected_' + event_types[kind])
                    field(event, 'trusted', bool, path + '.event')
                    field(event, 'persisted', type(None) if kind == 'freeze' else bool,
                          path + '.event', nullable=kind == 'freeze')
            if kind == 'freeze':
                departure = field(row, 'departure', dict, path)
                if departure is not None:
                    field(departure, 'id', int, path + '.departure', minimum=1)
                    field(departure, 'trusted', bool, path + '.departure')
                    field(departure, 'persisted', bool, path + '.departure')
            if kind in ('late-pagehide', 'freeze'):
                dom = field(row, 'dom', dict, path)
                if dom is not None:
                    field(dom, 'preview', bool, path + '.dom')
                    field(dom, 'proposal', bool, path + '.dom')
                    capture = field(dom, 'capture', list, path + '.dom')
                    if capture is not None:
                        for j, item in enumerate(capture):
                            at = path + '.dom.capture[' + str(j) + ']'
                            if object_value(item, at):
                                field(item, 'held', list, at)
    if errors:
        return {'passed': False, 'errors': errors}
    result = _semantic(trace, expected, actual_restoration)
    # Correlated pagehide evidence must retain its recorded boolean meaning.
    for index, row in enumerate(rows):
        if row['kind'] == 'late-pagehide' and (row['event']['trusted'] is not True or row['event']['persisted'] is not True):
            result['errors'].append('SEMANTIC:trace.rows[' + str(index) + '].event:trusted_persisted_pagehide')
        if row['kind'] == 'freeze' and (row['departure']['trusted'] is not True or row['departure']['persisted'] is not True):
            result['errors'].append('SEMANTIC:trace.rows[' + str(index) + '].departure:trusted_persisted_pagehide')
    result['passed'] = not result['errors']
    return result


def _semantic(trace, expected, actual_restoration):
 """Nonvacuous trusted pre-freeze departure proof; never a timer/end-of-pagehide claim."""
 errors=[]
 def need(ok,label):
  if not ok:errors.append(label)
 rows=trace.get('rows',[]);need(bool(rows),'missing_rows');need(trace.get('documentId')==expected.get('documentId'),'wrong_document');need(bool(expected.get('refs')) and expected.get('primary') is not None,'nonempty_initial_selection');need(bool(actual_restoration),'actual_bfcache_required');need([r.get('seq') for r in rows]==list(range(1,len(rows)+1)),'truncated_or_reordered_rows')
 hides=[r for r in rows if r.get('kind')=='early-pagehide'];freezes=[r for r in rows if r.get('kind')=='freeze'];shows=[r for r in rows if r.get('kind')=='early-pageshow' and r.get('event',{}).get('persisted')];need(len(hides)==1 and len(freezes)==1 and len(shows)==1,'exact_matching_departure_freeze_restore')
 if not hides or not freezes or not shows:return {'passed':False,'errors':errors}
 hide,freeze,show=hides[0],freezes[0],shows[0];eid=hide.get('event',{}).get('id');need(hide['event'].get('trusted') is True and hide['event'].get('persisted') is True,'real_persisted_pagehide');need(freeze['event'].get('trusted') is True and show['event'].get('trusted') is True,'real_freeze_and_restore');need(hide['seq']<freeze['seq']<show['seq'],'departure_before_freeze_before_restore');need(freeze.get('departure',{}).get('id')==eid,'wrong_lifecycle_event')
 def same(row):return row.get('documentId')==expected.get('documentId') and row.get('armed')==expected and len(row.get('stores',[]))==1 and row['stores'][0].get('store')==expected.get('store')
 def retired(row):return same(row) and row['stores'][0].get('refs')==[] and row['stores'][0].get('primary') is None and row['stores'][0].get('lifetime')!=expected.get('lifetime') and row['stores'][0].get('revision',-1)>expected.get('revision',-1)
 need(same(hide),'departure_store_binding');need(retired(freeze),'not_retired_at_freeze');notify=[r for r in rows if r.get('kind')=='notify' and hide['seq']<r['seq']<freeze['seq'] and retired(r)];need(bool(notify),'missing_departure_retirement_notification');late=[r for r in rows if r.get('kind')=='late-pagehide' and hide['seq']<r['seq']<freeze['seq']];need(len(late)==1 and retired(late[0]),'missing_same_event_post_retirement_pagehide');need(bool(late) and late[0].get('event',{}).get('id')==eid,'late_event_mismatch')
 for row in late+[freeze]:
  dom=row.get('dom',{});need(dom.get('preview') is False and dom.get('proposal') is False,'transient_dom_residue');cap=dom.get('capture');need(isinstance(cap,list) and len(cap)==1 and cap[0].get('held')==[],'capture_missing_or_held')
 for row in rows:
  if notify and notify[0]['seq']<=row['seq']<=show['seq'] and row.get('kind')=='notify':need(retired(row),'contradicting_late_notification')
 return {'passed':not errors,'errors':errors,'boundary':'TRUSTED_DOCUMENT_FREEZE_CALLBACK_BEFORE_SUSPENSION_WITH_MATCHED_PAGEHIDE_AND_SAME_STORE_NOTIFICATION','documentId':trace.get('documentId'),'departure_event':eid,'freeze_seq':freeze['seq'],'notification_sequences':[r['seq'] for r in notify]}
