import { useState } from 'react'

interface EntityCardProps<T> {
  entity: T
  patchUrl: string
  onSaved: (updated: T) => void
  renderFields: (
    entity: T,
    updateField: <K extends keyof T>(field: K, value: T[K]) => void,
  ) => React.ReactNode
  // When true, hides the Save button — used once a novel is locked (see
  // Novel.tsx), since the server rejects these PATCHes with 423 at that
  // point anyway. Fields still render via renderFields; only saving is
  // disabled, so the caller doesn't need a separate read-only field layout.
  readOnly?: boolean
}

// A generic editable card: renders whatever fields the caller wants via
// renderFields, tracks local edits against the last-saved entity, and PATCHes
// only the changed entity to patchUrl on Save. Used for characters, locations,
// items, groups, and events, which all follow the same edit/save shape
// but have different fields.
function EntityCard<T extends { id: string }>({
  entity,
  patchUrl,
  onSaved,
  renderFields,
  readOnly = false,
}: EntityCardProps<T>) {
  const [draft, setDraft] = useState<T>(entity)
  const [saved, setSaved] = useState<T>(entity)
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [justSaved, setJustSaved] = useState(false)

  const isDirty = JSON.stringify(draft) !== JSON.stringify(saved)

  function updateField<K extends keyof T>(field: K, value: T[K]) {
    setDraft((prev) => ({ ...prev, [field]: value }))
    setJustSaved(false)
  }

  async function handleSave() {
    if (!isDirty) return
    setSaving(true)
    setSaveError(null)
    setJustSaved(false)
    try {
      const { id: _id, ...body } = draft as T & { id: string }
      const res = await fetch(patchUrl, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!res.ok) throw new Error(`PATCH ${patchUrl} failed: ${res.status}`)
      const data = await res.json()
      setDraft(data)
      setSaved(data)
      setJustSaved(true)
      onSaved(data)
    } catch (err) {
      console.error(err)
      setSaveError('Failed to save. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="novel-character-card">
      {renderFields(draft, updateField)}
      {!readOnly && (
        <div className="novel-character-card-actions">
          {saveError && <span className="novels-error">{saveError}</span>}
          {justSaved && !saveError && <span className="novel-detail-saved">Saved.</span>}
          <button type="button" disabled={saving || !isDirty} onClick={handleSave}>
            {saving ? 'Saving...' : 'Save'}
          </button>
        </div>
      )}
    </div>
  )
}

export default EntityCard
