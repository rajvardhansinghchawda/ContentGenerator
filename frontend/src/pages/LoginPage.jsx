import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import { getGoogleLoginUrl } from '../services/api.js'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import './LoginPage.css'

export default function LoginPage() {
  const { teacher, loading } = useAuth()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [redirecting, setRedirecting] = useState(false)
  const errorParam = searchParams.get('error')

  useEffect(() => {
    if (!loading && teacher) {
      navigate('/dashboard', { replace: true })
    }
  }, [teacher, loading, navigate])

  const handleGoogleLogin = async () => {
    setRedirecting(true)
    try {
      const res = await getGoogleLoginUrl()
      const authUrl = res.data?.url || res.data?.auth_url
      if (!authUrl) throw new Error('Missing OAuth URL in response')
      window.location.href = authUrl
    } catch {
      setRedirecting(false)
    }
  }

  if (loading) {
    return (
      <div className="login-loading">
        <LoadingSpinner size={40} text="Checking session..." />
      </div>
    )
  }

  return (
    <div className="login-page">
      {/* Left panel — branding */}
      <div className="login-left">
        <div className="login-left-content animate-fade-in">
          <div className="login-logo-mark">
            <span className="material-icons-outlined">auto_stories</span>
          </div>
          <h1 className="display-md login-brand-name">EduFlow AI</h1>
          <p className="login-tagline">
            AI-Powered Lecture<br />Content Generator
          </p>

          <div className="login-feature-pills">
            <div className="feature-pill">
              <span className="material-icons-outlined">description</span>
              Google Docs
            </div>
            <div className="feature-pill">
              <span className="material-icons-outlined">quiz</span>
              Google Forms
            </div>
            <div className="feature-pill">
              <span className="material-icons-outlined">psychology</span>
              AI-Powered
            </div>
          </div>

          <blockquote className="login-quote">
            "Generated 15 lectures into structured study guides in 4 seconds."
          </blockquote>
        </div>

        {/* Decorative orbs */}
        <div className="orb orb-1" />
        <div className="orb orb-2" />
      </div>

      {/* Right panel — auth card */}
      <div className="login-right">
        <div className="login-card animate-slide-up">
          <div className="login-card-header">
            <h2 className="headline-lg">Welcome Back</h2>
            <p className="body-md login-subtitle">
              Enter the workspace of the digital curator.
            </p>
          </div>

          {errorParam && (
            <div className="login-error" role="alert">
              <span className="material-icons-outlined">error_outline</span>
              {errorParam === 'auth_failed'
                ? 'Authentication failed. Please try again.'
                : decodeURIComponent(errorParam)}
            </div>
          )}

          <button
            id="google-login-btn"
            className="btn btn-primary btn-lg google-btn"
            onClick={handleGoogleLogin}
            disabled={redirecting}
          >
            {redirecting ? (
              <LoadingSpinner size={20} color="rgba(255,255,255,0.8)" />
            ) : (
              <svg width="20" height="20" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
                <path fill="#fff" d="M44.5 20H24v8.5h11.8C34.7 33.9 30.1 37 24 37c-7.2 0-13-5.8-13-13s5.8-13 13-13c3.1 0 5.9 1.1 8.1 2.9l6.4-6.4C34.6 4.1 29.6 2 24 2 11.8 2 2 11.8 2 24s9.8 22 22 22c11 0 21-8 21-22 0-1.3-.2-2.7-.5-4z"/>
              </svg>
            )}
            Continue with Google
          </button>

          <div className="login-divider">
            <span>Secure OAuth 2.0</span>
          </div>

          <div className="login-trust-row">
            <div className="trust-item">
              <span className="material-icons-outlined">verified_user</span>
              <span>Secure</span>
            </div>
            <div className="trust-item">
              <span className="material-icons-outlined">lock</span>
              <span>Private</span>
            </div>
            <div className="trust-item">
              <span className="material-icons-outlined">bolt</span>
              <span>Instant</span>
            </div>
          </div>

          <div className="login-footer-links">
            <a href="#">Privacy Policy</a>
            <span>·</span>
            <a href="#">Academic Integrity</a>
            <span>·</span>
            <a href="#">Support</a>
          </div>
        </div>
      </div>
    </div>
  )
}
