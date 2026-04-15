import './LoadingSpinner.css'

export default function LoadingSpinner({ size = 32, text = '', color = 'var(--primary)' }) {
  return (
    <div className="loading-spinner-wrapper">
      <div
        className="loading-spinner"
        style={{
          width: size,
          height: size,
          borderColor: 'var(--surface-container-high)',
          borderTopColor: color,
          borderWidth: size > 32 ? 3 : 2,
        }}
      />
      {text && <p className="loading-spinner-text">{text}</p>}
    </div>
  )
}
