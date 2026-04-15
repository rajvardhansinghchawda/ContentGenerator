import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import { createJob, logout } from '../services/api.js'
import GenerationForm from '../components/GenerationForm.jsx'
import JobStatusCard from '../components/JobStatusCard.jsx'
import JobHistoryList from '../components/JobHistoryList.jsx'
import ProfileSettings from '../components/ProfileSettings.jsx'
import './DashboardPage.css'

export default function DashboardPage() {
  const { teacher, setTeacher } = useAuth()
  const navigate = useNavigate()
  const [activeJobId, setActiveJobId] = useState(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [historyRefresh, setHistoryRefresh] = useState(0)
  const [isSettingsOpen, setIsSettingsOpen] = useState(false)

  const handleFormSubmit = async (formData) => {
    setIsGenerating(true)
    setActiveJobId(null)
    try {
      const res = await createJob(formData)
      const jobId = res.data?.id || res.data?.job_id
      if (!jobId) throw new Error('Missing job id in create response')
      setActiveJobId(jobId)
    } catch (err) {
      console.error('Failed to create job:', err)
      setIsGenerating(false)
    }
  }

  const handleJobComplete = (data) => {
    setIsGenerating(false)
    // Refresh history list
    setHistoryRefresh(prev => prev + 1)
  }

  const handleRetry = () => {
    setActiveJobId(null)
    setIsGenerating(false)
  }

  const handleLogout = async () => {
    try {
      await logout()
    } finally {
      setTeacher(null)
      navigate('/', { replace: true })
    }
  }

  return (
    <div className="dashboard-layout">
      {/* ── Sidebar ── */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <div className="sidebar-logo-mark">
            <span className="material-icons-outlined">auto_stories</span>
          </div>
          <div>
            <div className="sidebar-brand">EduFlow AI</div>
            <div className="label-sm">Digital Curator</div>
          </div>
        </div>

        <nav className="sidebar-nav" aria-label="Main navigation">
          <a href="#generate" className="sidebar-nav-item active">
            <span className="material-icons-outlined">add_circle</span>
            Generate
          </a>
          <a href="#history" className="sidebar-nav-item">
            <span className="material-icons-outlined">library_books</span>
            Lecture Library
          </a>
          <button onClick={() => setIsSettingsOpen(true)} className="sidebar-nav-item btn-sidebar">
            <span className="material-icons-outlined">settings_suggest</span>
            Settings
          </button>
        </nav>

        <div className="sidebar-footer">
          {teacher && (
            <div className="sidebar-user">
              {teacher.profile_pic ? (
                <img
                  src={teacher.profile_pic}
                  alt={teacher.full_name}
                  className="sidebar-avatar"
                />
              ) : (
                <div className="sidebar-avatar-placeholder">
                  {(teacher.full_name || teacher.email || 'T')[0].toUpperCase()}
                </div>
              )}
              <div className="sidebar-user-info">
                <div className="sidebar-user-name">{teacher.full_name || 'Teacher'}</div>
                <div className="sidebar-user-email">{teacher.email}</div>
              </div>
            </div>
          )}
          <button
            id="logout-btn"
            className="btn btn-ghost btn-sm sidebar-logout"
            onClick={handleLogout}
          >
            <span className="material-icons-outlined">logout</span>
            Sign out
          </button>
        </div>
      </aside>

      {/* ── Main Content ── */}
      <main className="dashboard-main">
        {/* Header */}
        <header className="dashboard-header">
          <div>
            <h1 className="headline-lg">
              Good {getGreeting()},{' '}
              <span className="greeting-name">
                {teacher?.full_name?.split(' ')[0] || 'Teacher'}
              </span>
            </h1>
            <p className="body-md" style={{ color: 'var(--on-surface-variant)', marginTop: 4 }}>
              Ready to craft your next lecture?
            </p>
          </div>
        </header>

        {/* Content sections */}
        <div className="dashboard-content">
          {/* ── Generation Section ── */}
          <section id="generate" className="content-section">
            <div className="card card-elevated">
              <GenerationForm onSubmit={handleFormSubmit} disabled={isGenerating} />
            </div>

            {/* Job progress card */}
            {activeJobId && (
              <div className="job-status-wrapper animate-slide-up">
                <JobStatusCard
                  jobId={activeJobId}
                  onComplete={handleJobComplete}
                  onRetry={handleRetry}
                />
              </div>
            )}
          </section>

          {/* ── History Section ── */}
          <section id="history" className="content-section">
            <JobHistoryList refreshTrigger={historyRefresh} />
          </section>
        </div>

        <ProfileSettings 
          isOpen={isSettingsOpen} 
          onClose={() => setIsSettingsOpen(false)} 
        />
      </main>
    </div>
  )
}

function getGreeting() {
  const hour = new Date().getHours()
  if (hour < 12) return 'morning'
  if (hour < 17) return 'afternoon'
  return 'evening'
}
