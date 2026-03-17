import { createContext } from 'preact'
import { useContext, useState } from 'preact/hooks'
const Ctx=createContext<{jobs:Record<string,any>;update:(id:string,data:any)=>void}>({jobs:{},update:()=>{}})
export function JobStoreProvider(props:any){const [jobs,setJobs]=useState<Record<string,any>>({});const update=(id:string,data:any)=>setJobs((p)=>({...p,[id]:{...(p[id]||{}),...data}}));return <Ctx.Provider value={{jobs,update}}>{props.children}</Ctx.Provider>}
export function useJobStore(){return useContext(Ctx)}
