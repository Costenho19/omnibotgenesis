export default function PrivacyPolicy() {
  return (
    <div style={{ background: '#0a0a0f', minHeight: '100vh', color: '#e2e8f0', fontFamily: 'Inter, sans-serif' }}>
      <div style={{ maxWidth: '800px', margin: '0 auto', padding: '60px 24px' }}>

        <div style={{ marginBottom: '48px' }}>
          <a href="/" style={{ display: 'flex', alignItems: 'center', gap: 10, textDecoration: 'none', marginBottom: 24 }}>
            <img src="/omnix_logo.png" alt="OMNIX QUANTUM" style={{ height: 34, width: 'auto', objectFit: 'contain' }} />
          </a>
          <a href="/" style={{ color: '#6366f1', textDecoration: 'none', fontSize: '14px' }}>← Back to OMNIX</a>
          <h1 style={{ fontSize: '36px', fontWeight: '700', marginTop: '24px', marginBottom: '8px', color: '#fff' }}>Privacy Policy</h1>
          <p style={{ color: '#64748b', fontSize: '14px' }}>Effective Date: March 23, 2026 · Last Updated: March 23, 2026</p>
        </div>

        <div style={{ lineHeight: '1.8', fontSize: '16px', color: '#cbd5e1' }}>

          <section style={{ marginBottom: '40px' }}>
            <h2 style={{ color: '#fff', fontSize: '20px', fontWeight: '600', marginBottom: '16px', borderBottom: '1px solid #1e293b', paddingBottom: '8px' }}>1. Who We Are</h2>
            <p>OMNIX ("we", "our", "us") operates the Decision Governance Infrastructure platform accessible at omnixquantum.net. This Privacy Policy explains what data we collect, how we use it, and your rights regarding that data.</p>
            <p style={{ marginTop: '12px' }}>Contact: <a href="mailto:contacto@omnixquantum.net" style={{ color: '#6366f1' }}>contacto@omnixquantum.net</a> · Abu Dhabi, UAE</p>
          </section>

          <section style={{ marginBottom: '40px' }}>
            <h2 style={{ color: '#fff', fontSize: '20px', fontWeight: '600', marginBottom: '16px', borderBottom: '1px solid #1e293b', paddingBottom: '8px' }}>2. Data We Collect</h2>

            <h3 style={{ color: '#e2e8f0', fontSize: '17px', fontWeight: '600', marginBottom: '10px', marginTop: '20px' }}>2.1 Data You Provide</h3>
            <ul style={{ paddingLeft: '24px' }}>
              <li style={{ marginBottom: '8px' }}><strong>Email address</strong> — when you submit a scenario through the public sandbox or contact us directly</li>
              <li style={{ marginBottom: '8px' }}><strong>Scenario data</strong> — text descriptions, signals, and parameters you submit to the governance pipeline</li>
              <li style={{ marginBottom: '8px' }}><strong>Telegram data</strong> — username and messages if you interact with our Telegram bot (@omnixglobal2025_bot)</li>
            </ul>

            <h3 style={{ color: '#e2e8f0', fontSize: '17px', fontWeight: '600', marginBottom: '10px', marginTop: '20px' }}>2.2 Data Collected Automatically</h3>
            <ul style={{ paddingLeft: '24px' }}>
              <li style={{ marginBottom: '8px' }}><strong>Usage data</strong> — pages visited, features used, timestamps</li>
              <li style={{ marginBottom: '8px' }}><strong>Technical data</strong> — IP address, browser type, device type, referral source</li>
              <li style={{ marginBottom: '8px' }}><strong>Governance receipts</strong> — cryptographically signed records of governance decisions processed by the system</li>
            </ul>

            <h3 style={{ color: '#e2e8f0', fontSize: '17px', fontWeight: '600', marginBottom: '10px', marginTop: '20px' }}>2.3 Data We Do Not Collect</h3>
            <ul style={{ paddingLeft: '24px' }}>
              <li style={{ marginBottom: '8px' }}>Payment or financial account details (we do not process payments directly)</li>
              <li style={{ marginBottom: '8px' }}>Biometric data of any kind</li>
              <li style={{ marginBottom: '8px' }}>Data from children under 16</li>
            </ul>
          </section>

          <section style={{ marginBottom: '40px' }}>
            <h2 style={{ color: '#fff', fontSize: '20px', fontWeight: '600', marginBottom: '16px', borderBottom: '1px solid #1e293b', paddingBottom: '8px' }}>3. How We Use Your Data</h2>
            <p>We use collected data to:</p>
            <ul style={{ marginTop: '12px', paddingLeft: '24px' }}>
              <li style={{ marginBottom: '8px' }}>Operate and improve the governance pipeline</li>
              <li style={{ marginBottom: '8px' }}>Generate and store cryptographically signed governance receipts</li>
              <li style={{ marginBottom: '8px' }}>Respond to inquiries and support requests</li>
              <li style={{ marginBottom: '8px' }}>Analyze platform usage to improve performance and accuracy</li>
              <li style={{ marginBottom: '8px' }}>Detect and prevent abuse or unauthorized access</li>
              <li style={{ marginBottom: '8px' }}>Send transactional communications related to your use of the platform</li>
            </ul>
            <p style={{ marginTop: '12px' }}>We do not sell your data to third parties. We do not use your data to serve advertising.</p>
          </section>

          <section style={{ marginBottom: '40px' }}>
            <h2 style={{ color: '#fff', fontSize: '20px', fontWeight: '600', marginBottom: '16px', borderBottom: '1px solid #1e293b', paddingBottom: '8px' }}>4. Data Storage and Security</h2>
            <p>Your data is stored in a PostgreSQL database hosted on Railway (railway.app) infrastructure. Data in transit is encrypted via TLS 1.2+. Governance decision payloads are encrypted at rest using AES-256 encryption.</p>
            <p style={{ marginTop: '12px' }}>Governance receipts are cryptographically signed using post-quantum cryptographic algorithms standardized by NIST. This ensures the integrity and authenticity of each receipt cannot be forged or altered.</p>
            <p style={{ marginTop: '12px' }}>We implement role-based access controls and rate limiting on all API endpoints. No single point of access exposes raw internal data.</p>
          </section>

          <section style={{ marginBottom: '40px' }}>
            <h2 style={{ color: '#fff', fontSize: '20px', fontWeight: '600', marginBottom: '16px', borderBottom: '1px solid #1e293b', paddingBottom: '8px' }}>5. Data Retention</h2>
            <p>We retain governance receipts indefinitely as part of the cryptographic audit chain — these are public records of decisions processed by the system.</p>
            <p style={{ marginTop: '12px' }}>Email addresses and scenario content submitted through the sandbox are retained for up to 24 months to support system calibration, then anonymized or deleted.</p>
            <p style={{ marginTop: '12px' }}>You may request deletion of your personal data at any time by contacting us at <a href="mailto:contacto@omnixquantum.net" style={{ color: '#6366f1' }}>contacto@omnixquantum.net</a>.</p>
          </section>

          <section style={{ marginBottom: '40px' }}>
            <h2 style={{ color: '#fff', fontSize: '20px', fontWeight: '600', marginBottom: '16px', borderBottom: '1px solid #1e293b', paddingBottom: '8px' }}>6. Third-Party Services</h2>
            <p>We use the following third-party services which may process data on our behalf:</p>
            <ul style={{ marginTop: '12px', paddingLeft: '24px' }}>
              <li style={{ marginBottom: '8px' }}><strong>Google Gemini / OpenAI / Anthropic</strong> — AI processing for scenario interpretation (scenario text only, no personal data)</li>
              <li style={{ marginBottom: '8px' }}><strong>Railway</strong> — cloud infrastructure and database hosting</li>
              <li style={{ marginBottom: '8px' }}><strong>Telegram</strong> — messaging interface for bot interactions</li>
              <li style={{ marginBottom: '8px' }}><strong>Finnhub / Alpha Vantage / Tavily</strong> — market data APIs (no personal data shared)</li>
            </ul>
            <p style={{ marginTop: '12px' }}>Each third party is bound by their own privacy policies. We do not share personal data with AI providers beyond what is necessary to process your submitted scenario.</p>
          </section>

          <section style={{ marginBottom: '40px' }}>
            <h2 style={{ color: '#fff', fontSize: '20px', fontWeight: '600', marginBottom: '16px', borderBottom: '1px solid #1e293b', paddingBottom: '8px' }}>7. Your Rights</h2>
            <p>Depending on your jurisdiction, you may have the following rights:</p>
            <ul style={{ marginTop: '12px', paddingLeft: '24px' }}>
              <li style={{ marginBottom: '8px' }}><strong>Access</strong> — request a copy of the personal data we hold about you</li>
              <li style={{ marginBottom: '8px' }}><strong>Correction</strong> — request correction of inaccurate data</li>
              <li style={{ marginBottom: '8px' }}><strong>Deletion</strong> — request deletion of your personal data ("right to be forgotten")</li>
              <li style={{ marginBottom: '8px' }}><strong>Portability</strong> — receive your data in a structured, machine-readable format</li>
              <li style={{ marginBottom: '8px' }}><strong>Objection</strong> — object to processing of your data for certain purposes</li>
            </ul>
            <p style={{ marginTop: '12px' }}>To exercise any of these rights, contact us at <a href="mailto:contacto@omnixquantum.net" style={{ color: '#6366f1' }}>contacto@omnixquantum.net</a>. We will respond within 30 days.</p>
          </section>

          <section style={{ marginBottom: '40px' }}>
            <h2 style={{ color: '#fff', fontSize: '20px', fontWeight: '600', marginBottom: '16px', borderBottom: '1px solid #1e293b', paddingBottom: '8px' }}>8. Cookies</h2>
            <p>The platform uses minimal, essential cookies only — no tracking cookies or third-party advertising cookies are used. Essential cookies support session authentication for the dashboard and API access control.</p>
            <p style={{ marginTop: '12px' }}>We do not use Google Analytics, Meta Pixel, or any behavioral tracking tools.</p>
          </section>

          <section style={{ marginBottom: '40px' }}>
            <h2 style={{ color: '#fff', fontSize: '20px', fontWeight: '600', marginBottom: '16px', borderBottom: '1px solid #1e293b', paddingBottom: '8px' }}>9. International Transfers</h2>
            <p>OMNIX operates globally. Your data may be processed in the United States or other jurisdictions where our infrastructure providers operate. By using the Service, you consent to these transfers.</p>
            <p style={{ marginTop: '12px' }}>We take appropriate safeguards to ensure your data receives adequate protection regardless of where it is processed.</p>
          </section>

          <section style={{ marginBottom: '40px' }}>
            <h2 style={{ color: '#fff', fontSize: '20px', fontWeight: '600', marginBottom: '16px', borderBottom: '1px solid #1e293b', paddingBottom: '8px' }}>10. Changes to This Policy</h2>
            <p>We may update this Privacy Policy periodically. The effective date at the top of this page will reflect the latest revision. Continued use of the Service after changes constitutes acceptance of the revised policy.</p>
          </section>

          <section style={{ marginBottom: '40px' }}>
            <h2 style={{ color: '#fff', fontSize: '20px', fontWeight: '600', marginBottom: '16px', borderBottom: '1px solid #1e293b', paddingBottom: '8px' }}>11. Contact</h2>
            <div style={{ padding: '16px', background: '#1e293b', borderRadius: '8px' }}>
              <p style={{ margin: '0' }}>Email: <a href="mailto:contacto@omnixquantum.net" style={{ color: '#6366f1' }}>contacto@omnixquantum.net</a></p>
              <p style={{ margin: '8px 0 0 0' }}>Website: <a href="https://omnixquantum.net" style={{ color: '#6366f1' }}>omnixquantum.net</a></p>
              <p style={{ margin: '8px 0 0 0' }}>Abu Dhabi, UAE</p>
            </div>
          </section>

        </div>

        <div style={{ marginTop: '48px', padding: '24px', background: '#0f172a', borderRadius: '8px', border: '1px solid #1e293b', textAlign: 'center' }}>
          <p style={{ color: '#64748b', fontSize: '14px', margin: '0' }}>
            <a href="/terms" style={{ color: '#6366f1', marginRight: '24px' }}>Terms of Service</a>
            <a href="/" style={{ color: '#6366f1' }}>Back to OMNIX</a>
          </p>
        </div>

      </div>
    </div>
  )
}
