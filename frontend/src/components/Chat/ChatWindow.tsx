import { useState, useRef, useEffect } from 'react'
import { v4 as uuidv4 } from 'uuid'
import MessageBubble from './MessageBubble'
import ChatInput from './ChatInput'
import TypingIndicator from './TypingIndicator'
import { sendMessage } from '../../services/chat'

interface Message {
    role: 'user' | 'assistant'
    content: string
    intent?: string
}

export default function ChatWindow() {
    const [messages, setMessages] = useState<Message[]>([
        { role: 'assistant', content: "Hi! I'm AutoStream's AI assistant. Ask me about our video editing plans, features, or anything else. How can I help you today?" }
    ])
    const [loading, setLoading] = useState(false)
    const [sessionId] = useState(() => uuidv4())
    const [leadCaptured, setLeadCaptured] = useState(false)
    const bottomRef = useRef<HTMLDivElement>(null)

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages, loading])

    const handleSend = async (text: string) => {
        setMessages(prev => [...prev, { role: 'user', content: text }])
        setLoading(true)
        try {
            const res = await sendMessage(text, sessionId)
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: res.response,
                intent: res.intent,
            }])
            if (res.lead_captured) setLeadCaptured(true)
        } catch {
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: 'Sorry, something went wrong. Please try again.',
            }])
        } finally {
            setLoading(false)
        }
    }

    return (
        <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', maxWidth: 720, margin: '0 auto' }}>
            {/* Header */}
            <div style={{ padding: '16px 20px', borderBottom: '1px solid #2d2d3d', background: '#0f0f1a', display: 'flex', alignItems: 'center', gap: 12 }}>
                <div style={{ width: 40, height: 40, borderRadius: '50%', background: 'linear-gradient(135deg,#6366f1,#8b5cf6)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 20 }}>🎬</div>
                <div>
                    <div style={{ fontWeight: 700, fontSize: 16 }}>AutoStream AI</div>
                    <div style={{ fontSize: 12, color: '#6b7280' }}>Video Editing SaaS Assistant</div>
                </div>
                {leadCaptured && (
                    <div style={{ marginLeft: 'auto', background: '#065f46', color: '#6ee7b7', padding: '4px 10px', borderRadius: 20, fontSize: 12 }}>
                        ✓ Lead Captured
                    </div>
                )}
            </div>

            {/* Messages */}
            <div style={{ flex: 1, overflowY: 'auto', padding: '16px', background: '#0f0f1a' }}>
                {messages.map((m, i) => (
                    <MessageBubble key={i} role={m.role} content={m.content} intent={m.intent} />
                ))}
                {loading && <TypingIndicator />}
                <div ref={bottomRef} />
            </div>

            <ChatInput onSend={handleSend} disabled={loading} />
        </div>
    )
}
