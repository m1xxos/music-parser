export type CreateJobPayload={url:string;trim?:{startSeconds?:number;endSeconds?:number};metadata?:{title?:string;artist?:string;album?:string}}
export async function createJob(payload:CreateJobPayload){const r=await fetch('/api/v1/jobs',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});if(!r.ok)throw new Error('create job failed');return r.json()}
export async function getJob(jobId:string){const r=await fetch(`/api/v1/jobs/${jobId}`);if(!r.ok)throw new Error('job status failed');return r.json()}
export async function getResult(jobId:string){const r=await fetch(`/api/v1/jobs/${jobId}/result`);if(!r.ok)throw new Error('result unavailable');return r.json()}
export async function getHistory(){const r=await fetch('/api/v1/history');return r.json()}
export async function createPreset(payload:any){const r=await fetch('/api/v1/presets',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});return r.json()}
export async function submitBatch(urls:string[]){const r=await fetch('/api/v1/batch',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({urls})});return r.json()}
