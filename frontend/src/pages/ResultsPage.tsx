import { useEffect, useState } from 'preact/hooks'
import { getHistory } from '../services/jobs'
import { HistoryPanel } from '../components/HistoryPanel'
export function ResultsPage(){const [entries,setEntries]=useState<any[]>([]);useEffect(()=>{getHistory().then(setEntries)},[]);return <HistoryPanel entries={entries} />}
