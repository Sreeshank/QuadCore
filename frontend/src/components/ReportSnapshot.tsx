import { useData } from '../hooks/useData';
import { Modal,Loading,ErrorState,Badge } from './ui';
import { money,title,date } from '../utils/format';
import type { Summary } from '../types';
export default function ReportSnapshot({id,onClose}:{id:string;onClose:()=>void}){
  const query=useData<{id:string;generated_at:string;summary:Summary}>('/reports/'+id+'/snapshot');
  return <Modal title="Saved report snapshot" onClose={onClose}>{query.isLoading?<Loading/>:!query.data?<ErrorState error={query.error}/>:<div className="snapshot"><p className="muted">Saved {date(query.data.generated_at)} · FY {query.data.summary.profile.financial_year}. This snapshot does not change when current records change.</p><div className="snapshot-score"><strong>{query.data.summary.readiness_score}%</strong><span>Preparation score at generation</span></div>{Object.entries(query.data.summary.components).map(([key,v])=><div className="snapshot-row" key={key}><span>{title(key)}</span><strong>{v.contribution} points</strong></div>)}<h3>Verified supported income</h3>{query.data.summary.income_summary.map(i=><div className="snapshot-row" key={i.label}><span>{i.label}</span><strong>{money(i.amount)}</strong></div>)}<h3>Checklist at generation</h3>{query.data.summary.checklist.filter(i=>i.status!=='not_applicable').map(i=><div className="snapshot-row" key={i.id}><span>{i.title}</span><Badge value={i.status}/></div>)}<h3>Unresolved findings</h3>{query.data.summary.issues.filter(i=>i.status!=='resolved').map(i=><p className="small-text muted" key={i.id}>{i.details.title}{i.details.difference?' · '+money(i.details.difference):''}</p>)}{!query.data.summary.issues.some(i=>i.status!=='resolved')&&<p className="small-text muted">No unresolved findings in this snapshot.</p>}</div>}</Modal>;
}

