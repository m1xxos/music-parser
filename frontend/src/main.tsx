import { render } from 'preact'
import { ParsePage } from './pages/ParsePage'
import { ResultsPage } from './pages/ResultsPage'
import { JobStoreProvider } from './stores/jobStore'
import { UiModeProvider } from './stores/uiModeStore'
import './styles.css'

function App(){return <JobStoreProvider><UiModeProvider><ParsePage/><ResultsPage/></UiModeProvider></JobStoreProvider>}
render(<App />, document.getElementById('app')!)
