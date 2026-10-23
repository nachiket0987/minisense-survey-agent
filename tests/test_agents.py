import pytest
from pydantic import ValidationError
from minisense.contracts import Plan, Task, Period, Retrieval, Chunk
from minisense.dataset import generate
from minisense.analytics import SurveyStore
from minisense.agents import Orchestrator, demo_plan, DataAgent


class FakeIndex:
    def retrieve(self, query, **kwargs):
        return Retrieval(query=query,chunks=[Chunk(id='faq-02',source='faq.txt',content='Q: What is your average wait time?\nA: We target under 10 minutes. Peak hours may see 15–20 minute waits.')])


def test_dynamic_routes():
    store=SurveyStore(generate(200))
    app=Orchestrator(store,FakeIndex())
    out=app.ask('What are the top three complaints in June 2026?')
    assert 'comparison' not in out.agents_invoked
    assert out.tool_calls[0].name == 'compute_metrics'
    assert out.summary.mode == 'demo'
    assert 'June 2026' in out.summary.answer
    out=app.ask('How did wait-time complaints change from May to June 2026, and what does the FAQ say about wait times?')
    assert out.agents_invoked == ['data','data','rag','comparison','summary']
    assert any(c.name == 'compute_csat' for c in out.tool_calls)
    assert out.results['comparison']['complaints']['wait_time']['count_delta'] is not None


def test_plan_validation():
    with pytest.raises(ValidationError):
        Plan(question='x',tasks=[Task(id='s',agent='summary',operation='synthesize',depends_on=['missing'])])
    with pytest.raises(ValidationError):
        Task(id='d',agent='data',operation='retrieve')
    with pytest.raises(ValueError): demo_plan('Predict sales next year',SurveyStore(generate(10)).latest)


def test_empty_business_and_no_context():
    class EmptyIndex:
        def retrieve(self,query,**kwargs): return Retrieval(query=query,chunks=[],limitation='No relevant context')
    out=Orchestrator(SurveyStore(generate(100)),EmptyIndex()).ask('What is CSAT for business b99 in June 2026?')
    assert 'No survey responses' in out.summary.answer
    assert 'No relevant FAQ' in out.summary.answer


def test_scope_guard():
    class BadProvider:
        def call_tool(self,task,schema): return 'compute_metrics',{'period':task.period.model_dump(mode='json'),'business_id':'b99','theme':None,'top_n':3}
    task=Task(id='d',agent='data',operation='metrics',period=Period(start='2026-05-01',end='2026-05-31'))
    with pytest.raises(ValueError,match='scope'): DataAgent(SurveyStore(generate(10)),BadProvider()).run(task,[])
