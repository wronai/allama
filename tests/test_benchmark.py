import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from allama.benchmark import (generate, payload, thinking_mode, summarize,
                              functional_check, save_report, IMAGE)
from allama.main import LLMTester


@pytest.mark.parametrize('values,expected', [([False, True], False), (['low','medium'], 'low'),
                                             ([False,'low'], False), ([], None)])
def test_advertised_thinking(values, expected):
    assert thinking_mode({'thinking': {'values': values}}) == expected


def test_no_thinking_metadata():
    assert thinking_mode({'thinking': None}) is None
    assert thinking_mode({}) is None


@pytest.mark.parametrize('think', [False, True, 'low', 'medium'])
def test_payload_preserves_think(think):
    p = payload('model', 'prompt', think)
    assert p['think'] == think
    assert p['options'] == dict(num_ctx=8192, num_predict=1024, temperature=0, seed=42)
    assert p['stream'] is True
    assert 'think' not in payload('model', 'prompt', None)


def fake_session(chunks):
    response = Mock()
    response.iter_lines.return_value = [json.dumps(x).encode() for x in chunks]
    response.__enter__ = Mock(return_value=response)
    response.__exit__ = Mock(return_value=None)
    session = Mock()
    session.post.return_value = response
    return session


def test_stream_metrics_and_thinking():
    s = fake_session([{'message': {'thinking':'reason'}}, {'message': {'content':'code'}},
                      {'done':True,'done_reason':'stop','eval_count':20,'eval_duration':2_000_000_000}])
    r = generate(s, 'http://ollama', {})
    assert r['content'] == 'code' and r['thinking'] == 'reason'
    assert r['tokens_per_second'] == 10
    assert r['first_answer_s'] >= r['first_token_s']
    assert r['valid_answer'] and r['completed']


@pytest.mark.parametrize('chunks', [
    [{'message':{'content':'code'}}],
    [{'message':{'content':'code'},'done':True,'done_reason':'length'}],
    [{'message':{'thinking':'reason'},'done':True,'done_reason':'stop'}],
    [{'error':'backend failed'}],
])
def test_incomplete_or_empty_not_success(chunks):
    r = generate(fake_session(chunks), 'http://ollama', {})
    assert not r['valid_answer']


def test_failed_results_remain_in_denominator():
    rows = [{'model':'m','passed':True,'valid_answer':True,'wall_s':2},
            {'model':'m','passed':False,'valid_answer':False,'wall_s':100,'error':'timeout'}]
    s = summarize(rows, {'m':{}})[0]
    assert s['attempts'] == 2 and s['passed'] == 1 and s['errors'] == 1
    assert s['wall_s'] == 2 and s['tokens_per_second'] is None


@pytest.mark.parametrize('think,expected', [('false',False),('true',True),('low','low'),(False,False)])
def test_legacy_think_forwarding(think, expected):
    tester = LLMTester()
    response = Mock(status_code=200)
    response.json.return_value = {'message':{'content':'ok'}}
    with patch('allama.main.requests.post', return_value=response) as call:
        tester.make_request({'model_name':'m','url':'http://m','think':think},'hello')
    assert call.call_args.kwargs['json']['think'] == expected


def test_html_escapes_generated_content(tmp_path):
    report = {'status':'complete','models':{},'results':[], 'host':'<script>alert(1)</script>',
              'settings':{'context':8192,'limit':10,'repeats':1}, 'ollama_version':{'version':'test'},
              'tasks':[], 'planned':0,'tasks_sha256':'hash','started_at':'now'}
    save_report(report, tmp_path)
    html = (tmp_path/'index.html').read_text()
    assert '<script>alert(1)</script>' not in html
    assert '&lt;script&gt;' in html
    assert json.loads((tmp_path/'results.json').read_text())['status'] == 'complete'


@pytest.mark.parametrize('code,passed', [('def add(a,b): return a+b',True),
    ('def add(a,b): return a-b',False), ('raise SystemExit(0)',False), ('invalid python !!!',False)])
def test_container_evaluates_behavior(code, passed):
    result = functional_check(code,'assert add(2,3) == 5')
    assert result['passed'] is passed, result


def test_container_has_no_network():
    code = "import socket\ndef check():\n    try:\n        socket.create_connection(('1.1.1.1', 443), timeout=.1)\n    except OSError:\n        return True\n    return False"
    assert functional_check(code, 'assert check()')['passed']


def test_timeout_kills_container():
    r = functional_check('while True: pass', '', timeout=1)
    assert not r['passed'] and 'timeout' in r['output']


def test_infrastructure_errors_not_scored_as_wrong_code():
    rows = [{'model':'m','passed':False,'valid_answer':True,'wall_s':2,
             'evaluation':{'status':'infra_error'}}]
    result = summarize(rows, {'m':{}})[0]
    assert result['attempts'] == 1 and result['evaluated'] == 0
    assert result['infra_errors'] == 1


def test_container_launch_failure_is_infrastructure_error():
    process = Mock(returncode=125, stdout='', stderr='daemon unavailable')
    with patch('allama.benchmark.subprocess.run', return_value=process):
        result = functional_check('x=1', 'assert x==1')
    assert result['status'] == 'infra_error'


def test_reevaluate_rejects_running_report(tmp_path):
    from allama.benchmark import reevaluate
    (tmp_path/'results.json').write_text(json.dumps({'status':'running'}))
    with pytest.raises(ValueError, match='running'):
        reevaluate(tmp_path)


def test_resume_preserves_answers_and_audits_transport_failures():
    from allama.benchmark import resume_report
    saved = {'settings':{},'tasks_sha256':'hash','planned':2,'url':'http://old',
             'models':{'m':{'digest':'abc'}}, 'results':[
                 {'model':'m','task':'a','repeat':1,'passed':False},
                 {'model':'m','task':'b','repeat':1,'error':'NameResolutionError'}]}
    expected = {'settings':{},'tasks_sha256':'hash','planned':2,
                'planned_models':['m'], 'url':'http://new'}
    result = resume_report(saved, expected, {'m':{'digest':'abc'}})
    assert len(result['results']) == 1 and not result['results'][0]['passed']
    assert len(result['superseded_transport_attempts']) == 1
    assert result['status'] == 'running' and result['url'] == 'http://new'


@pytest.mark.parametrize('change', ['settings','tasks_sha256','planned','digest'])
def test_resume_rejects_incomparable_run(change):
    from allama.benchmark import resume_report
    saved = {'settings':{},'tasks_sha256':'hash','planned':2,'url':'http://old',
             'models':{'m':{'digest':'abc'}}, 'results':[]}
    expected = {'settings':{},'tasks_sha256':'hash','planned':2,
                'planned_models':['m'], 'url':'http://new'}
    tags = {'m':{'digest':'abc'}}
    if change == 'digest':
        tags['m']['digest'] = 'different'
    else:
        expected[change] = 'different'
    with pytest.raises(ValueError, match='changed'):
        resume_report(saved, expected, tags)


def test_resume_archives_interference_without_hiding_quality_failures():
    from allama.benchmark import resume_report
    saved = {'settings':{}, 'tasks_sha256':'h','planned':1,'url':'old',
             'models':{'m':{'digest':'d'}},'results':[
                 {'model':'m','task':'a','repeat':1,'isolation_ok':False,'passed':True}]}
    expected = {'settings':{},'tasks_sha256':'h','planned':1,'url':'new','planned_models':['m']}
    result = resume_report(saved, expected, {'m':{'digest':'d'}})
    assert result['results'] == []
    assert result['superseded_interference_attempts'][0]['passed'] is True


@pytest.mark.parametrize('parameters,modelfile,expected', [
    ('draft_num_predict 4','FROM model',True),
    ('draft_num_predict 0','DRAFT model',False),
    ('','DRAFT model',True),
    ('temperature 1','FROM model',False),
])
def test_embedded_and_external_speculative_configuration(parameters, modelfile, expected):
    from allama.benchmark import speculative_configured
    assert speculative_configured({'parameters':parameters,'modelfile':modelfile}) is expected
