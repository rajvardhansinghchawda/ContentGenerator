import { useJobPolling } from '../hooks/useJobPolling.js'
import LoadingSpinner from './LoadingSpinner.jsx'
import './JobStatusCard.css'

const STEPS = [
  { key: 'ai', label: 'Calling AI Engine...', icon: 'psychology' },
  { key: 'docs', label: 'Creating Google Docs...', icon: 'description' },
  { key: 'quiz', label: 'Setting up Quiz Form...', icon: 'quiz' },
]

export default function JobStatusCard({ jobId, onComplete, onRetry }) {
  const status = useJobPolling(jobId, onComplete)
  const quizUrl = status?.quiz_url || status?.quiz_form_url

  if (!status) {
    return (
      <div className="status-card status-card-pending animate-slide-up">
        <LoadingSpinner size={36} text="Preparing your content..." />
      </div>
    )
  }

  if (status.status === 'pending') {
    return (
      <div className="status-card status-card-pending animate-slide-up">
        <LoadingSpinner size={36} text="Preparing your content..." />
      </div>
    )
  }

  if (status.status === 'processing') {
    return (
      <div className="status-card status-card-processing animate-slide-up">
        <div className="status-shimmer" />
        <div className="status-card-content">
          <h3 className="headline-sm">
            <span className="material-icons-outlined" style={{ color: 'var(--primary)' }}>auto_awesome</span>
            Synthesizing Lecture Material
          </h3>
          <p className="body-md status-step-label">
            {status.current_step || 'Processing...'}
          </p>
          <div className="status-steps">
            {STEPS.map((step, i) => {
              const currentIdx = status.current_step?.toLowerCase().includes('ai') ? 0
                : status.current_step?.toLowerCase().includes('doc') ? 1
                : status.current_step?.toLowerCase().includes('quiz') ? 2 : 0
              const isDone = i < currentIdx
              const isActive = i === currentIdx

              return (
                <div
                  key={step.key}
                  className={`status-step ${isDone ? 'done' : ''} ${isActive ? 'active' : ''}`}
                >
                  <span className="material-icons-outlined">{step.icon}</span>
                  <span>{step.label}</span>
                  {isDone && <span className="material-icons-outlined step-check">check_circle</span>}
                  {isActive && <LoadingSpinner size={16} />}
                </div>
              )
            })}
          </div>
        </div>
      </div>
    )
  }

  if (status.status === 'completed') {
    return (
      <div className="status-card status-card-completed animate-slide-up">
        <div className="status-success-header">
          <span className="material-icons-outlined success-icon">check_circle</span>
          <div>
            <h3 className="headline-sm">Content Generated Successfully!</h3>
            <p className="body-md" style={{ color: 'var(--on-surface-variant)' }}>
              Your materials are ready. Click below to open them.
            </p>
          </div>
        </div>
        <div className="status-links">
          {status.pre_doc_url && (
            <a href={status.pre_doc_url} target="_blank" rel="noopener noreferrer" className="btn btn-secondary btn-sm">
              <span className="material-icons-outlined">description</span>
              Pre-Doc
            </a>
          )}
          {status.post_doc_url && (
            <a href={status.post_doc_url} target="_blank" rel="noopener noreferrer" className="btn btn-secondary btn-sm">
              <span className="material-icons-outlined">article</span>
              Post-Doc
            </a>
          )}
          {quizUrl && (
            <a href={quizUrl} target="_blank" rel="noopener noreferrer" className="btn btn-primary btn-sm">
              <span className="material-icons-outlined">quiz</span>
              Quiz Form
            </a>
          )}
        </div>
      </div>
    )
  }

  if (status.status === 'failed') {
    return (
      <div className="status-card status-card-failed animate-slide-up">
        <div className="status-fail-header">
          <span className="material-icons-outlined fail-icon">error_outline</span>
          <div>
            <h3 className="headline-sm">Generation Failed</h3>
            <p className="body-md" style={{ color: 'var(--on-surface-variant)' }}>
              {status.error_message || 'Something went wrong. Please try again.'}
            </p>
          </div>
        </div>
        <button className="btn btn-danger btn-sm" onClick={onRetry}>
          <span className="material-icons-outlined">refresh</span>
          Retry Generation
        </button>
      </div>
    )
  }

  return null
}
