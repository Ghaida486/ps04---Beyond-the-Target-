"""Report observable assignment progress without assigning a grade or inventing completion."""
import sys
sys.path.insert(0,'lib')
from common import *
from collections import Counter

def main():
    if len(sys.argv)!=2:return 2
    run=Path(sys.argv[1])
    def optional(file,lines=False):
        p=run/file;return (rows(p) if lines else read(p)) if p.exists() else None
    items=optional('eligible.jsonl',True); decisions=optional('decisions.jsonl',True); review=optional('review.json'); approval=optional('approval.json'); links=optional('package/publication_links.json')
    distinct={x.get('underlying_id',x['item_id']):x for x in (items or [])};counts=Counter(x['kind'] for x in distinct.values())
    live_dates=[]
    for p in Path('runs').glob('*/run.json'):
        m=read(p);summary=p.parent/'summary.json'
        if m['mode']=='live' and summary.exists() and read(summary)['status'] in ('awaiting_review','ready_for_production'):live_dates.append(m['as_of_date'])
    sample=optional('student_review/student_responses.json');student_review_done=bool(sample and sample.get('status')=='completed' and sample.get('reviewer') and all(x.get('student_judgment') and x.get('student_reason') for x in sample.get('sample',[])) and len(sample.get('sample',[]))>=6)
    checklist=[
      {'requirement':'12 distinct eligible items','observed':len(distinct) if items is not None else None,'mechanical_minimum_met':len(distinct)>=12,'limitation':'Meaningfulness, provenance and original publication still require editorial judgment.'},
      {'requirement':'six independent producers','observed':len({x['publisher_id'] for x in distinct.values()}) if items is not None else None,'mechanical_minimum_met':len({x['publisher_id'] for x in distinct.values()})>=6,'limitation':'Producer IDs alone do not establish independent corroboration of a claim.'},
      {'requirement':'two of each required input type','observed':dict(counts) if items is not None else None,'mechanical_minimum_met':all(counts[k]>=2 for k in ('feed','youtube','podcast'))},
      {'requirement':'draft and reference checks','observed':review,'mechanical_minimum_met':bool(review and review['passed'])},
      {'requirement':'two successful live days','observed':sorted(set(live_dates)),'mechanical_minimum_met':len(set(live_dates))>=2},
      {'requirement':'student editorial sample review','observed':'completed response form' if student_review_done else 'pending','mechanical_minimum_met':student_review_done},
      {'requirement':'inspected policy revision and affected-stage rerun','observed':'Must be documented from actual student feedback and preserved outputs','mechanical_minimum_met':False},
      {'requirement':'matching student approval','observed':approval,'mechanical_minimum_met':bool(approval and review and review['passed'] and approval.get('decision')=='approve' and approval.get('review_id')==review['review_id'])},
      {'requirement':'three published article/video pairs','observed':links,'mechanical_minimum_met':bool(links and len(links)==3 and all(x.get('substack_url') and x.get('youtube_url') for x in links)),'limitation':'Entered links must also be opened and checked for course-staff access.'},
      {'requirement':'Google Vids/HeyGen video production and separate technical demo','observed':'Needs actual production and accessible demonstration link','mechanical_minimum_met':False}]
    report={'run_id':read(run/'run.json')['run_id'],'checked_at':now(),'not_a_grade':True,'requirements':checklist,'accepted_decisions':sum(d['decision']=='accept' for d in decisions) if decisions is not None else None}
    write(run/'requirements_audit.json',report);emit(report);return 0
invoke(main)
