import axios from 'axios';
export const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || '/api/v1', timeout: 180000 });
api.interceptors.request.use(config => {
  const token = sessionStorage.getItem('taxready_token');
  if (token) config.headers.Authorization = 'Bearer ' + token;
  return config;
});
export function errorText(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) return detail.map((d: {msg:string}) => d.msg).join('. ');
    if (!error.response) return 'Could not reach TaxReady AI. Check that the backend is running.';
  }
  return error instanceof Error ? error.message : 'Something went wrong. Please try again.';
}
export async function download(path:string, filename:string) {
  const {data} = await api.get(path,{responseType:'blob'});
  const url = URL.createObjectURL(data);
  const link = document.createElement('a'); link.href=url; link.download=filename; link.click();
  setTimeout(()=>URL.revokeObjectURL(url),10000);
}

