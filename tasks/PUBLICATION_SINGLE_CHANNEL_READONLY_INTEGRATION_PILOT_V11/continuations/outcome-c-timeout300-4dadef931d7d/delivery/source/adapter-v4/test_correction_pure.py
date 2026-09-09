"""New v4 pure proofs only: no transport imports, fake IO, or loop construction."""
import copy
import json
import unittest
from dataclasses import FrozenInstanceError, replace
from boundary import Authority, CONTRACT, identity, snapshot_target
from client_state import ClientState, OwnerConfig, validate_receipt, validate_envelope
from model import Config, Failure, PENDING, PostizProjector
from runtime_handle import RuntimeHandle, _bound_handle, require_handle
from test_model import raw_config, post, LOCAL, UPSTREAM, START, END

class CorrectionPureTests(unittest.TestCase):
    def setUp(self):
        self.config = Config.from_mapping(raw_config())
        # Pure metadata fixture: this does not bind, claim OS assignment or emulate IO.
        self.handle = _bound_handle(('127.0.0.1',49152),'rev-v4')
        self.state = ClientState(self.config,LOCAL,self.handle)
        self.authority = Authority(self.config,LOCAL,UPSTREAM,'rev-v4')
        self.authority.attach(self.handle)

    def test_handle_closed_typed_nonsecret_and_frozen(self):
        for value in ('http://127.0.0.1:49152',{'port':49152},49152,None):
            with self.subTest(kind=type(value).__name__),self.assertRaises(Failure): require_handle(value)
        for address in (('localhost',49152),('0.0.0.0',49152),('127.0.0.1',0),('127.0.0.1',True),('127.0.0.1',65536)):
            with self.subTest(address=address),self.assertRaises(Failure): _bound_handle(address,'rev-v4')
        with self.assertRaises(Failure): RuntimeHandle(49152,'rev-v4')
        with self.assertRaises(FrozenInstanceError): self.handle.port = 1
        self.assertEqual(self.handle.host_header,'127.0.0.1:49152')
        self.assertNotIn(LOCAL,repr(self.handle))
        self.assertNotIn(UPSTREAM,repr(self.handle))

    def test_authority_requires_attached_exact_host_and_revision(self):
        headers = {'host':self.handle.host_header,'authorization':LOCAL,'x-observation-identity':json.dumps(identity(self.config))}
        self.assertIsNone(self.authority.authorize('GET','/observations/access',headers))
        for host in ('127.0.0.1:0','127.0.0.1:49153','localhost:49152'):
            with self.subTest(host=host),self.assertRaises(Failure) as caught:
                self.authority.authorize('GET','/observations/access',dict(headers,host=host))
            self.assertEqual((caught.exception.code,caught.exception.status),('HOST_DENIED',403))
        a = Authority(self.config,LOCAL,UPSTREAM,'rev-v4')
        with self.assertRaises(Failure): a.authorize('GET','/observations/access',headers)
        with self.assertRaises(Failure): a.attach(_bound_handle(('127.0.0.1',49153),'wrong'))
        with self.assertRaises(Failure): self.authority.attach(self.handle)
        headers['x-observation-revision'] = 'stale'
        with self.assertRaises(Failure) as caught:
            self.authority.authorize('GET',snapshot_target(self.config,'r1'),headers)
        self.assertEqual((caught.exception.code,caught.exception.status),('ACCESS_RETIRED',403))
        self.assertEqual(self.authority.reads,0)

    def test_owner_config_is_detached_and_stored_frozen(self):
        expected = identity(self.config)
        captured = OwnerConfig.capture(self.config)
        self.config.binding['scope']['projectId'] = 'mutated'
        self.state.config.binding['ownerId'] = 'mutated'
        captured.view().binding['scope']['sourceId'] = 'mutated'
        self.assertEqual(identity(self.state.config),expected)
        self.assertEqual(identity(captured.view()),expected)
        with self.assertRaises(FrozenInstanceError): captured.encoded = '{}'
        with self.assertRaises(FrozenInstanceError): self.state.config.base = 'http://foreign.invalid'

    def test_invalid_request_ids_rejected_before_generation_or_acquisition(self):
        generation = self.state.begin('valid')
        for value in (None,True,1,'','x'*181,'a\r\nX: y','http://arbitrary.invalid'):
            with self.subTest(kind=type(value).__name__),self.assertRaises(Failure): self.state.begin(value)
            self.state.check(generation)
        self.assertIsNone(self.state.snapshot)

    def test_complete_method_target_revision_and_generation_preflight(self):
        generation = self.state.begin('r1')
        target = snapshot_target(self.config,'r1')
        request = self.state.prepare('GET',target,generation,'rev-v4')
        self.assertIn(('Host: '+self.handle.host_header+'\r\n').encode(),request)
        self.assertTrue(request.startswith(('GET '+target+' HTTP/1.1\r\n').encode()))
        self.assertIn(b'X-Observation-Revision: rev-v4\r\n',request)
        for method in ('POST','PUT','PATCH','DELETE','CONNECT','OPTIONS','HEAD','TRACE'):
            with self.subTest(method=method),self.assertRaises(Failure): self.state.prepare(method,target,generation,'rev-v4')
        for altered in (None,'https://foreign.invalid','/observations/access?x=1',target+'&requestId=r2',snapshot_target(self.config,'r2'),target+'\r\nX: y'):
            with self.subTest(target=altered),self.assertRaises(Failure): self.state.prepare('GET',altered,generation,'rev-v4')
        for revision in (None,True,'','wrong','rev\r\nX: y'):
            with self.subTest(revision=revision),self.assertRaises(Failure): self.state.prepare('GET',target,generation,revision)
        with self.assertRaises(Failure): self.state.prepare('GET','/observations/access',generation,'rev-v4')
        newer = self.state.begin('r2')
        with self.assertRaises(Failure): self.state.prepare('GET','/observations/access',generation)
        self.state.check(newer)

    def test_newer_generation_invalidates_older_through_checks_and_publication(self):
        older = self.state.begin('old')
        newer = self.state.begin('new')
        with self.assertRaises(Failure) as caught: self.state.check(older)
        self.assertEqual(caught.exception.code,'READ_SUPERSEDED')
        self.state.publish(newer,{'requestId':'new'},lambda:None)
        with self.assertRaises(Failure): self.state.publish(older,{'requestId':'old'},lambda:None)
        self.assertEqual(self.state.snapshot,{'requestId':'new'})

    def test_foreign_generation_is_not_current_even_with_same_number(self):
        own = self.state.begin('r1')
        other = ClientState(self.config,LOCAL,self.handle).begin('r1')
        self.assertEqual(own.number,other.number)
        with self.assertRaises(Failure): self.state.check(other)
        self.state.check(own)

    def test_retirement_clears_snapshot_and_all_outstanding_generations(self):
        generation = self.state.begin('r1')
        self.state.publish(generation,{'requestId':'r1'},lambda:None)
        self.state.retire()
        self.assertIsNone(self.state.snapshot)
        for action in (lambda:self.state.check(generation),lambda:self.state.begin('r2'),lambda:self.state.publish(generation,{},lambda:None)):
            with self.assertRaises(Failure) as caught: action()
            self.assertEqual(caught.exception.code,'CLIENT_RETIRED')

    def test_deadline_failure_does_not_publish_and_snapshots_are_detached(self):
        first = self.state.begin('r1')
        supplied = {'requestId':'r1','nested':{'x':1}}
        self.state.publish(first,supplied,lambda:None)
        supplied['nested']['x'] = 2
        self.state.snapshot['nested']['x'] = 3
        second = self.state.begin('r2')
        def deadline(): raise Failure('DEADLINE_EXCEEDED',504)
        with self.assertRaises(Failure): self.state.publish(second,{'requestId':'r2'},deadline)
        self.assertEqual(self.state.snapshot,{'requestId':'r1','nested':{'x':1}})

    def test_receipt_preserves_strict_bool_lifetime_closed_identity_and_revision(self):
        receipt = self.authority.receipt()
        self.assertEqual(validate_receipt(receipt,self.config,self.handle),receipt)
        for key,value in (('list',1),('content',0),('lifetimeSeconds',1800.0),('revision','stale'),('contract','invented'),('unknown',True)):
            changed = copy.deepcopy(receipt); changed[key] = value
            with self.subTest(key=key),self.assertRaises(Failure): validate_receipt(changed,self.config,self.handle)
        for key in receipt:
            changed = copy.deepcopy(receipt); changed.pop(key)
            with self.subTest(missing=key),self.assertRaises(Failure): validate_receipt(changed,self.config,self.handle)
        for field in ('provider','instance','account','startInclusive','endExclusive'):
            changed = copy.deepcopy(receipt); changed['identity'][field] = 'foreign'
            with self.subTest(field=field),self.assertRaises(Failure): validate_receipt(changed,self.config,self.handle)

    def envelope(self):
        accounts = [{'id':'account1','name':'channel','identifier':'synthetic','disabled':False}]
        snapshot = PostizProjector(self.config,LOCAL,UPSTREAM).project(accounts,{'posts':[post()]},'r1','2026-09-09T13:00:00Z')
        snapshot['evidence'] = 'synthetic-http-observation'
        receipt = self.authority.receipt()
        return {'contract':CONTRACT,'kind':'owner-local-snapshot-envelope','coreContract':PENDING,'receipt':receipt,'requestId':'r1','snapshot':snapshot}

    def test_envelope_snapshot_exact_provider_instance_account_window_access_contract(self):
        value = self.envelope()
        def validate(value): return validate_envelope(value,self.authority.receipt(),self.config,self.handle,'r1',LOCAL)
        self.assertEqual(validate(value),value)
        paths = [('snapshot','externalAccount','externalReferences',k) for k in ('provider','instance','account')]
        paths += [('snapshot','observations',0,'externalReferences',k) for k in ('provider','instance','account')]
        paths += [('snapshot','window',k) for k in ('startInclusive','endExclusive','semantics','upstreamEndInclusive')]
        paths += [('snapshot','access','authority'),('snapshot','contract'),('snapshot','binding','scope','projectId'),('coreContract',)]
        for path in paths:
            altered = copy.deepcopy(value); parent = altered
            for k in path[:-1]: parent = parent[k]
            parent[path[-1]] = 'foreign'
            with self.subTest(path=path),self.assertRaises(Failure): validate(altered)
        for parent,key,number in (('receipt','list',1),('receipt','content',0),('receipt','lifetimeSeconds',1800.0),('snapshot','access',None)):
            altered = copy.deepcopy(value)
            if parent == 'snapshot': altered[parent][key]['list'] = 1
            else: altered[parent][key] = number
            with self.subTest(parent=parent,key=key),self.assertRaises(Failure): validate(altered)
        altered = copy.deepcopy(value)
        altered['snapshot']['observations'] *= 2
        with self.assertRaises(Failure): validate(altered)
        altered = copy.deepcopy(value)
        altered['snapshot']['window']['extra'] = True
        with self.assertRaises(Failure): validate(altered)
