import { useState, useEffect } from 'react'
import { getJobs, regenerateJob } from '../services/api.js'
import LoadingSpinner from './LoadingSpinner.jsx'
import './JobHistoryList.css'

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function StatusBadge({ status }) {
  const map = {
    pending: { label: 'Pending', cls: 'badge-pending', icon: 'schedule' },
    processing: { label: 'Processing', cls: 'badge-processing', icon: 'sync' },
    completed: { label: 'Completed', cls: 'badge-completed', icon: 'check_circle' },
    failed: { label: 'Failed', cls: 'badge-failed', icon: 'error' },
  }
  const { label, cls, icon } = map[status] || map.pending
  return (
    <span className={`badge ${cls}`}>
      <span className="material-icons-outlined" style={{ fontSize: 13 }}>{icon}</span>
      {label}
    </span>
  )
}

export default function JobHistoryList({ refreshTrigger }) {
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [retrying, setRetrying] = useState(null)

  useEffect(() => {
    setLoading(true)
    getJobs()
      .then(res => {
        const data = res.data
        setJobs(data.results || data || [])
        setError(null)
      })
      .catch(() => setError('Failed to load history.'))
      .finally(() => setLoading(false))
  }, [refreshTrigger])

  const handleRegenerate = async (jobId) => {
    setRetrying(jobId)
    try {
      await regenerateJob(jobId)
      // Reload list after small delay
      setTimeout(() => {
        getJobs()
          .then(res => setJobs(res.data.results || res.data || []))
          .finally(() => setRetrying(null))
      }, 800)
    } catch {
      setRetrying(null)
    }
  }

  return (
    <div className="history-section">
      <div className="history-header">
        <div>
          <h2 className="headline-md">Recent Generations</h2>
          <p className="body-md" style={{ color: 'var(--on-surface-variant)', marginTop: 4 }}>
            Your lecture content library
          </p>
        </div>
        <span className="label-sm">{jobs.length} items</span>
      </div>

      {loading ? (
        <div className="history-loading">
          <LoadingSpinner size={32} text="Loading your library..." />
        </div>
      ) : error ? (
        <div className="history-empty">
          <span className="material-icons-outlined">cloud_off</span>
          <p>{error}</p>
        </div>
      ) : jobs.length === 0 ? (
        <div className="history-empty">
          <span className="material-icons-outlined">auto_stories</span>
          <p>No generations yet</p>
          <span className="label-md">Your first generation will appear here</span>
        </div>
      ) : (
        <div className="history-list">
          {jobs.map(job => (
            <div key={job.id} className="history-item animate-fade-in">
              <div className="history-item-main">
                <div className="history-item-info">
                  <h4 className="history-topic">{job.topic}</h4>
                  <div className="history-meta">
                    {job.subject_name && (
                      <span className="history-subject">
                        <span className="material-icons-outlined">school</span>
                        {job.subject_name}
                      </span>
                    )}
                    <span className="history-date">
                      <span className="material-icons-outlined">calendar_today</span>
                      {formatDate(job.created_at)}
                    </span>
                  </div>
                </div>
                <StatusBadge status={job.status} />
              </div>

              {job.status === 'completed' && (
                <div className="history-actions">
                  {job.pre_doc_url && (
                    <a href={job.pre_doc_url} target="_blank" rel="noopener noreferrer" className="btn btn-ghost btn-sm">
                      <span className="material-icons-outlined">description</span>
                      Pre-Doc
                    </a>
                  )}
                  {job.post_doc_url && (
                    <a href={job.post_doc_url} target="_blank" rel="noopener noreferrer" className="btn btn-ghost btn-sm">
                      <span className="material-icons-outlined">article</span>
                      Post-Doc
                    </a>
                  )}
                  {(job.quiz_url || job.quiz_form_url) && (
                    <a href={job.quiz_url || job.quiz_form_url} target="_blank" rel="noopener noreferrer" className="btn btn-secondary btn-sm">
                      <span className="material-icons-outlined">quiz</span>
                      Quiz
                    </a>
                  )}
                </div>
              )}

              {job.status === 'failed' && (
                <div className="history-actions">
                  <button
                    className="btn btn-ghost btn-sm"
                    onClick={() => handleRegenerate(job.id)}
                    disabled={retrying === job.id}
                  >
                    {retrying === job.id
                      ? <LoadingSpinner size={14} />
                      : <span className="material-icons-outlined">refresh</span>
                    }
                    Regenerate
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
