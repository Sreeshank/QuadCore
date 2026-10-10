import { useAnimatedNumber } from '../hooks/useMotion';
import { useEffect,useRef,type ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, CircleCheck, FileText, X, AlertCircle, LoaderCircle } from 'lucide-react';
import { title } from '../utils/format';
import { errorText } from '../services/api';
export function Logo({compact=false}:{compact?:boolean}) { return <span className="logo"><span className="logo-mark"><svg width="24" height="26" viewBox="0 0 24 26" fill="none" aria-hidden="true"><path d="M3 3h18v5h-6v15H9V8H3V3Z" fill="currentColor"/><path d="m16 13 3 3 4-5" stroke="#9DDDC9" strokeWidth="2.5" strokeLinecap="round"/></svg></span>{!compact && <span>TaxReady<span className="logo-ai">AI</span></span>}</span>; }
export function Badge({value}:{value:string}) {const type=['verified','complete','resolved'].includes(value)?'success':['extraction_failed','high','open'].includes(value)?'danger':['needs_verification','needs_review','missing','medium','under_review'].includes(value)?'warning':'neutral'; return <span className={'badge '+type}><span className="badge-dot"/>{title(value)}</span>;}
export function Spinner(){return <LoaderCircle size={18} className="spin"/>;}
export function Loading(){return <div aria-label="Loading" className="loading-grid"><div className="skeleton tall"/><div className="skeleton"/><div className="skeleton"/></div>;}
export function ErrorState({error,retry}:{error:unknown;retry?:()=>void}) {return <div className="empty"><AlertCircle size={30}/><h3>We couldn't load this view</h3><p>{errorText(error)}</p><div className="button-row">{retry && <button className="btn secondary" onClick={retry}>Try again</button>}<Link className="btn" to="/app/profile">Set up profile</Link><Link className="text-link" to="/auth">Sign in again</Link></div></div>;}
export function Empty({title:heading,children,action}:{title:string;children:ReactNode;action?:ReactNode}) {return <div className="empty"><span className="empty-icon"><FileText size={28}/></span><h3>{heading}</h3><p>{children}</p>{action}</div>;}
export function PageHeading({eyebrow,title:heading,description,actions}:{eyebrow:string;title:string;description:string;actions?:ReactNode}) {return <div className="page-heading"><div><div className="eyebrow">{eyebrow}</div><h1>{heading}</h1><p>{description}</p></div>{actions && <div className="button-row">{actions}</div>}</div>;}
export function CardHeading({title:heading,sub,link,to}:{title:string;sub?:string;link?:string;to?:string}) {return <div className="card-heading"><div><h2>{heading}</h2>{sub&&<p>{sub}</p>}</div>{to&&<Link className="text-link" to={to}>{link||'View all'}<ArrowRight size={15}/></Link>}</div>;}
export function Modal({title:heading,children,onClose}:{title:string;children:ReactNode;onClose:()=>void}) {
  const ref=useRef<HTMLDialogElement>(null);
  useEffect(()=>{const dialog=ref.current;dialog?.showModal();return ()=>dialog?.close();},[]);
  return <dialog ref={ref} className="modal" onCancel={onClose} onClick={e=>{if(e.target===ref.current)onClose();}}><div className="modal-head"><h2>{heading}</h2><button className="icon-btn" aria-label="Close dialog" onClick={onClose}><X size={20}/></button></div>{children}</dialog>;
}
export function Confirm({title:heading,children,onConfirm,onClose,busy,label='Confirm'}:{title:string;children:ReactNode;onConfirm:()=>void;onClose:()=>void;busy:boolean;label?:string}) {return <Modal title={heading} onClose={onClose}><p className="muted">{children}</p><div className="modal-actions"><button className="btn secondary" onClick={onClose}>Cancel</button><button className="btn danger-btn" disabled={busy} onClick={onConfirm}>{busy?<Spinner/>:null}{label}</button></div></Modal>;}
export function Ring({score,size=164}:{score:number;size?:number}) {const r=64;const animated=useAnimatedNumber(score);return <div className="readiness-ring" style={{width:size,height:size}}><svg viewBox="0 0 160 160" aria-hidden="true"><circle cx="80" cy="80" r={r} fill="none" stroke="var(--line)" strokeWidth="11"/><circle cx="80" cy="80" r={r} fill="none" stroke="#2563eb" strokeWidth="11" strokeLinecap="round" strokeDasharray={2*Math.PI*r} strokeDashoffset={2*Math.PI*r*(1-animated/100)} transform="rotate(-90 80 80)"/></svg><div><strong aria-label={score+' percent'}>{Math.round(animated)}<small>%</small></strong><span>PREPARATION SCORE</span></div></div>;}
export function Notice({children}:{children:ReactNode}) {return <div className="notice"><CircleCheck size={17}/><span>{children}</span></div>;}


export function AnimatedCount({value}:{value:number}){const count=useAnimatedNumber(value);return <strong aria-label={String(value)}>{String(Math.round(count)).padStart(2,'0')}</strong>;}
