export function HistoryPanel(props:{entries:any[]}){return <div class='card'><h3>Recent Jobs</h3>{props.entries.map((e)=><div>{e.jobId.slice(0,8)}... - {e.status} - {e.summary}</div>)}</div>}
