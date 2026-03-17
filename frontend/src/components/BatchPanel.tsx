import { useState } from 'preact/hooks'
import { submitBatch } from '../services/jobs'
export function BatchPanel(){const [urls,setUrls]=useState('');const [result,setResult]=useState<any>(null);return <div class='card'><h3>Batch Submit</h3><textarea rows={4} placeholder='One URL per line' value={urls} onInput={(e:any)=>setUrls(e.currentTarget.value)}/><div><button onClick={async()=>setResult(await submitBatch(urls.split('\n').map((u)=>u.trim()).filter(Boolean)))}>Submit batch</button></div>{result?.items?.map((i:any)=><div>{i.url} =&gt; {i.jobId}</div>)}</div>}
