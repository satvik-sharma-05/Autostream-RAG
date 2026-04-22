interface Props {
    role: 'user' | 'assistant'
    content: string
    intent?: string
}

export default function MessageBubble({ role, content, intent }: Props) {
    const isUser = role === 'user'
    return (
        <div style={{
            display: 'flex',
            justifyContent: isUser ? 'flex-end' : 'flex-start',
            marginBottom: 12,
        }}>
            {!isUser && (
                <div style={{
                    width: 32, height: 32, borderRadius: '50%', background: '#6366f1',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 14, marginRight: 8, flexShrink: 0,
                }}>🤖</div>
            )}
            <div style={{ maxWidth: '70%' }}>
                <div style={{
                    background: isUser ? '#6366f1' : '#1e1e2e',
                    color: '#e2e8f0',
                    padding: '10px 14px',
                    borderRadius: isUser ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
                    fontSize: 14,
                    lineHeight: 1.5,
                    border: isUser ? 'none' : '1px solid #2d2d3d',
                    whiteSpace: 'pre-wrap',
                }}>
                    {content}
                </div>
                {intent && !isUser && (
                    <div style={{ fontSize: 11, color: '#6b7280', marginTop: 4, paddingLeft: 4 }}>
                        intent: {intent}
                    </div>
                )}
            </div>
        </div>
    )
}
