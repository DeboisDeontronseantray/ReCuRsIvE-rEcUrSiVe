import { useEffect, useState } from 'react'
import ConfirmDialog from './ConfirmDialog'
import CopyDialog from './CopyDialog'

interface OutlineBeatSummary {
  id: string
  sort_order: number
  title: string | null
}

interface ChapterSummary {
  id: string
  outline_beat_id: string
  sort_order: number
  title: string | null
  word_count: number | null
}

interface Episode extends ChapterSummary {
  edited_prose: string
  raw_prose: string
  summary: string
}

interface ModelsResponse {
  models: string[]
  defaults: Record<string, string>
}

interface EpisodesProps {
  novelId: string
  outlineBeats: OutlineBeatSummary[]
  chaptersPrepared: boolean
  locked: boolean
  onLockChanged: () => void
}

interface ChapterPipelineModelPickerProps {
  availableModels: string[]
  generateModel: string
  setGenerateModel: (v: string) => void
  generateReasoning: boolean
  setGenerateReasoning: (v: boolean) => void
  editModel: string
  setEditModel: (v: string) => void
  editReasoning: boolean
  setEditReasoning: (v: boolean) => void
  stateModel: string
  setStateModel: (v: string) => void
  stateReasoning: boolean
  setStateReasoning: (v: boolean) => void
}

// One fieldset per prose-generation-phase step (Generate Prose, Edit Prose,
// Update State), each with its own model dropdown and reasoning checkbox —
// same pattern as PromptForm's per-step pipeline fieldsets.
function ChapterPipelineModelPicker({
  availableModels,
  generateModel,
  setGenerateModel,
  generateReasoning,
  setGenerateReasoning,
  editModel,
  setEditModel,
  editReasoning,
  setEditReasoning,
  stateModel,
  setStateModel,
  stateReasoning,
  setStateReasoning,
}: ChapterPipelineModelPickerProps) {
  // Edit Prose is temporarily disabled pipeline-wide (edit_chapter_prose is
  // commented out in router._run_chapter_pipeline pending new edit prompts —
  // see chapter_editing_prompts.py) — greyed out here to match, rather than
  // removed, so the model/reasoning choice is preserved for when it's back.
  const steps: [string, string, (v: string) => void, boolean, (v: boolean) => void, boolean][] = [
    ['Generate Prose', generateModel, setGenerateModel, generateReasoning, setGenerateReasoning, false],
    ['Edit Prose', editModel, setEditModel, editReasoning, setEditReasoning, true],
    ['Update State', stateModel, setStateModel, stateReasoning, setStateReasoning, false],
  ]
  return (
    <div className="novels-create-pipeline">
      {steps.map(([label, model, setModel, reasoning, setReasoning, stepDisabled]) => (
        <fieldset
          key={label}
          className={
            stepDisabled ? 'novels-create-pipeline-step novels-create-pipeline-step--disabled' : 'novels-create-pipeline-step'
          }
          disabled={stepDisabled}
        >
          <legend>{label}{stepDisabled ? ' (disabled for now)' : ''}</legend>
          <div className="novels-create-pipeline-row">
            <div className="field-row-stacked novels-create-pipeline-select">
              <label htmlFor={`chapter-${label}-model`}>Model</label>
              <select
                id={`chapter-${label}-model`}
                value={model}
                onChange={(e) => setModel(e.target.value)}
              >
                {availableModels.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
            </div>
            <div className="field-row">
              <input
                id={`chapter-${label}-reasoning`}
                type="checkbox"
                checked={reasoning}
                onChange={(e) => setReasoning(e.target.checked)}
              />
              <label htmlFor={`chapter-${label}-reasoning`}>Reasoning</label>
            </div>
          </div>
        </fieldset>
      ))}
    </div>
  )
}

// The "Episodes" tab: a sidebar listing every outline beat (generated or
// not) and a body showing the selected chapter's prose. Generates one
// episode at a time — only the current last generated episode (or the next
// ungenerated one) offers Generate/Regenerate; earlier chapters are
// read-only, matching the server's own ordering rules (see
// router._run_chapter_pipeline).
function Episodes({ novelId, outlineBeats, chaptersPrepared, locked, onLockChanged }: EpisodesProps) {
  const [chapters, setEpisodes] = useState<ChapterSummary[] | null>(null)
  const [chaptersError, setEpisodesError] = useState<string | null>(null)
  const [selectedBeatId, setSelectedBeatId] = useState<string | null>(null)
  const [selectedChapter, setSelectedChapter] = useState<Episode | null>(null)
  const [detailError, setDetailError] = useState<string | null>(null)
  const [pending, setPending] = useState<'generate' | 'regenerate' | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [confirmingRegenerate, setConfirmingRegenerate] = useState(false)

  const [availableModels, setAvailableModels] = useState<string[]>([])
  const [generateModel, setGenerateModel] = useState('')
  const [generateReasoning, setGenerateReasoning] = useState(false)
  const [editModel, setEditModel] = useState('')
  const [editReasoning, setEditReasoning] = useState(false)
  const [stateModel, setStateModel] = useState('')
  const [stateReasoning, setStateReasoning] = useState(false)

  useEffect(() => {
    let cancelled = false
    async function loadModels() {
      try {
        const res = await fetch('/api/v1/models')
        if (!res.ok) throw new Error(`GET /api/v1/models failed: ${res.status}`)
        const data: ModelsResponse = await res.json()
        if (cancelled) return
        setAvailableModels(data.models)
        setGenerateModel((prev) => prev || data.defaults.generate || data.models[0] || '')
        setEditModel((prev) => prev || data.defaults.edit || data.models[0] || '')
        setStateModel((prev) => prev || data.defaults.state || data.models[0] || '')
      } catch (err) {
        console.error(err)
      }
    }
    loadModels()
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    async function loadEpisodes() {
      setEpisodes(null)
      setEpisodesError(null)
      try {
        const res = await fetch(`/api/v1/novel/${novelId}/chapters`)
        if (!res.ok) throw new Error(`GET /api/v1/novel/${novelId}/chapters failed: ${res.status}`)
        const data: ChapterSummary[] = await res.json()
        if (cancelled) return
        setEpisodes(data)
        setSelectedBeatId((prev) => prev ?? (data.length > 0 ? data[data.length - 1].outline_beat_id : null))
      } catch (err) {
        console.error(err)
        if (!cancelled) setEpisodesError('Failed to load chapters.')
      }
    }
    loadEpisodes()
    return () => {
      cancelled = true
    }
  }, [novelId, locked])

  useEffect(() => {
    let cancelled = false
    async function loadChapter() {
      setSelectedChapter(null)
      setDetailError(null)
      if (!selectedBeatId) return
      const generated = chapters?.some((c) => c.outline_beat_id === selectedBeatId)
      if (!generated) return
      try {
        const res = await fetch(`/api/v1/novel/${novelId}/chapters/${selectedBeatId}`)
        if (!res.ok) throw new Error(`GET episode failed: ${res.status}`)
        const data: Episode = await res.json()
        if (!cancelled) setSelectedChapter(data)
      } catch (err) {
        console.error(err)
        if (!cancelled) setDetailError('Failed to load this chapter.')
      }
    }
    loadChapter()
    return () => {
      cancelled = true
    }
  }, [novelId, selectedBeatId, chapters])

  if (outlineBeats.length === 0) {
    return <p>No outline generated yet — chapters can't be written until the outline exists.</p>
  }
  if (!chaptersPrepared) {
    return (
      <p>
        This outline doesn't have entity-presence data yet. Regenerate the outline on the Outline
        tab before generating chapters.
      </p>
    )
  }
  if (chaptersError) return <p className="novels-error">{chaptersError}</p>
  if (chapters === null) return <p>Loading chapters...</p>

  const sortedBeats = [...outlineBeats].sort((a, b) => a.sort_order - b.sort_order)
  const generatedByBeatId = new Map(chapters.map((c) => [c.outline_beat_id, c]))
  const lastGeneratedSortOrder = chapters.length > 0 ? chapters[chapters.length - 1].sort_order : -1
  const nextBeat = sortedBeats.find((b) => b.sort_order === lastGeneratedSortOrder + 1) ?? null

  const selectedBeat = sortedBeats.find((b) => b.id === selectedBeatId) ?? null
  const selectedIsGenerated = selectedBeat ? generatedByBeatId.has(selectedBeat.id) : false
  const selectedIsLastGenerated = selectedBeat ? selectedBeat.sort_order === lastGeneratedSortOrder : false
  const selectedIsNext = selectedBeat ? selectedBeat.id === nextBeat?.id : false

  async function runPipeline(beatId: string, action: 'generate' | 'regenerate') {
    setPending(action)
    setActionError(null)
    try {
      const res = await fetch(`/api/v1/novel/${novelId}/chapters/${beatId}/${action}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          generate_model: generateModel || null,
          generate_reasoning: generateReasoning,
          edit_model: editModel || null,
          edit_reasoning: editReasoning,
          state_model: stateModel || null,
          state_reasoning: stateReasoning,
        }),
      })
      if (!res.ok) {
        const detail = await res.json().catch(() => null)
        throw new Error(detail?.detail ?? `${action} failed: ${res.status}`)
      }
      const data: Episode = await res.json()
      setSelectedChapter(data)
      setSelectedBeatId(beatId)
      const res2 = await fetch(`/api/v1/novel/${novelId}/chapters`)
      if (res2.ok) setEpisodes(await res2.json())
      if (!locked) onLockChanged()
    } catch (err) {
      console.error(err)
      setActionError(err instanceof Error ? err.message : `Failed to ${action} chapter.`)
    } finally {
      setPending(null)
    }
  }

  return (
    <div className="chapters-layout">
      {pending && (
        <CopyDialog
          title={pending === 'generate' ? 'Generating Chapter' : 'Regenerating Chapter'}
          message="Writing, editing, and updating story state..."
        />
      )}
      {confirmingRegenerate && selectedBeat && (
        <ConfirmDialog
          title="Regenerate Chapter"
          message="This replaces the current chapter's prose and story-state changes. Continue?"
          confirmLabel="Regenerate"
          onConfirm={() => {
            setConfirmingRegenerate(false)
            runPipeline(selectedBeat.id, 'regenerate')
          }}
          onCancel={() => setConfirmingRegenerate(false)}
        />
      )}

      <div className="chapters-sidebar">
        {sortedBeats.map((beat) => {
          const generated = generatedByBeatId.has(beat.id)
          return (
            <button
              key={beat.id}
              type="button"
              className="chapters-sidebar-item"
              aria-current={beat.id === selectedBeatId}
              disabled={!generated && beat.id !== nextBeat?.id}
              onClick={() => setSelectedBeatId(beat.id)}
            >
              <span className="chapters-sidebar-number">{beat.sort_order + 1}.</span>
              <span className="chapters-sidebar-title">{beat.title ?? 'Untitled'}</span>
              {generated && generatedByBeatId.get(beat.id)?.word_count != null && (
                <span className="chapters-sidebar-word-count">
                  {generatedByBeatId.get(beat.id)!.word_count!.toLocaleString()}w
                </span>
              )}
              <span className="chapters-sidebar-status">{generated ? 'done' : 'not written'}</span>
            </button>
          )
        })}
      </div>

      <div className="chapters-body">
        {!selectedBeat && <p>Select a chapter.</p>}
        {selectedBeat && !selectedIsGenerated && !selectedIsNext && (
          <p>This episode hasn't been reached yet — generate earlier chapters first.</p>
        )}
        {selectedBeat && !selectedIsGenerated && selectedIsNext && (
          <>
            <p>Episode {selectedBeat.sort_order + 1}, "{selectedBeat.title ?? 'Untitled'}", hasn't been written yet.</p>
            <ChapterPipelineModelPicker
              availableModels={availableModels}
              generateModel={generateModel}
              setGenerateModel={setGenerateModel}
              generateReasoning={generateReasoning}
              setGenerateReasoning={setGenerateReasoning}
              editModel={editModel}
              setEditModel={setEditModel}
              editReasoning={editReasoning}
              setEditReasoning={setEditReasoning}
              stateModel={stateModel}
              setStateModel={setStateModel}
              stateReasoning={stateReasoning}
              setStateReasoning={setStateReasoning}
            />
            {actionError && <p className="novels-error">{actionError}</p>}
            <div className="novel-character-card-actions">
              <button type="button" disabled={pending !== null} onClick={() => runPipeline(selectedBeat.id, 'generate')}>
                Generate Episode {selectedBeat.sort_order + 1}
              </button>
            </div>
          </>
        )}
        {selectedBeat && selectedIsGenerated && (
          <>
            {detailError && <p className="novels-error">{detailError}</p>}
            {!detailError && selectedEpisode === null && <p>Loading chapter...</p>}
            {selectedEpisode && (
              <>
                <h3 className="chapters-body-title">
                  Episode {selectedBeat.sort_order + 1}: {selectedBeat.title ?? 'Untitled'}
                </h3>
                {selectedChapter.word_count != null && (
                  <p className="chapters-body-word-count">{selectedChapter.word_count.toLocaleString()} words</p>
                )}
                <div className="chapters-body-prose">
                  {selectedChapter.edited_prose.split('\n\n').map((paragraph, i) => (
                    <p key={i}>{paragraph}</p>
                  ))}
                </div>
                {selectedIsLastGenerated && (
                  <>
                    <ChapterPipelineModelPicker
                      availableModels={availableModels}
                      generateModel={generateModel}
                      setGenerateModel={setGenerateModel}
                      generateReasoning={generateReasoning}
                      setGenerateReasoning={setGenerateReasoning}
                      editModel={editModel}
                      setEditModel={setEditModel}
                      editReasoning={editReasoning}
                      setEditReasoning={setEditReasoning}
                      stateModel={stateModel}
                      setStateModel={setStateModel}
                      stateReasoning={stateReasoning}
                      setStateReasoning={setStateReasoning}
                    />
                    {actionError && <p className="novels-error">{actionError}</p>}
                    <div className="novel-character-card-actions">
                      <button
                        type="button"
                        disabled={pending !== null}
                        onClick={() => setConfirmingRegenerate(true)}
                      >
                        Regenerate
                      </button>
                      {nextBeat && (
                        <button
                          type="button"
                          disabled={pending !== null}
                          onClick={() => runPipeline(nextBeat.id, 'generate')}
                        >
                          Generate Next Chapter
                        </button>
                      )}
                    </div>
                  </>
                )}
              </>
            )}
          </>
        )}
      </div>
    </div>
  )
}

export default Episodes
