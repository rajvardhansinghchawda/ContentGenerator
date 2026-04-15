import { createContext, useContext, useState, useEffect } from 'react'
import { getMe } from '../services/api.js'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [teacher, setTeacher] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getMe()
      .then(res => setTeacher(res.data))
      .catch(() => setTeacher(null))
      .finally(() => setLoading(false))
  }, [])

  return (
    <AuthContext.Provider value={{ teacher, setTeacher, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
