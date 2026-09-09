"""Additional pure validation assertions; imports no IO implementation."""
import copy
import json
import unittest
from dataclasses import replace
from runtime_handle import _bound_handle
from boundary import Authority, identity, snapshot_target, parse_config
from model import Config, Failure, PENDING, PostizProjector, secret_variants, ensure_redacted
from wire import parse_head, strict_json, parse_response, MAX_HEADERS
from test_model import raw_config, post, LOCAL, UPSTREAM, START, END

class PureBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.config = Config.from_mapping(raw_config())
        self.a = Authority(self.config,LOCAL,UPSTREAM,'rev1')
        self.handle = _bound_handle(('127.0.0.1',49152),'rev1')  # pure metadata, no listener
        self.a.attach(self.handle)
        self.headers = {'host':self.handle.host_header,'authorization':LOCAL,
                        'x-observation-identity':json.dumps(identity(self.config))}

    def denied(self,headers=None,target='/observations/access',method='GET'):
        with self.assertRaises(Failure):
            self.a.authorize(method,target,self.headers if headers is None else headers)

    def test_each_identity_field_exact_and_null_tenant(self):
        original = identity(self.config)
        paths = [('binding','scope',k) for k in original['binding']['scope']]
        paths += [('binding','ownerId'),('provider',),('instance',),('account',),('startInclusive',),('endExclusive',)]
        for path in paths:
            altered = copy.deepcopy(original)
            parent = altered
            for k in path[:-1]: parent = parent[k]
            parent[path[-1]] = 'changed'
            with self.subTest(path=path):
                self.denied(dict(self.headers,**{'x-observation-identity':json.dumps(altered)}))
        self.assertIsNone(self.a.authorize('GET','/observations/access',self.headers))
        self.assertIsNone(original['binding']['scope']['tenantId'])

    def test_revision_query_duplicates_and_no_caller_destination(self):
        headers = dict(self.headers,**{'x-observation-revision':'rev1'})
        target = snapshot_target(self.config,'r1')
        self.assertEqual(self.a.authorize('GET',target,headers),'r1')
        for suffix in ('&requestId=r2','&url=http://127.0.0.1','&limit=1','&credential=secret'):
            self.denied(headers,target+suffix)
        self.denied(dict(headers,**{'x-observation-revision':'stale'}),target)
        self.denied(headers,target.replace('2026-10-01','2026-10-02'))

    def test_method_route_body_and_header_default_deny(self):
        for verb in ('POST','PUT','PATCH','DELETE','CONNECT','OPTIONS','HEAD','TRACE'):
            self.denied(method=verb)
        for target in ('https://example.invalid','/observations/access?x=1','/posts','/integrations','//observations/access'):
            self.denied(target=target)
        for extra in ({'content-length':'1'},{'origin':'http://x.invalid'},{'x-credential':'not-accepted'}):
            self.denied(dict(self.headers,**extra))

    def test_access_expiry_retirement_and_read_reservation(self):
        clock = [1]
        a = Authority(replace(self.config,max_reads=3),LOCAL,UPSTREAM,'rev1',lambda:clock[0])
        a.reserve_snapshot()
        self.assertEqual(a.reads,2)
        with self.assertRaises(Failure) as caught: a.reserve_snapshot()
        self.assertEqual(caught.exception.code,'READ_BUDGET_EXHAUSTED')
        self.assertEqual(a.reads,2)
        clock[0] = 1801
        with self.assertRaises(Failure): a.receipt()
        self.a.retire()
        with self.assertRaises(Failure): self.a.publish(lambda:self.fail('retired callback invoked'))
        self.assertEqual(self.a.published,0)

    def test_owner_config_mutation_does_not_change_access_receipt(self):
        before = self.a.receipt()
        self.config.binding['scope']['projectId'] = 'changed'
        self.assertEqual(self.a.receipt(),before)

    def test_credentials_config_closed_and_no_encoded_leaks(self):
        for secret in ('short','x'*4097,'abcdefgh12345678\r\nX: y','abcdefghijklmnop é'):
            with self.assertRaises(Failure): Authority(self.config,secret,UPSTREAM,'rev1')
        with self.assertRaises(Failure): Authority(self.config,LOCAL,LOCAL,'rev1')
        for secret in (LOCAL,UPSTREAM):
            for representation in secret_variants(secret):
                with self.subTest(kind='representation'), self.assertRaises(Failure):
                    ensure_redacted({'nested':{'key':representation}},(LOCAL,UPSTREAM),1048576)
                with self.subTest(kind='object-key'), self.assertRaises(Failure):
                    ensure_redacted({representation:'ordinary'},(LOCAL,UPSTREAM),1048576)
        for config in (raw_config(organization_read_consent=False),raw_config(credential='forbidden'),raw_config(synthetic=1),raw_config(max_reads=True),raw_config(approved_ip='127.0.0.2')):
            with self.assertRaises(Failure): Config.from_mapping(config)
        # Supplied config bytes only, no real credential file or environment read.
        for text in (b'{"provider":"postiz","provider":"other"}',b'{}',b'[]',b'x'*(MAX_HEADERS+1)):
            with self.assertRaises(Failure): parse_config(text)

class PureWireTests(unittest.TestCase):
    def test_http_framing_rejects_ambiguity_injection_and_sizes(self):
        for extra in (b'Content-Length: 0\r\nContent-Length: 0\r\n',b'Transfer-Encoding: chunked\r\n',b'Content-Length: +1\r\n',b'Content-Length: 01\r\n',b'Bad : x\r\n',b'X: y\nz\r\n',b' X: y\r\n',b'X: \x00\r\n'):
            with self.subTest(extra=extra),self.assertRaises(Failure):
                parse_head(b'GET /observations/access HTTP/1.1\r\n'+extra+b'\r\n')
        with self.assertRaises(Failure): parse_head(b'x'*(MAX_HEADERS+1))
        with self.assertRaises(Failure): parse_head(b'HTTP/1.1 200 OK\r\n\r\n',True)
        self.assertEqual(parse_head(b'HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\n',True),(200,{'content-length':'2'}))

    def test_json_duplicate_nonfinite_malformed_and_content_types(self):
        for body in (b'{"a":1,"a":2}',b'NaN',b'Infinity',b'\xff',b'{',b'['*2000):
            with self.subTest(body_kind=body[:1]),self.assertRaises(Failure): strict_json(body)
        self.assertEqual(strict_json(b'{"a":[]}'),{'a':[]})
        for headers in ({'content-type':'text/application/json'},{'content-type':'application/json','content-encoding':'gzip'}):
            with self.assertRaises(Failure): parse_response(200,headers,b'{}',1024)
        with self.assertRaises(Failure): parse_response(200,{'content-type':'application/json'},b'x'*1025,1024)

    def test_all_upstream_failure_classes_are_value_free(self):
        expected = {400:('UPSTREAM_BAD_REQUEST',502),401:('UPSTREAM_AUTH',403),403:('UPSTREAM_AUTH',403),404:('UPSTREAM_NOT_FOUND',502),429:('UPSTREAM_RATE_LIMIT',429),500:('UPSTREAM_FAILURE',502),503:('UPSTREAM_FAILURE',502),302:('UPSTREAM_REDIRECT',502)}
        for status,pair in expected.items():
            with self.subTest(status=status),self.assertRaises(Failure) as caught:
                parse_response(status,{},('private '+UPSTREAM).encode(),1024)
            self.assertEqual((caught.exception.code,caught.exception.status),pair)
            self.assertEqual(str(caught.exception),pair[0])
            self.assertIsNone(caught.exception.__cause__)

class PureMissingProjectionTests(unittest.TestCase):
    def setUp(self):
        self.config = Config.from_mapping(raw_config(max_records=1))
        self.accounts = [{'id':'account1','disabled':False,'name':'channel','identifier':'synthetic'}]
        self.projector = PostizProjector(self.config,LOCAL,UPSTREAM)

    def project(self,rows):
        return self.projector.project(self.accounts,{'posts':rows},'r1','2026-09-09T13:00:00Z')

    def test_dates_start_end_cap_recurrence_and_foreign_account(self):
        result = self.project([post(id='a',publishDate=START),post(id='b'),post(id='c',publishDate=END),post(id='d',intervalInDays=2),post(id='e',integration={'id':'other'})])
        self.assertEqual(result['observations'][0]['externalReferences']['post'],'a')
        self.assertEqual(result['omissions'],{'recurrence':1,'outsideWindow':1,'recordCap':1})
        self.assertEqual(result['completeness'],'partial')

    def test_missing_optional_values_unknown_relations_required_values_fail(self):
        row = post(state=None)
        row.pop('content')
        value = self.project([row])['observations'][0]
        self.assertEqual(value['displayStatus'],'unknown')
        self.assertTrue(all(v=={'status':PENDING} for v in value['relationships'].values()))
        self.assertNotIn('summary',value)
        for field in ('id','publishDate','integration'):
            broken = post(); broken.pop(field)
            with self.subTest(field=field),self.assertRaises(Failure): self.project([broken])
        with self.assertRaises(Failure): self.project([post(integration={})])

    def test_duplicate_recurring_ids_and_account_rows_fail(self):
        with self.assertRaises(Failure): self.project([post(intervalInDays=1),post()])
        self.accounts *= 2
        with self.assertRaises(Failure): self.project([])


class PureClientProjectionTests(unittest.TestCase):
    def test_client_rejects_cross_scope_invented_graph_and_wrong_date(self):
        from boundary import validate_snapshot
        config = Config.from_mapping(raw_config())
        accounts = [{'id':'account1','name':'channel','identifier':'synthetic','disabled':False}]
        value = PostizProjector(config,LOCAL,UPSTREAM).project(accounts,{'posts':[post()]},'r1','2026-09-09T13:00:00Z')
        value['evidence'] = 'synthetic-http-observation'
        self.assertEqual(validate_snapshot(value,config,'r1'),value)
        for field in ('provider','instance','account'):
            altered = copy.deepcopy(value)
            altered['observations'][0]['externalReferences'][field] = 'foreign'
            with self.subTest(field=field),self.assertRaises(Failure): validate_snapshot(altered,config,'r1')
        for changes in ({'relationships':{'attempts':[]}}, {'publishedAt':START}, {'scheduledAt':END}, {'displayStatus':'failed'}):
            altered = copy.deepcopy(value)
            altered['observations'][0].update(changes)
            with self.subTest(change=list(changes)),self.assertRaises(Failure): validate_snapshot(altered,config,'r1')
        with self.assertRaises(Failure): validate_snapshot(value,config,'wrong-request')
