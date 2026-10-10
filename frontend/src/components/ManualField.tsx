import { useState } from 'react';
import { Plus, FilePenLine } from 'lucide-react';
import { useAction } from '../hooks/useData';
import { api } from '../services/api';
import { Modal,Spinner } from './ui';
import { title } from '../utils/format';
import type { DocumentRecord } from '../types';
const names=['financial_year','assessment_year','employer_name','employee_name','pan','gross_salary','taxable_salary','tds','bank_interest','bank_name','deductions','period_scope','document_date'];
export default function ManualField({document,onClose}:{document:DocumentRecord;onClose:()=>void}){
  const available=names.filter(name=>!document.fields.some(f=>f.field_name===name));
  const [name,setName]=useState(document.missing_fields?.find(f=>available.includes(f))||available[0]||'');
  const [value,setValue]=useState('');const [page,setPage]=useState(1);const [evidence,setEvidence]=useState('');
  const save=useAction(async()=>{await api.post('/documents/'+document.id+'/fields',{field_name:name,value,source_page:page,evidence});onClose();},'Source transcription added. Review and confirm it next.');
  return <Modal title="Add information from the source" onClose={onClose}><div className="info-banner"><FilePenLine size={23}/><span>Enter only information visible in this document. This is labelled as your transcription and stays unverified until you confirm it.</span></div><form className="manual-form" onSubmit={e=>{e.preventDefault();save.mutate();}}><div className="form-grid"><label htmlFor="manual-field">Field<select id="manual-field" value={name} onChange={e=>{setName(e.target.value);setValue('');}}>{available.map(n=><option value={n} key={n}>{title(n)}</option>)}</select></label><label>Source page<input type="number" min="1" max="30" required value={page} onChange={e=>setPage(Number(e.target.value))}/></label></div><label>Value{name==='period_scope'?<select value={value} onChange={e=>setValue(e.target.value)} required><option value="">Select source scope</option><option value="annual">Annual</option><option value="monthly">Monthly</option><option value="quarterly">Quarterly</option></select>:<input required maxLength={500} value={value} onChange={e=>setValue(e.target.value)} placeholder={name.includes('year')?'2025-26':name==='document_date'?'YYYY-MM-DD':'Copy the value from the source'}/>}</label><label>Quote the source evidence<textarea rows={3} required minLength={3} maxLength={600} value={evidence} onChange={e=>setEvidence(e.target.value)} placeholder="Copy the label and supporting text from the selected page."/></label><div className="modal-actions"><button type="button" className="btn secondary" onClick={onClose}>Cancel</button><button className="btn" disabled={save.isPending||!available.length}>{save.isPending?<Spinner/>:<Plus size={16}/>}Add unverified field</button></div></form></Modal>;
}

