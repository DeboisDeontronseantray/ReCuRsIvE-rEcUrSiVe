import copyAnimation from '../assets/copy-animation.gif'

interface CopyDialogProps {
  title: string
  message?: string
}

// Recreates the classic Windows 98 "copying files" dialog, using the real
// shell32 folder-copy animation (resource 161). Reused anywhere the client
// is waiting on a server response.
function CopyDialog({ title, message = 'Working...' }: CopyDialogProps) {
  return (
    <div className="copy-dialog-overlay">
      <div className="window copy-dialog">
        <div className="title-bar">
          <div className="title-bar-text">{title}</div>
        </div>
        <div className="window-body copy-dialog-body">
          <img src={copyAnimation} alt="Copying files" className="copy-dialog-gif" />
          <p className="copy-dialog-text">{message}</p>
        </div>
      </div>
    </div>
  )
}

export default CopyDialog
