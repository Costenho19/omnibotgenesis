import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ErrorBoundary } from './components/ErrorBoundary'
import ClientReportDownload from './pages/ClientReportDownload'
import CommercialLanding from './pages/CommercialLanding'
import PitchDeck from './pages/PitchDeck'
import InstitutionalPage from './pages/InstitutionalPage'
import CreditGovernanceDemo from './pages/CreditGovernanceDemo'
import InsuranceGovernanceDemo from './pages/InsuranceGovernanceDemo'
import EnergyGovernanceDemo from './pages/EnergyGovernanceDemo'
import BiotechGovernanceDemo from './pages/BiotechGovernanceDemo'
import PublicGovernanceSandbox from './pages/PublicGovernanceSandbox'
import PublicDecisionVerify from './pages/PublicDecisionVerify'
import CreditLiveDashboard from './pages/CreditLiveDashboard'
import InsuranceDashboard from './pages/InsuranceDashboard'
import RoboticsDashboard from './pages/RoboticsDashboard'
import MedicalGovernanceDemo from './pages/MedicalGovernanceDemo'
import MedicalDashboard from './pages/MedicalDashboard'
import AgentsGovernanceDemo from './pages/AgentsGovernanceDemo'
import AgentsDashboard from './pages/AgentsDashboard'
import RealEstateGovernanceDemo from './pages/RealEstateGovernanceDemo'
import RoboticsGovernanceDemo from './pages/RoboticsGovernanceDemo'
import IslamicCreditGovernanceDemo from './pages/IslamicCreditGovernanceDemo'
import RealEstateDashboard from './pages/RealEstateDashboard'
import EnergyDashboard from './pages/EnergyDashboard'
import StablecoinDashboard from './pages/StablecoinDashboard'
import StablecoinGovernanceDemo from './pages/StablecoinGovernanceDemo'
import DefenseGovernanceDemo from './pages/DefenseGovernanceDemo'
import InvestorCommandCenter from './pages/InvestorCommandCenter'
import AuditDashboard from './pages/AuditDashboard'
import ClientDashboard from './pages/ClientDashboard'
import InvestorDemo from './pages/InvestorDemo'
import TechnicalStack from './pages/TechnicalStack'
import IntegrationGuide from './pages/IntegrationGuide'
import TermsOfService from './pages/TermsOfService'
import PrivacyPolicy from './pages/PrivacyPolicy'
import ProofLayer from './pages/ProofLayer'
import IndependentVerification from './pages/IndependentVerification'
import GettingStarted from './pages/GettingStarted'
import ARFCompliance from './pages/ARFCompliance'
import FullDemo from './pages/FullDemo'
import BookLanding from './pages/BookLanding'
import BookLeadsDashboard from './pages/BookLeadsDashboard'
import OscillationDashboard from './pages/OscillationDashboard'
import AnomalyDashboard from './pages/AnomalyDashboard'
import ExecutionDashboard from './pages/ExecutionDashboard'
import BreachDashboard from './pages/BreachDashboard'
import RiskDashboard from './pages/RiskDashboard'
import CrisisReplay from './pages/CrisisReplay'
import ArchitecturePage from './pages/ArchitecturePage'
import InstitutionalDemo from './pages/InstitutionalDemo'
import WhyOMNIX from './pages/WhyOMNIX'
import AboutPage from './pages/AboutPage'
import SecurityPage from './pages/SecurityPage'
import PartnersPage from './pages/PartnersPage'
import CustomersPage from './pages/CustomersPage'
import './index.css'

function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<CommercialLanding />} />
          <Route path="/institutional" element={<InstitutionalPage />} />
          <Route path="/command" element={<InvestorCommandCenter />} />
          <Route path="/governance-demo" element={<CreditGovernanceDemo />} />
          <Route path="/governance-demo-insurance" element={<InsuranceGovernanceDemo />} />
          <Route path="/governance-demo-energy" element={<EnergyGovernanceDemo />} />
          <Route path="/governance-demo-biotech" element={<BiotechGovernanceDemo />} />
          <Route path="/credit" element={<CreditLiveDashboard />} />
          <Route path="/insurance" element={<InsuranceDashboard />} />
          <Route path="/robotics" element={<RoboticsDashboard />} />
          <Route path="/governance-demo-medical" element={<MedicalGovernanceDemo />} />
          <Route path="/medical" element={<MedicalDashboard />} />
          <Route path="/governance-demo-agents" element={<AgentsGovernanceDemo />} />
          <Route path="/agents" element={<AgentsDashboard />} />
          <Route path="/governance-demo-real-estate" element={<RealEstateGovernanceDemo />} />
          <Route path="/governance-demo-robotics" element={<RoboticsGovernanceDemo />} />
          <Route path="/governance-demo-islamic-credit" element={<IslamicCreditGovernanceDemo />} />
          <Route path="/real-estate" element={<RealEstateDashboard />} />
          <Route path="/energy" element={<EnergyDashboard />} />
          <Route path="/governance-demo-stablecoin" element={<StablecoinGovernanceDemo />} />
          <Route path="/governance-demo-defense" element={<DefenseGovernanceDemo />} />
          <Route path="/stablecoin" element={<StablecoinDashboard />} />
          <Route path="/try" element={<PublicGovernanceSandbox />} />
          <Route path="/verify" element={<PublicDecisionVerify />} />
          <Route path="/verify/:receiptId" element={<PublicDecisionVerify />} />
          <Route path="/audit" element={<AuditDashboard />} />
          <Route path="/client" element={<ClientDashboard />} />
          <Route path="/demo" element={<InvestorDemo />} />
          <Route path="/pitch" element={<PitchDeck />} />
          <Route path="/stack" element={<TechnicalStack />} />
          <Route path="/integration" element={<IntegrationGuide />} />
          <Route path="/my-report" element={<ClientReportDownload />} />
          <Route path="/proof" element={<ProofLayer />} />
          <Route path="/verify-independently" element={<IndependentVerification />} />
          <Route path="/docs" element={<GettingStarted />} />
          <Route path="/eidas" element={<ARFCompliance />} />
          <Route path="/full-demo" element={<FullDemo />} />
          <Route path="/book" element={<BookLanding />} />
          <Route path="/book-leads" element={<BookLeadsDashboard />} />
          <Route path="/oscillation" element={<OscillationDashboard />} />
          <Route path="/anomaly" element={<AnomalyDashboard />} />
          <Route path="/execution" element={<ExecutionDashboard />} />
          <Route path="/breach" element={<BreachDashboard />} />
          <Route path="/risk" element={<RiskDashboard />} />
          <Route path="/crisis-replay" element={<CrisisReplay />} />
          <Route path="/architecture" element={<ArchitecturePage />} />
          <Route path="/show" element={<InstitutionalDemo />} />
          <Route path="/why-omnix" element={<WhyOMNIX />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="/security" element={<SecurityPage />} />
          <Route path="/partners" element={<PartnersPage />} />
          <Route path="/customers" element={<CustomersPage />} />
          <Route path="/terms" element={<TermsOfService />} />
          <Route path="/privacy" element={<PrivacyPolicy />} />
          <Route path="/terminal" element={<Navigate to="/" replace />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  )
}

export default App
