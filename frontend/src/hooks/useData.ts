import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api, errorText } from '../services/api';
import { useToast } from '../context/ToastContext';
import type { Summary } from '../types';
export function useData<T>(path:string,enabled=true) {
  return useQuery<T>({ queryKey:[path],queryFn:async()=>(await api.get<T>(path)).data,enabled,retry:false });
}
export const useSummary = ()=>useData<Summary>('/dashboard/summary');
export function useAction<T>(fn:(value:T)=>Promise<unknown>,message?:string) {
  const query = useQueryClient(); const toast=useToast();
  return useMutation({mutationFn:fn,onSuccess:()=>{query.invalidateQueries();if(message)toast(message);},onError:error=>toast(errorText(error),true)});
}

