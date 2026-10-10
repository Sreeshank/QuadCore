import { createContext,useContext,useState,useRef,type ReactNode } from 'react';
import { CheckCircle2, X, AlertCircle } from 'lucide-react';
const ToastContext = createContext<(message:string,error?:boolean)=>void>(()=>{});
export function ToastProvider({children}:{children:ReactNode}) {
  const [toast,setToast] = useState<{message:string;error:boolean}|null>(null);
  const timer=useRef<ReturnType<typeof setTimeout>|undefined>(undefined);
  function notify(message:string,error=false) { clearTimeout(timer.current);setToast({message,error});timer.current=setTimeout(()=>setToast(null),7000); }
  return <ToastContext.Provider value={notify}>{children}{toast && <div className={'toast '+(toast.error?'error':'')} role={toast.error?'alert':'status'}>{toast.error?<AlertCircle size={20}/>:<CheckCircle2 size={20}/>}<span>{toast.message}</span><button aria-label="Dismiss notification" onClick={()=>setToast(null)}><X size={18}/></button></div>}</ToastContext.Provider>;
}
export const useToast = ()=>useContext(ToastContext);

