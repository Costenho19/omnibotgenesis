import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ErrorBoundary } from './components/ErrorBoundary'
import CommercialLanding from './pages/CommercialLanding'
import './index.css'

// ─── Lazy-loaded routes ───────────────────────────────────────────────────────
// All non-homepage routes are lazy-loaded to minimize initial bundle size.
// CommercialLanding is kept eager (above-fold, first paint critical path).

const ProtocolVisualizationPage   = lazy(() => import('./pages/ProtocolVisualizationPage'))
const ClientReportDownload        = lazy(() => import('./pages/ClientReportDownload'))
const PitchDeck                   = lazy(() => import('./pages/PitchDeck'))
const InstitutionalPage           = lazy(() => import('./pages/InstitutionalPage'))
const CreditGovernanceDemo        = lazy(() => import('./pages/CreditGovernanceDemo'))
const InsuranceGovernanceDemo     = lazy(() => import('./pages/InsuranceGovernanceDemo'))
const EnergyGovernanceDemo        = lazy(() => import('./pages/EnergyGovernanceDemo'))
const BiotechGovernanceDemo       = lazy(() => import('./pages/BiotechGovernanceDemo'))
const PublicGovernanceSandbox     = lazy(() => import('./pages/PublicGovernanceSandbox'))
const PublicDecisionVerify        = lazy(() => import('./pages/PublicDecisionVerify'))
const CreditLiveDashboard         = lazy(() => import('./pages/CreditLiveDashboard'))
const InsuranceDashboard          = lazy(() => import('./pages/InsuranceDashboard'))
const RoboticsDashboard           = lazy(() => import('./pages/RoboticsDashboard'))
const MedicalGovernanceDemo       = lazy(() => import('./pages/MedicalGovernanceDemo'))
const MedicalDashboard            = lazy(() => import('./pages/MedicalDashboard'))
const AgentsGovernanceDemo        = lazy(() => import('./pages/AgentsGovernanceDemo'))
const AgentsDashboard             = lazy(() => import('./pages/AgentsDashboard'))
const RealEstateGovernanceDemo    = lazy(() => import('./pages/RealEstateGovernanceDemo'))
const RoboticsGovernanceDemo      = lazy(() => import('./pages/RoboticsGovernanceDemo'))
const IslamicCreditGovernanceDemo = lazy(() => import('./pages/IslamicCreditGovernanceDemo'))
const RealEstateDashboard         = lazy(() => import('./pages/RealEstateDashboard'))
const EnergyDashboard             = lazy(() => import('./pages/EnergyDashboard'))
const StablecoinDashboard         = lazy(() => import('./pages/StablecoinDashboard'))
const StablecoinGovernanceDemo    = lazy(() => import('./pages/StablecoinGovernanceDemo'))
const DefenseGovernanceDemo       = lazy(() => import('./pages/DefenseGovernanceDemo'))
const InvestorCommandCenter       = lazy(() => import('./pages/InvestorCommandCenter'))
const AuditDashboard              = lazy(() => import('./pages/AuditDashboard'))
const ClientDashboard             = lazy(() => import('./pages/ClientDashboard'))
const InvestorDemo                = lazy(() => import('./pages/InvestorDemo'))
const TechnicalStack              = lazy(() => import('./pages/TechnicalStack'))
const IntegrationGuide            = lazy(() => import('./pages/IntegrationGuide'))
const TermsOfService              = lazy(() => import('./pages/TermsOfService'))
const PrivacyPolicy               = lazy(() => import('./pages/PrivacyPolicy'))
const ProofLayer                  = lazy(() => import('./pages/ProofLayer'))
const IndependentVerification     = lazy(() => import('./pages/IndependentVerification'))
const GettingStarted              = lazy(() => import('./pages/GettingStarted'))
const ARFCompliance               = lazy(() => import('./pages/ARFCompliance'))
const FullDemo                    = lazy(() => import('./pages/FullDemo'))
const BookLanding                 = lazy(() => import('./pages/BookLanding'))
const BookLeadsDashboard          = lazy(() => import('./pages/BookLeadsDashboard'))
const OscillationDashboard        = lazy(() => import('./pages/OscillationDashboard'))
const AnomalyDashboard            = lazy(() => import('./pages/AnomalyDashboard'))
const ExecutionDashboard          = lazy(() => import('./pages/ExecutionDashboard'))
const BreachDashboard             = lazy(() => import('./pages/BreachDashboard'))
const RiskDashboard               = lazy(() => import('./pages/RiskDashboard'))
const CrisisReplay                = lazy(() => import('./pages/CrisisReplay'))
const ArchitecturePage            = lazy(() => import('./pages/ArchitecturePage'))
const InstitutionalDemo           = lazy(() => import('./pages/InstitutionalDemo'))
const WhyOMNIX                    = lazy(() => import('./pages/WhyOMNIX'))
const AboutPage                   = lazy(() => import('./pages/AboutPage'))
const SecurityPage                = lazy(() => import('./pages/SecurityPage'))
const PartnersPage                = lazy(() => import('./pages/PartnersPage'))
const CustomersPage               = lazy(() => import('./pages/CustomersPage'))
const AgentTrustFabricPage        = lazy(() => import('./pages/AgentTrustFabricPage'))
const ATFVerifierPage             = lazy(() => import('./pages/ATFVerifierPage'))
const ATFStandardPage             = lazy(() => import('./pages/ATFStandardPage'))
const ATFExplainedPage            = lazy(() => import('./pages/ATFExplainedPage'))
const ArchiveVerifierPage         = lazy(() => import('./pages/ArchiveVerifierPage'))
const TrustInfrastructurePage     = lazy(() => import('./pages/TrustInfrastructurePage'))
const ForensicOperationsDemoPage  = lazy(() => import('./pages/ForensicOperationsDemoPage'))
const GovernanceFlowPage          = lazy(() => import('./pages/GovernanceFlowPage'))
const InstitutionalBriefPage      = lazy(() => import('./pages/InstitutionalBriefPage'))
const VideoTemplate               = lazy(() => import('./components/video/VideoTemplate'))
const ReviewerStartPage           = lazy(() => import('./pages/ReviewerStartPage'))
const GovernanceAPIPage           = lazy(() => import('./pages/GovernanceAPIPage'))
const ProofOfGovernancePage       = lazy(() => import('./pages/ProofOfGovernancePage'))
const SettlementGatePage          = lazy(() => import('./pages/SettlementGatePage'))

// ─── Loading fallback ─────────────────────────────────────────────────────────
function PageLoader() {
  return (
    <div style={{
      minHeight: '100vh',
      background: '#060F1E',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
    }}>
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 16,
      }}>
        <div style={{
          width: 36,
          height: 36,
          borderRadius: '50%',
          border: '3px solid #1a2d45',
          borderTopColor: '#C9A227',
          animation: 'spin 0.8s linear infinite',
        }} />
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        <span style={{
          color: '#64748b',
          fontSize: 12,
          fontFamily: 'monospace',
          letterSpacing: '0.08em',
        }}>OMNIX QUANTUM</span>
      </div>
    </div>
  )
}

// ─── App ──────────────────────────────────────────────────────────────────────
function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Suspense fallback={<PageLoader />}>
          <Routes>
            <Route path="/"                               element={<CommercialLanding />} />
            <Route path="/institutional"                  element={<InstitutionalPage />} />
            <Route path="/command"                        element={<InvestorCommandCenter />} />
            <Route path="/governance-demo"                element={<CreditGovernanceDemo />} />
            <Route path="/governance-demo-insurance"      element={<InsuranceGovernanceDemo />} />
            <Route path="/governance-demo-energy"         element={<EnergyGovernanceDemo />} />
            <Route path="/governance-demo-biotech"        element={<BiotechGovernanceDemo />} />
            <Route path="/credit"                         element={<CreditLiveDashboard />} />
            <Route path="/insurance"                      element={<InsuranceDashboard />} />
            <Route path="/robotics"                       element={<RoboticsDashboard />} />
            <Route path="/governance-demo-medical"        element={<MedicalGovernanceDemo />} />
            <Route path="/medical"                        element={<MedicalDashboard />} />
            <Route path="/governance-demo-agents"         element={<AgentsGovernanceDemo />} />
            <Route path="/agents"                         element={<AgentsDashboard />} />
            <Route path="/governance-demo-real-estate"    element={<RealEstateGovernanceDemo />} />
            <Route path="/governance-demo-robotics"       element={<RoboticsGovernanceDemo />} />
            <Route path="/governance-demo-islamic-credit" element={<IslamicCreditGovernanceDemo />} />
            <Route path="/real-estate"                    element={<RealEstateDashboard />} />
            <Route path="/energy"                         element={<EnergyDashboard />} />
            <Route path="/governance-demo-stablecoin"     element={<StablecoinGovernanceDemo />} />
            <Route path="/governance-demo-defense"        element={<DefenseGovernanceDemo />} />
            <Route path="/stablecoin"                     element={<StablecoinDashboard />} />
            <Route path="/try"                            element={<PublicGovernanceSandbox />} />
            <Route path="/verify"                         element={<PublicDecisionVerify />} />
            <Route path="/verify/:receiptId"              element={<PublicDecisionVerify />} />
            <Route path="/audit"                          element={<AuditDashboard />} />
            <Route path="/client"                         element={<ClientDashboard />} />
            <Route path="/demo"                           element={<InvestorDemo />} />
            <Route path="/pitch"                          element={<PitchDeck />} />
            <Route path="/stack"                          element={<TechnicalStack />} />
            <Route path="/integration"                    element={<IntegrationGuide />} />
            <Route path="/my-report"                      element={<ClientReportDownload />} />
            <Route path="/proof"                          element={<ProofLayer />} />
            <Route path="/verify-independently"           element={<IndependentVerification />} />
            <Route path="/docs"                           element={<GettingStarted />} />
            <Route path="/eidas"                          element={<ARFCompliance />} />
            <Route path="/full-demo"                      element={<FullDemo />} />
            <Route path="/book"                           element={<BookLanding />} />
            <Route path="/book-leads"                     element={<BookLeadsDashboard />} />
            <Route path="/oscillation"                    element={<OscillationDashboard />} />
            <Route path="/anomaly"                        element={<AnomalyDashboard />} />
            <Route path="/execution"                      element={<ExecutionDashboard />} />
            <Route path="/breach"                         element={<BreachDashboard />} />
            <Route path="/risk"                           element={<RiskDashboard />} />
            <Route path="/crisis-replay"                  element={<CrisisReplay />} />
            <Route path="/architecture"                   element={<ArchitecturePage />} />
            <Route path="/show"                           element={<InstitutionalDemo />} />
            <Route path="/why-omnix"                      element={<WhyOMNIX />} />
            <Route path="/about"                          element={<AboutPage />} />
            <Route path="/security"                       element={<SecurityPage />} />
            <Route path="/partners"                       element={<PartnersPage />} />
            <Route path="/customers"                      element={<CustomersPage />} />
            <Route path="/terms"                          element={<TermsOfService />} />
            <Route path="/privacy"                        element={<PrivacyPolicy />} />
            <Route path="/protocol"                       element={<ProtocolVisualizationPage />} />
            <Route path="/agent-trust-fabric"             element={<AgentTrustFabricPage />} />
            <Route path="/atf-verify"                     element={<ATFVerifierPage />} />
            <Route path="/atf-standard"                   element={<ATFStandardPage />} />
            <Route path="/atf-explained"                  element={<ATFExplainedPage />} />
            <Route path="/archive-verify"                 element={<ArchiveVerifierPage />} />
            <Route path="/trust-infrastructure"           element={<TrustInfrastructurePage />} />
            <Route path="/forensic-operations"            element={<ForensicOperationsDemoPage />} />
            <Route path="/governance-flow"               element={<GovernanceFlowPage />} />
            <Route path="/institutional-brief"           element={<InstitutionalBriefPage />} />
            <Route path="/start"                          element={<ReviewerStartPage />} />
            <Route path="/governance-api"                 element={<GovernanceAPIPage />} />
            <Route path="/proof-of-governance"            element={<ProofOfGovernancePage />} />
            <Route path="/settlement-gate"                element={<SettlementGatePage />} />
            <Route path="/video"                          element={<VideoTemplate />} />
            <Route path="/terminal"                       element={<Navigate to="/" replace />} />
            <Route path="*"                               element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </BrowserRouter>
    </ErrorBoundary>
  )
}

export default App
