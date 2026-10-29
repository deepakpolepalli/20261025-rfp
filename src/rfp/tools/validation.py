"""Deterministic normalization; quotation matching verifies provenance, not merit."""
from collections import Counter
from decimal import Decimal, InvalidOperation
import json
import re


class InvalidModelJSON(ValueError):
    pass


def normalized_text(text):
    return re.sub(r'\s+',' ',text).strip()


def normalize(raw, criteria, pages, supplier_name):
    try:
        data=json.loads(raw)
    except (ValueError,TypeError):
        raise InvalidModelJSON('Model returned invalid JSON.') from None
    if not isinstance(data,dict) or not isinstance(data.get('criteria'),list) or any(not isinstance(x,dict) for x in data['criteria']):
        raise InvalidModelJSON('Model response must contain an object with a criteria list of objects.')
    warnings=[]
    ids={c['criterion_id'] for c in criteria}
    rows={}
    counts=Counter()
    for item in data['criteria']:
        cid=item.get('criterion_id')
        if type(cid) is not int or cid not in ids:
            warnings.append('Unknown or invalid criterion ID dropped.')
            continue
        counts[cid]+=1
        rows[cid]=item
    if data.get('supplier_name')!=supplier_name:
        warnings.append('Model supplier name differs; uploaded metadata retained.')
    result=[]
    for c in criteria:
        cid=c['criterion_id']; maximum=Decimal(c['max_score'])
        row=rows.get(cid,{})
        reasons=[]
        raw_score=row.get('score')
        score=Decimal(0)
        if counts[cid]!=1:
            reasons.append('Missing criterion normalized to zero.' if counts[cid]==0 else 'Duplicate criterion normalized to zero.')
        else:
            try:
                if isinstance(raw_score,bool):
                    raise InvalidOperation
                score=Decimal(str(raw_score))
                if not score.is_finite():
                    raise InvalidOperation
                if isinstance(raw_score,str):
                    reasons.append('Numeric-string score converted to Decimal.')
                clipped=min(maximum,max(Decimal(0),score))
                if clipped!=score:
                    reasons.append('Out-of-range score clipped to permitted range.')
                score=clipped
            except (InvalidOperation,TypeError,ValueError):
                score=Decimal(0);reasons.append('Invalid score normalized to zero.')
        if str(row.get('max_score')) not in (str(maximum),str(float(maximum))):
            reasons.append('Model maximum differs or is missing; database maximum retained.')
        justification=row.get('justification')
        if not isinstance(justification,str) or not justification.strip():
            justification='No valid model assessment returned.'
            reasons.append('Missing justification normalized.')
        evidence=row.get('evidence')
        if not isinstance(evidence,str):
            evidence='';reasons.append('Invalid evidence normalized to empty text.')
        # Model is asked to return only the verbatim quotation in evidence, page separately.
        quote=normalized_text(evidence)
        matches=[p['page'] for p in pages if quote and quote in normalized_text(p['text'])]
        if score>0 and not matches:
            score=Decimal(0);reasons.append('Positive score lacks verified document quotation; normalized to zero.')
        if counts[cid]!=1:
            score=Decimal(0)
        safe_raw=raw_score if isinstance(raw_score,(str,int,float)) and not isinstance(raw_score,bool) else None
        if isinstance(safe_raw,float) and (safe_raw!=safe_raw or abs(safe_raw)==float('inf')):
            safe_raw=str(safe_raw)
        result.append({'criterion_id':cid,'name':c['name'],'score':str(score),'raw_score':safe_raw,
                       'max_score':str(maximum),'weight':c['weight'],'justification':justification,
                       'evidence':evidence,'evidence_pages':matches,'evidence_verified':bool(matches),
                       'warnings':reasons})
        warnings.extend(f'{c["name"]}: {reason}' for reason in reasons)
    risks=data.get('risks',[])
    if not isinstance(risks,list) or any(not isinstance(x,str) for x in risks):
        risks=[];warnings.append('Malformed risks normalized to empty list.')
    summary=data.get('overall_summary','')
    if not isinstance(summary,str):
        summary='';warnings.append('Malformed summary normalized to empty text.')
    return {'supplier_name':supplier_name,'criteria':result,'risks':risks,'overall_summary':summary,'warnings':warnings}
