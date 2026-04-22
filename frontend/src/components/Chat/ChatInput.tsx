import { useState, KeyboardEvent } from 'react'

interface Props {
    onSend: (msg: string) => void
    disabled: boolean
}

export default function ChatInput({ onSend, disabled }: Props) {
    const [value, setValue] = useState('')

    const handleSend = () => {
        if (value.trim() && !disabled) {
            onSend(value.trim())
            setValue('')
        }
    }

    const handleKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            handleSend()
        }
    }

    return (
        <div style={{ display: 'flex', gap: 8, padding: '12px 16px', borderTop: '1px solid #2d2d3d', background: '#0f0f1a' }}>
            <textarea
                value={value}
                onChange={e => setValue(e.target.value)}
                onKeyDown={handleKey}
                placeholder="Ask about AutoStream plans, features..."
                disabled={disabled}
                rows={1}
                style={{
                    flex: 1, background: '#1e1e2e', border: '1px solid #2d2d3d', borderRadius: 12,
                    color: '#e2e8f0', padding: '10px 14px', fontSize: 14, resize: 'none',
                    outline: 'none', fontFamily: 'inherit',
                }}
            />
            <button
                onClick={handleSend}
                disabled={disabled || !value.trim()}
                style={{
                    background: disabled || !value.trim() ? '#374151' : '#6366f1',
                    color: 'white', border: 'none', borderRadius: 12,
                    padding: '0 20px', cursor: disabled ? 'not-allowed' : 'pointer',
                    fontSize: 14, fontWeight: 600, transition: 'background 0.2s',
                }}
            >
                Send
            </button>
        </div>
    )
}
