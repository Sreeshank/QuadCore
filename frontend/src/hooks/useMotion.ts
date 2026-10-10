import {useEffect,useState} from 'react';
export function useReducedMotion(){
  const [reduced,setReduced]=useState(()=>window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  useEffect(()=>{const query=window.matchMedia('(prefers-reduced-motion: reduce)');const update=()=>setReduced(query.matches);query.addEventListener('change',update);return()=>query.removeEventListener('change',update);},[]);
  return reduced;
}
export function useAnimatedNumber(value:number,duration=850){
  const reduced=useReducedMotion();const [display,setDisplay]=useState(value);
  useEffect(()=>{if(reduced){setDisplay(value);return;}let frame=0;const start=performance.now();setDisplay(0);const tick=(now:number)=>{const progress=Math.min(1,(now-start)/duration);setDisplay(value*(1-Math.pow(1-progress,3)));if(progress<1)frame=requestAnimationFrame(tick);};frame=requestAnimationFrame(tick);return()=>cancelAnimationFrame(frame);},[value,duration,reduced]);
  return reduced?value:display;
}
