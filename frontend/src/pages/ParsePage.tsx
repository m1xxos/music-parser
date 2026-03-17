import { useState } from 'preact/hooks'
import { createJob, getResult } from '../services/jobs'
import { subscribeJobEvents } from '../services/events'
import { EditPanel } from '../components/EditPanel'
import { ResultCard } from '../components/ResultCard'
import { ProgressTimeline } from '../components/ProgressTimeline'
import { AdvancedDrawer } from '../components/AdvancedDrawer'
import { PresetManager } from '../components/PresetManager'
import { BatchPanel } from '../components/BatchPanel'

export function ParsePage(){const [url,setUrl]=useState('');const [trimStart,setTrimStart]=useState(0);const [trimEnd,setTrimEnd]=useState(0);const [title,setTitle]=useState('');const [artist,setArtist]=useState('');const [album,setAlbum]=useState('');const [jobId,setJobId]=useState('');const [events,setEvents]=useState<any[]>([]);const [progress,setProgress]=useState(0);const [result,setResult]=useState<any>(null);
const submit=async()=>{const created=await createJob({url,trim:{startSeconds:trimStart||undefined,endSeconds:trimEnd||undefined},metadata:{title:title||undefined,artist:artist||undefined,album:album||undefined}});setJobId(created.jobId);const unsub=subscribeJobEvents(created.jobId,async(evt)=>{setEvents((p)=>[...p,evt]);setProgress(evt.progressPercent);if(evt.status==='completed'){setResult(await getResult(created.jobId));unsub()}})};
return <><div class='card'><h2>Guided Parse Flow</h2><p>Paste a YouTube, SoundCloud, or RuTube URL and run parse with optional edits.</p><div class='row'><input style='flex:1' value={url} placeholder='https://...' onInput={(e:any)=>setUrl(e.currentTarget.value)}/><button onClick={submit}>Start Parse</button></div><div class='progress'><div style={`width:${progress}%`} /></div>{jobId&&<small>Job: {jobId}</small>}</div><EditPanel {...{trimStart,setTrimStart,trimEnd,setTrimEnd,title,setTitle,artist,setArtist,album,setAlbum}}/><ProgressTimeline events={events}/><ResultCard result={result}/><AdvancedDrawer><PresetManager/><BatchPanel/></AdvancedDrawer></>}
