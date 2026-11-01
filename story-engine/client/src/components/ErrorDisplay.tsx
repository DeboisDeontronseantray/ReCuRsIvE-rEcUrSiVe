import { useError } from '../context/ErrorContext'

// Renders the shared error banner. Shows nothing when there is no error.
function ErrorDisplay() {
  const { error, clearError } = useError()

  if (!error) return null

  return (
    <div className="error-display">
      <div className="title-bar">
        <div className="title-bar-text">Error</div>
        <div className="title-bar-controls">
          <button aria-label="Close" onClick={clearError}></button>
        </div>
      </div>
      <div className="window-body">
        <p>{error}</p>
      </div>
    </div>
  )
}

export default ErrorDisplay
