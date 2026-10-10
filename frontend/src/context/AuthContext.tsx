import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { createClient } from '@supabase/supabase-js';
import { useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';

export const supabase = import.meta.env.VITE_SUPABASE_URL && import.meta.env.VITE_SUPABASE_ANON_KEY ? createClient(import.meta.env.VITE_SUPABASE_URL, import.meta.env.VITE_SUPABASE_ANON_KEY) : null;
const AuthContext = createContext<{token:string|null;demo:boolean;loginDemo:(scenario:string)=>Promise<void>;logout:()=>Promise<void>}>({token:null,demo:false,loginDemo:async()=>{},logout:async()=>{}});
export function AuthProvider({children}:{children:ReactNode}) {
  const [token,setToken] = useState<string|null>(sessionStorage.getItem('taxready_token'));
  const query = useQueryClient();
  function applyToken(value:string|null) {
    if(value) sessionStorage.setItem('taxready_token',value); else sessionStorage.removeItem('taxready_token');
    setToken(value); query.clear();
  }
  useEffect(()=>{
    if(!supabase) return;
    const { data } = supabase.auth.onAuthStateChange((_event,session)=>{
      if(session) applyToken(session.access_token);
      else if(!sessionStorage.getItem('taxready_token')?.startsWith('demo_')) applyToken(null);
    });
    return ()=>data.subscription.unsubscribe();
  },[]);
  async function loginDemo(scenario:string) {
    const {data} = await api.post('/auth/demo',{scenario});
    sessionStorage.setItem('taxready_scenario',scenario);
    applyToken(data.access_token);
  }
  async function logout() {
    try { await api.post('/auth/logout'); } finally {
      if(supabase && !token?.startsWith('demo_')) await supabase.auth.signOut();
      applyToken(null); sessionStorage.removeItem('taxready_scenario');
    }
  }
  return <AuthContext.Provider value={{token,demo:!!token?.startsWith('demo_'),loginDemo,logout}}>{children}</AuthContext.Provider>;
}
export const useAuth = ()=>useContext(AuthContext);

