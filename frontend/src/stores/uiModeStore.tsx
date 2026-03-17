import { createContext } from 'preact'
import { useContext, useState } from 'preact/hooks'
const ModeCtx=createContext({expert:false,setExpert:(_v:boolean)=>{}})
export function UiModeProvider(props:any){const [expert,setExpert]=useState(false);return <ModeCtx.Provider value={{expert,setExpert}}>{props.children}</ModeCtx.Provider>}
export const useUiMode=()=>useContext(ModeCtx)
