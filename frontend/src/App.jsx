import { useAuthStore } from './store/authStore'
import LoginPage from './pages/LoginPage'
import EditorPage from './pages/EditorPage'
import './index.css'

export default function App() {
  const token = useAuthStore((s) => s.token)
  return token ? <EditorPage /> : <LoginPage />
}
