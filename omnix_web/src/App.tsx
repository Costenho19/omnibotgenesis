import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import ClientReportDownload from './pages/ClientReportDownload'
import CommercialLanding from './pages/CommercialLanding'
import InstitutionalPage from './pages/InstitutionalPage'
import CreditGovernanceDemo from './pages/CreditGovernanceDemo'
import InsuranceGovernanceDemo from './pages/InsuranceGovernanceDemo'
import EnergyGovernanceDemo from './pages/EnergyGovernanceDemo'
import BiotechGovernanceDemo from './pages/BiotechGovernanceDemo'
import PublicGovernanceSandbox from './pages/PublicGovernanceSandbox'
import PublicDecisionVerify from './pages/PublicDecisionVerify'
import InvestorDemo from './pages/InvestorDemo'
import TermsOfService from './pages/TermsOfService'
import PrivacyPolicy from './pages/PrivacyPolicy'
import './index.css'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<CommercialLanding />} />
        <Route path="/institutional" element={<InstitutionalPage />} />
        <Route path="/demo" element={<InvestorDemo />} />
        <Route path="/governance-demo" element={<CreditGovernanceDemo />} />
        <Route path="/governance-demo-insurance" element={<InsuranceGovernanceDemo />} />
        <Route path="/governance-demo-energy" element={<EnergyGovernanceDemo />} />
        <Route path="/governance-demo-biotech" element={<BiotechGovernanceDemo />} />
        <Route path="/try" element={<PublicGovernanceSandbox />} />
        <Route path="/verify" element={<PublicDecisionVerify />} />
        <Route path="/verify/:receiptId" element={<PublicDecisionVerify />} />
        <Route path="/my-report" element={<ClientReportDownload />} />
        <Route path="/terms" element={<TermsOfService />} />
        <Route path="/privacy" element={<PrivacyPolicy />} />
        <Route path="/terminal" element={<Navigate to="/" replace />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
