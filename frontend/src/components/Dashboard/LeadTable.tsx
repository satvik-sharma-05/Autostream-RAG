import { useEffect, useState } from 'react'
import { getLeads, Lead } from '../../services/chat'

export default function LeadTable() {
    const [leads, setLeads] = useState<Lead[]>([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        getLeads().then(setLeads).finally(() => setLoading(false))
    }, [])

    const exportCSV = () => {
        window.open('http://localhost:8000/api/v1/leads/export', '_blank')
    }

    if (loading) return <div style={{ color: '#6b7280', padding: 20 }}>Loading leads...</div>

    return (
        <div style={{ padding: 24 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <h2 style={{ fontSize: 20, fontWeight: 700 }}>Captured Leads ({leads.length})</h2>
                <button onClick={exportCSV} style={{ background: '#6366f1', color: 'white', border: 'none', borderRadius: 8, padding: '8px 16px', cursor: 'pointer' }}>
                    Export CSV
                </button>
            </div>
            {leads.length === 0 ? (
                <div style={{ color: '#6b7280', textAlign: 'center', padding: 40 }}>No leads captured yet. Start chatting!</div>
            ) : (
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
                    <thead>
                        <tr style={{ borderBottom: '1px solid #2d2d3d' }}>
                            {['Name', 'Email', 'Platform', 'Captured At', 'Status'].map(h => (
                                <th key={h} style={{ textAlign: 'left', padding: '8px 12px', color: '#9ca3af', fontWeight: 600 }}>{h}</th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {leads.map((l, i) => (
                            <tr key={i} style={{ borderBottom: '1px solid #1e1e2e' }}>
                                <td style={{ padding: '10px 12px' }}>{l.name}</td>
                                <td style={{ padding: '10px 12px', color: '#6366f1' }}>{l.email}</td>
                                <td style={{ padding: '10px 12px' }}>{l.platform}</td>
                                <td style={{ padding: '10px 12px', color: '#6b7280' }}>{new Date(l.captured_at).toLocaleString()}</td>
                                <td style={{ padding: '10px 12px' }}>
                                    <span style={{ background: '#065f46', color: '#6ee7b7', padding: '2px 8px', borderRadius: 12, fontSize: 12 }}>{l.status}</span>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}
        </div>
    )
}
