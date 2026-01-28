import { BrowserRouter, Routes, Route } from 'react-router-dom'
import CommercialLanding from './pages/CommercialLanding'
import InstitutionalPage from './pages/InstitutionalPage'
import './index.css'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<CommercialLanding />} />
        <Route path="/institutional" element={<InstitutionalPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
