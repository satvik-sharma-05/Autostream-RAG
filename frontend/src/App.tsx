import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import ChatPage from './pages/Chat'
import DashboardPage from './pages/Dashboard'

export default function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/" element={<ChatPage />} />
                <Route path="/dashboard" element={<DashboardPage />} />
            </Routes>
        </BrowserRouter>
    )
}
