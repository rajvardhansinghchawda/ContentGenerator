import { useAuth } from '../context/AuthContext.jsx'
import { Navigate } from 'react-router-dom'
import LoadingSpinner from './LoadingSpinner.jsx'

export default function ProtectedRoute({ children }) {
  const { teacher, loading } = useAuth()

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        background: 'var(--background)',
      }}>
        <LoadingSpinner size={48} text="Entering the workspace..." />
      </div>
    )
  }

  if (!teacher) {
    return <Navigate to="/" replace />
  }

  return children
}
