"""Prepare concrete student review material from actual AI decisions; never approve."""
import sys
sys.path.insert(0,'lib')
from common import *
import shutil

def main():
    if len(sys.argv)!=2: return 2
    run=Path(sys.argv[1]); decisions=rows(run/'decisions.jsonl'); items={(x['item_id'],x['version_id']):x for x in rows(run/'eligible.jsonl')}
    def sample(pool):
        chosen=[];producers=set();kinds=set();remaining=list(pool)
        while remaining and len(chosen)<3:
            def priority(decision):
                item=items[(decision['item_id'],decision['version_id'])]
                return 2*(item['kind'] not in kinds)+(item['publisher_id'] not in producers)
            decision=max(remaining,key=priority);remaining.remove(decision);chosen.append(decision)
            item=items[(decision['item_id'],decision['version_id'])];producers.add(item['publisher_id']);kinds.add(item['kind'])
        return chosen
    accepted=sample([d for d in decisions if d['decision']=='accept'])
    other=sample([d for d in decisions if d['decision'] in ('reject','defer')])
    folder=run/'student_review';folder.mkdir(exist_ok=True)
    existing=folder/'student_responses.json'
    if existing.exists():
        prior=read(existing)
        if prior.get('reviewer') or any(x.get('student_judgment') or x.get('student_reason') or x.get('factual_corrections') for x in prior.get('sample',[])):
            emit({'worksheet':str(folder/'worksheet.md'),'response_file':str(existing),'existing_student_work_preserved':True,'human_approval_created':False});return 0
    if not (folder/'policy-before-review.md').exists(): shutil.copyfile(run/'config/editorial_policy.md',folder/'policy-before-review.md')
    review=[]; lines=['# Student editorial review — Beyond the Target','This worksheet contains actual AI decisions. The student must supply her own judgments. Blank responses are pending, not approval.']
    if len(accepted)<3 or len(other)<3: lines.append('**Incomplete sample:** three accepted and three rejected/deferred decisions are required. Do not manufacture rejections to fill the sample.')
    for d in accepted+other:
        item=items[(d['item_id'],d['version_id'])]
        lines.append(f'## {item["title"]}\n\n- Decision: **{d["decision"]}**\n- Original source: [{item["publisher_id"]}]({item["url"]})\n- Published: {item["published_at"]}\n- Source version: `{item["version_id"]}`\n- Retained text: `{item["text_path"]}`\n- AI reason: {d["reason"]}\n\n**Your assessment:** Do you agree, disagree, or want to defer? Explain what the evidence supports, what it does not, and any missing perspective.\n\n_To be completed by the student._')
        review.append({'ai_decision':d,'title':item['title'],'url':item['url'],'student_judgment':None,'student_reason':None,'factual_corrections':[]})
    lines.append('## Policy revision\n\nAfter reviewing the sample, state one concrete rule you want changed, why, and what difference you expect. Preserve the policy before/after and rerun the affected stages.\n\n_To be completed by the student._')
    (folder/'worksheet.md').write_text('\n\n'.join(lines)+'\n')
    template=folder/'student_responses.json'
    write(template,{'status':'awaiting_student','reviewer':None,'reviewed_at':None,'sample':review,'policy_revision_requested':None})
    emit({'worksheet':str(folder/'worksheet.md'),'response_file':str(template),'accepted_sample':len(accepted),'rejected_or_deferred_sample':len(other),'human_approval_created':False});return 0
invoke(main)
