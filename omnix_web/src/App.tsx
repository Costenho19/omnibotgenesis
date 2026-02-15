import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import CommercialLanding from './pages/CommercialLanding'
import InstitutionalPage from './pages/InstitutionalPage'
import CreditGovernanceDemo from './pages/CreditGovernanceDemo'
import './index.css'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<CommercialLanding />} />
        <Route path="/institutional" element={<InstitutionalPage />} />
        <Route path="/governance-demo" element={<CreditGovernanceDemo />} />
        <Route path="/terminal" element={<Navigate to="/" replace />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
