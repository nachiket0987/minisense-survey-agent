"""Specialists and a dependency-driven orchestrator with auditable tool calls."""
import calendar
import re
from datetime import date
from pydantic import Field
from .contracts import (Contract, Period, Task, Plan, Metrics, Comparison, Retrieval,
                        ToolCall, Summary, Answer, THEMES)
from .analytics import compare, compute_csat


def month_period(year: int, month: int):
    return Period(start=date(year,month,1),end=date(year,month,calendar.monthrange(year,month)[1]))


def demo_plan(question: str, latest: date) -> Plan:
    """Explicit limited grammar for offline demonstrations, not a model substitute."""
    q=question.lower().replace('wait-time','wait time')
    if not q.strip() or len(q)>2000:
        raise ValueError('Question must contain 1–2000 characters')
    if not any(w in q for w in ('complaint','satisfaction','csat','rating','response','faq','wait time','menu','policy')):
        raise ValueError('Unsupported demo question; use LLM mode for broader planning')
    year_match=re.search(r'\b(20\d{2})\b',q)
    year=int(year_match[1]) if year_match else latest.year
    month_names={name.lower():i for i,name in enumerate(calendar.month_name) if name}
    months=[month_names[m] for m in re.findall(r'\b('+'|'.join(month_names)+r')\b',q)]
    months=list(dict.fromkeys(months))
    comparison=any(w in q for w in ('change','compare','comparison','versus',' vs ','last month')) and 'target' not in q
    if len(months)>2:
        raise ValueError('Demo supports at most two months')
    if not months:
        months=[latest.month]
    if comparison and len(months)==1:
        current=months[0]
        if current==1:
            raise ValueError('Cross-year comparisons require LLM mode')
        months=[current-1,current]
    if len(months)==2 and not comparison:
        raise ValueError('Two months require an explicit comparison in demo mode')
    if re.search(r'\b\d{1,2}(?:st|nd|rd|th)?\s+(?:'+'|'.join(month_names)+r')\b',q) or re.search(r'\b\d{4}-\d{2}-\d{2}\b',q):
        raise ValueError('Demo supports whole months only; use LLM mode for date ranges')
    theme_aliases={'wait time':'wait_time','food quality':'food_quality','staff':'staff_service','order accuracy':'order_accuracy','cleanliness':'cleanliness','pricing':'value','value':'value'}
    theme=next((v for k,v in theme_aliases.items() if k in q),None)
    top_match=re.search(r'top\s+(\d+)',q)
    top_n=int(top_match[1]) if top_match else 3
    business=re.search(r'\b(b\d+)\b',q)
    business_id=business[1] if business else 'b01'
    tasks=[]
    pure_faq=('faq' in q or 'menu' in q or 'policy' in q) and not any(w in q for w in ('complaint','csat','satisfaction','rating','response','change'))
    if not pure_faq:
        for i,month in enumerate(sorted(months)):
            tasks.append(Task(id=f'data_{i}',agent='data',operation='metrics',period=month_period(year,month),theme=theme,top_n=top_n,business_id=business_id))
    if comparison and not pure_faq:
        tasks.append(Task(id='comparison',agent='comparison',operation='compare',depends_on=['data_0','data_1']))
    query='company CSAT target satisfaction score root cause review' if any(w in q for w in ('csat','satisfaction','target')) else ('expected wait times peak off peak hours' if theme=='wait_time' else ('customer complaint escalation refunds quality issues' if 'complaint' in q else question))
    tasks.append(Task(id='rag',agent='rag',operation='retrieve',query=query))
    tasks.append(Task(id='summary',agent='summary',operation='synthesize',depends_on=[t.id for t in tasks]))
    return Plan(question=question,tasks=tasks)


class MetricsArguments(Contract):
    period: Period
    business_id: str
    theme: str | None = None
    top_n: int = Field(default=3,ge=1,le=7)


class DataAgent:
    def __init__(self,store,provider=None):
        self.store,self.provider=store,provider

    def run(self,task: Task,trace: list[ToolCall]) -> Metrics:
        expected=MetricsArguments(period=task.period,business_id=task.business_id,theme=task.theme,top_n=task.top_n)
        if self.provider:
            name,arguments=self.provider.call_tool(task,MetricsArguments.model_json_schema())
        else:
            name,arguments='compute_metrics',expected.model_dump(mode='json')
        if name != 'compute_metrics':
            raise ValueError('Tool is not allowlisted')
        args=MetricsArguments.model_validate(arguments)
        if args != expected:
            raise ValueError('Tool arguments changed the validated task scope')
        result=self.store.metrics(**args.model_dump()) if False else self.store.metrics(args.period,args.business_id,args.theme,args.top_n)
        trace.append(ToolCall(agent='data',name=name,arguments=args.model_dump(mode='json'),result=result.model_dump(mode='json')))
        trace.append(ToolCall(agent='data',name='compute_csat',arguments={'rating_count':result.count,'period':args.period.model_dump(mode='json'),'business_id':args.business_id},result={'mean':result.mean_rating,'satisfied_pct':result.satisfied_pct}))
        return result


class ComparisonAgent:
    def run(self,task,results):
        return compare(*(Metrics.model_validate(results[d]) for d in task.depends_on))


class RAGAgent:
    def __init__(self,index): self.index=index
    def run(self,task): return self.index.retrieve(task.query)


def evidence_statements(results):
    facts=[]
    for key,value in results.items():
        if 'mean_rating' in value:
            m=Metrics.model_validate(value)
            label=m.period.start.strftime('%B %Y')
            if not m.count:
                facts.append(f'No survey responses matched {m.business_id} in {label}.')
                continue
            facts.append(f'In {label}, {m.business_id} had {m.count:,} responses, a mean satisfaction rating of {m.mean_rating:.2f}/5, and {m.satisfied_pct:.2f}% rating four or five.')
            if m.top_complaints:
                ranked=', '.join(f'{t.replace("_"," ")} ({n:,}; {m.complaint_rates[t]:.2f}% of responses)' for t,n in m.top_complaints)
                facts.append(f'The leading complaint themes were {ranked} [survey:{key}].')
        elif 'count_delta' in value:
            c=Comparison.model_validate(value)
            for theme,change in c.complaints.items():
                rel='undefined from a zero baseline' if change['change_pct'] is None else f'{change["change_pct"]:+.2f}%'
                rate='undefined for an empty period' if change['rate_delta_pp'] is None else f'{change["rate_delta_pp"]:+.2f} percentage points'
                facts.append(f'From {c.earlier.start:%B %Y} to {c.later.start:%B %Y}, {theme.replace("_"," ")} complaints changed by {change["count_delta"]:+,} ({rel}); prevalence changed by {rate} [comparison:{key}].')
            facts.extend(c.warnings)
        elif 'chunks' in value:
            r=Retrieval.model_validate(value)
            if not r.chunks:
                facts.append('No relevant FAQ evidence was retrieved; policy context is unavailable.')
            else:
                for chunk in r.chunks:
                    # Extractive policy statements prevent invention and keep source qualifiers.
                    text=chunk.content.split('\nA:',1)[-1].strip()
                    facts.append(f'FAQ [{chunk.source}#{chunk.id}]: {text}')
    return facts


class SummaryAgent:
    def __init__(self,provider=None): self.provider=provider

    def run(self,task,results,question):
        facts=evidence_statements(results)
        recommendations=[]
        metrics=[Metrics.model_validate(v) for v in results.values() if 'mean_rating' in v]
        chunks=[c for v in results.values() if 'chunks' in v for c in Retrieval.model_validate(v).chunks]
        csat_policy=any('Q: What is your CSAT target?' in c.content for c in chunks)
        if metrics and csat_policy:
            current=max(metrics,key=lambda m:m.period.end)
            if current.mean_rating is not None:
                gap=current.mean_rating-4.5
                facts.append(f'The latest mean is {abs(gap):.2f} points {"below" if gap<0 else "above"} the FAQ target of 4.50/5.')
                recommendations.append('Recommendation: initiate the documented operations root-cause review because the mean is below 4.0.' if current.mean_rating<4 else ('Recommendation: investigate recurring complaints to work toward the 4.5 target; the below-4.0 review trigger is not met.' if current.mean_rating<4.5 else 'Recommendation: monitor recurring themes while maintaining the current satisfaction target.'))
        if metrics and not recommendations:
            recommendations.append('Recommendation: investigate the leading reported themes and validate causes operationally before changing staffing or pricing.')
        if self.provider:
            selection=self.provider.select_evidence({'question':question,'structured_results':results,'evidence':facts,'allowed_recommendations':recommendations})
            if sorted(selection.evidence_order) != list(range(len(facts))):
                raise ValueError('Summary must preserve every evidence statement exactly once')
            if selection.recommendation is not None and selection.recommendation not in recommendations:
                raise ValueError('Summary recommendation lacks supporting evidence')
            facts=[facts[i] for i in selection.evidence_order]
            recommendation=selection.recommendation
        else:
            recommendation=recommendations[0] if recommendations else None
        return Summary(answer=' '.join(facts+([recommendation] if recommendation else [])),evidence=facts,recommendation=recommendation,mode='llm' if self.provider else 'demo')


class Orchestrator:
    def __init__(self,store,index,provider=None):
        self.store,self.provider=store,provider
        self.data=DataAgent(store,provider)
        self.comparison=ComparisonAgent()
        self.rag=RAGAgent(index)
        self.summary=SummaryAgent(provider)

    def ask(self,question: str) -> Answer:
        plan=self.provider.plan(question,self.store.latest) if self.provider else demo_plan(question,self.store.latest)
        results,trace,invoked={},[],[]
        pending=list(plan.tasks)
        summary=None
        while pending:
            ready=[t for t in pending if set(t.depends_on)<=results.keys()]
            if not ready:
                raise ValueError('Task plan cannot be scheduled')
            for task in ready:
                if task.agent=='data': result=self.data.run(task,trace)
                elif task.agent=='comparison': result=self.comparison.run(task,results)
                elif task.agent=='rag': result=self.rag.run(task)
                else:
                    result=self.summary.run(task,{d:results[d] for d in task.depends_on},question)
                    summary=result
                results[task.id]=result.model_dump(mode='json')
                invoked.append(task.agent)
                pending.remove(task)
        return Answer(plan=plan,agents_invoked=invoked,tool_calls=trace,results={k:v for k,v in results.items() if k!=next(t.id for t in plan.tasks if t.agent=='summary')},summary=summary)
