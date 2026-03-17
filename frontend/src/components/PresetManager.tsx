import { createPreset } from '../services/jobs'
import { useState } from 'preact/hooks'
export function PresetManager(){const [name,setName]=useState('');return <div class='card'><h3>Presets</h3><div class='row'><input value={name} onInput={(e:any)=>setName(e.currentTarget.value)} placeholder='Preset name'/><button onClick={async()=>{if(name) await createPreset({name,trim_start_seconds:0,metadata:{}});setName('')}}>Save preset</button></div></div>}
