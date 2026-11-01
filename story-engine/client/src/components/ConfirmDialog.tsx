interface ConfirmDialogProps {
  title: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
  onConfirm: () => void
  onCancel: () => void
}

// Classic Windows 98 message box with the yellow exclamation icon, used
// anywhere a destructive action needs a confirmation stronger than a plain
// window.confirm() (which can't carry the icon).
function ConfirmDialog({
  title,
  message,
  confirmLabel = 'OK',
  cancelLabel = 'Cancel',
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  return (
    <div className="copy-dialog-overlay">
      <div className="window confirm-dialog">
        <div className="title-bar">
          <div className="title-bar-text">{title}</div>
          <div className="title-bar-controls">
            <button aria-label="Close" onClick={onCancel}></button>
          </div>
        </div>
        <div className="window-body confirm-dialog-body">
          <div className="confirm-dialog-content">
            <svg
              className="confirm-dialog-icon"
              viewBox="0 0 32 32"
              width="32"
              height="32"
              aria-hidden="true"
            >
              <path
                d="M16 2 L30 27 L2 27 Z"
                fill="#ffe600"
                stroke="#000000"
                strokeWidth="1.5"
                strokeLinejoin="round"
              />
              <rect x="14.5" y="11" width="3" height="9" fill="#000000" />
              <rect x="14.5" y="22" width="3" height="3" fill="#000000" />
            </svg>
            <p className="confirm-dialog-text">{message}</p>
          </div>
          <div className="confirm-dialog-actions">
            <button type="button" onClick={onConfirm}>
              {confirmLabel}
            </button>
            <button type="button" onClick={onCancel}>
              {cancelLabel}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ConfirmDialog
