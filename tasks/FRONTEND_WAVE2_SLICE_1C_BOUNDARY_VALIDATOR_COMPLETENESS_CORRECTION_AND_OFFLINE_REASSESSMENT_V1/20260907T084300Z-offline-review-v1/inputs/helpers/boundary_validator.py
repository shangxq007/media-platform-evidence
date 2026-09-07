def verify(trace, expected, actual_restoration):
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
