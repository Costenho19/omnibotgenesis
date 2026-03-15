import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import CommercialLanding from './pages/CommercialLanding'
import InstitutionalPage from './pages/InstitutionalPage'
import CreditGovernanceDemo from './pages/CreditGovernanceDemo'
import InsuranceGovernanceDemo from './pages/InsuranceGovernanceDemo'
import EnergyGovernanceDemo from './pages/EnergyGovernanceDemo'
import BiotechGovernanceDemo from './pages/BiotechGovernanceDemo'
import PublicGovernanceSandbox from './pages/PublicGovernanceSandbox'
import './index.css'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<CommercialLanding />} />
        <Route path="/institutional" element={<InstitutionalPage />} />
        <Route path="/governance-demo" element={<CreditGovernanceDemo />} />
        <Route path="/governance-demo-insurance" element={<InsuranceGovernanceDemo />} />
        <Route path="/governance-demo-energy" element={<EnergyGovernanceDemo />} />
        <Route path="/governance-demo-biotech" element={<BiotechGovernanceDemo />} />
        <Route path="/try" element={<PublicGovernanceSandbox />} />
        <Route path="/terminal" element={<Navigate to="/" replace />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
