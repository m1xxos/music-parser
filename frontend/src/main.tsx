import { render } from 'preact'
import { useMemo, useState } from 'preact/hooks'
import { getJob, getResult, submitBatch } from './services/jobs'
import './styles.css'

type BatchItem = { url: string; jobId: string; status: string; progress?: number; file?: string; download?: string; error?: string }

function App() {
  const [urlsText, setUrlsText] = useState('')
  const [artist, setArtist] = useState('')
  const [album, setAlbum] = useState('')
  const [busy, setBusy] = useState(false)
  const [items, setItems] = useState<BatchItem[]>([])

  const links = useMemo(() => urlsText.split('\n').map((x) => x.trim()).filter(Boolean), [urlsText])

  const submit = async () => {
    if (!links.length || busy) return
    setBusy(true)
    try {
      const response = await submitBatch({
        urls: links,
        metadata: {
          artist: artist || undefined,
          album: album || undefined,
        },
      })
      const batchItems: BatchItem[] = (response.items || []).map((item: any) => ({
        url: item.url,
        jobId: item.jobId,
        status: item.status,
        progress: 0,
      }))
      setItems(batchItems)
      poll(batchItems.map((item) => item.jobId))
    } catch (error: any) {
      setItems([{ url: '-', jobId: '-', status: 'failed', error: error?.message || 'Batch submit failed' }])
    } finally {
      setBusy(false)
    }
  }

  const poll = (jobIds: string[]) => {
    const done = new Set<string>()
    const timer = setInterval(async () => {
      for (const jobId of jobIds) {
        if (done.has(jobId)) continue
        try {
          const job = await getJob(jobId)
          if (job.status === 'completed') {
            const result = await getResult(jobId)
            setItems((prev) => prev.map((item) => item.jobId === jobId ? {
              ...item,
              status: 'completed',
              progress: 100,
              file: result.output?.filename,
              download: result.output?.downloadUrl,
            } : item))
            done.add(jobId)
          } else if (job.status === 'failed') {
            setItems((prev) => prev.map((item) => item.jobId === jobId ? {
              ...item,
              status: 'failed',
              error: job.error?.message || 'Job failed',
              progress: job.progressPercent || 0,
            } : item))
            done.add(jobId)
          } else {
            setItems((prev) => prev.map((item) => item.jobId === jobId ? {
              ...item,
              status: job.status,
              progress: job.progressPercent || 0,
            } : item))
          }
        } catch {
          setItems((prev) => prev.map((item) => item.jobId === jobId ? { ...item, status: 'failed', error: 'Status check failed' } : item))
          done.add(jobId)
        }
      }
      if (done.size === jobIds.length) clearInterval(timer)
    }, 1500)
  }

  return (
    <main class="app">
      <section class="card">
        <h1>Music Parser</h1>
        <p>Minimal batch downloader for YouTube, SoundCloud, and RuTube. Files are tagged for Navidrome and copied to Omnivore import folder.</p>
        <label>Links (one per line)</label>
        <textarea rows={8} value={urlsText} onInput={(e: any) => setUrlsText(e.currentTarget.value)} placeholder="https://youtube.com/...&#10;https://soundcloud.com/..."/>
        <div class="row">
          <input value={artist} onInput={(e: any) => setArtist(e.currentTarget.value)} placeholder="Default artist (optional)"/>
          <input value={album} onInput={(e: any) => setAlbum(e.currentTarget.value)} placeholder="Default album (optional)"/>
          <button disabled={busy || !links.length} onClick={submit}>{busy ? 'Submitting...' : `Download ${links.length || ''}`.trim()}</button>
        </div>
      </section>
      <section class="card">
        <h2>Jobs</h2>
        {!items.length && <small>No jobs yet.</small>}
        {items.map((item) => (
          <article class="job" key={item.jobId}>
            <div class="job-row">
              <strong>{item.url}</strong>
              <span>{item.status}</span>
            </div>
            <div class="progress"><div style={`width:${item.progress || 0}%`} /></div>
            <small>{item.error || item.file || item.jobId}</small>
            {item.download && <a href={item.download} target="_blank" rel="noopener noreferrer">Download</a>}
          </article>
        ))}
      </section>
    </main>
  )
}

render(<App />, document.getElementById('app')!)
