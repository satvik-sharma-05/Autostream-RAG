import { api } from './api'

export interface ChatResponse {
    response: string
    session_id: string
    intent: string
    intent_confidence: number
    lead_captured: boolean
    turn_count: number
}

export interface Lead {
    name: string
    email: string
    platform: string
    captured_at: string
    status: string
}

export async function sendMessage(message: string, sessionId: string): Promise<ChatResponse> {
    const { data } = await api.post<ChatResponse>('/chat', { message, session_id: sessionId })
    return data
}

export async function getLeads(): Promise<Lead[]> {
    const { data } = await api.get<Lead[]>('/leads')
    return data
}
