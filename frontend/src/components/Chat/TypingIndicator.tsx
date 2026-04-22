export default function TypingIndicator() {
    return (
        <div style={{ display: 'flex', gap: 4, padding: '12px 16px', alignItems: 'center' }}>
            {[0, 1, 2].map(i => (
                <span key={i} style={{
                    width: 8, height: 8, borderRadius: '50%', background: '#6366f1',
                    animation: `bounce 1.2s ease-in-out ${i * 0.2}s infinite`,
                }} />
            ))}
            <style>{`@keyframes bounce { 0%,80%,100%{transform:scale(0)} 40%{transform:scale(1)} }`}</style>
        </div>
    )
}
