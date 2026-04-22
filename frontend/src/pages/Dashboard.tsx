import LeadTable from '../components/Dashboard/LeadTable'

export default function DashboardPage() {
    return (
        <div style={{ minHeight: '100vh', background: '#0f0f1a', color: '#e2e8f0' }}>
            <div style={{ padding: '16px 24px', borderBottom: '1px solid #2d2d3d', display: 'flex', alignItems: 'center', gap: 12 }}>
                <span style={{ fontSize: 24 }}>🎬</span>
                <span style={{ fontWeight: 700, fontSize: 18 }}>AutoStream Dashboard</span>
                <a href="/" style={{ marginLeft: 'auto', color: '#6366f1', textDecoration: 'none', fontSize: 14 }}>← Back to Chat</a>
            </div>
            <LeadTable />
        </div>
    )
}
