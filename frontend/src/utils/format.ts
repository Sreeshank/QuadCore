export const title = (value:string)=>value.replace(/_/g,' ').replace(/\b\w/g,c=>c.toUpperCase());
export function money(value:string|number) {
  const [whole, fraction=''] = (typeof value==='number'?value.toFixed(2):value).split('.');
  return '₹' + new Intl.NumberFormat('en-IN').format(BigInt(whole||'0')) + '.' + fraction.padEnd(2,'0').slice(0,2);
}
export function sumAmounts(values:string[]):string {
  const cents=values.reduce((total,value)=>{const [whole,fraction='']=value.split('.');return total+BigInt(whole)*100n+BigInt(fraction.padEnd(2,'0'));},0n);
  return (cents/100n).toString()+'.'+(cents%100n).toString().padStart(2,'0');
}
export const date = (value:string)=>new Date(value.endsWith('Z') || /[+-]\d\d:\d\d$/.test(value)?value:value+'Z').toLocaleDateString('en-IN',{day:'numeric',month:'short',year:'numeric'});
export const categories:Record<string,string> = {form16:'Form 16',form26as:'Form 26AS',ais:'AIS',bank_interest:'Bank interest',salary_slip:'Salary slip',other:'Other / unrecognized',freelance:'Freelance records',business:'Business records',capital_gains:'Capital gains',rental:'Rental records',deductions:'Deduction records',other_income:'Other income'};

