from copy import deepcopy
from decimal import Decimal as D, localcontext, ROUND_HALF_EVEN
from rfp.contracts import canonical


def absolute_scores(suppliers):
    output=deepcopy(suppliers)
    with localcontext() as ctx:
        ctx.prec=28;ctx.rounding=ROUND_HALF_EVEN
        for s in output:
            total=D(0)
            for c in sorted(s['criteria'],key=lambda x:x['criterion_id']):
                contribution=D(c['score'])/D(c['max_score'])*D(c['weight'])
                c['weighted_score']=str(contribution);total+=contribution
            s['absolute_score']=str(total)
    return output


def peer_metrics(suppliers):
    output=deepcopy(suppliers)
    benchmarks={c['criterion_id']:max(D(x['score']) for s in output for x in s['criteria'] if x['criterion_id']==c['criterion_id']) for c in output[0]['criteria']}
    with localcontext() as ctx:
        ctx.prec=28;ctx.rounding=ROUND_HALF_EVEN
        for s in output:
            ppi=D(0)
            for c in sorted(s['criteria'],key=lambda x:x['criterion_id']):
                b=benchmarks[c['criterion_id']]
                relative=D(c['score'])/b*100 if b else D(0)
                c.update(benchmark=str(b),gap=str(D(c['score'])-b),relative_percentage=str(relative))
                if not b:
                    c['warnings'].append('All suppliers scored zero; peer relative performance is 0%.')
                    s['warnings'].append(f'{c["name"]}: zero peer benchmark.')
                ppi+=D(c['weight'])*relative
            s['ppi']=str(ppi/100)
    return output


def industry_metrics(suppliers, baseline):
    output=deepcopy(suppliers)
    with localcontext() as ctx:
        ctx.prec=28;ctx.rounding=ROUND_HALF_EVEN
        for s in output:
            total=D(0);available=True
            for c in sorted(s['criteria'],key=lambda x:x['criterion_id']):
                ref=baseline['targets'].get(str(c['criterion_id']),{})
                target=ref.get('score')
                ok=target is not None and D(target)>0 and D(ref['max_score'])==D(c['max_score'])
                c['industry_target']=target
                c['industry_gap']=str(D(c['score'])-D(target)) if ok else None
                c['industry_relative_percentage']=str(D(c['score'])/D(target)*100) if ok else None
                if ok:
                    total+=D(c['weight'])*D(c['industry_relative_percentage'])
                elif D(c['weight'])>0:
                    available=False
            s['industry_index']=str(total/100) if available else None
            s['industry_source']=baseline['label']
    return output


def rank_suppliers(suppliers):
    output=deepcopy(suppliers)
    output.sort(key=lambda s:(-D(s['ppi']),s['submission_date'],-D(s['experience_rating']),canonical(s['supplier_name'])))
    for i,s in enumerate(output,1):
        s['final_rank']=i
        s['sort_key']={'ppi_desc':s['ppi'],'submission_date_asc':s['submission_date'],
                       'experience_desc':s['experience_rating'],'supplier_name_asc':canonical(s['supplier_name'])}
        s['ranking_explanation']='Sorted by full-precision PPI (descending), submission date (earlier), historical experience (higher), then normalized supplier name (ascending). Absolute and industry scores do not determine rank.'
    return output


def score_and_rank(suppliers,baseline):
    return rank_suppliers(industry_metrics(peer_metrics(absolute_scores(suppliers)),baseline))
