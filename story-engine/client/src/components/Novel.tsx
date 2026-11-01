import { useEffect, useState } from 'react'
import AutoGrowTextarea from './AutoGrowTextarea'
import Episodes from './Episodes'
import CopyDialog from './CopyDialog'
import EntityCard from './EntityCard'
import Prompts from './Prompts'

interface NovelDetail {
  id: string
  prompt: string
  title: string
  summary: string | null
  author: string | null
  word_count: number | null
  premise: string
  primary_genre: string | null
  region: string | null
  character_seeds: { name: string; notes: string }[]
  sub_genres: string[]
  genre_conventions: { genre: string; convention: string; type: 'common' | 'deep_cut' }[]
  tone: string | null
  themes: string[]
  spice_level: string | null  // legacy; prefer none
  literary_voice: string | null
  tense: string | null
  perspective: string | null
  forbidden_element: string | null
  tone_notes: string | null
  characters_notes: string | null
  worldbuilding_notes: string | null
  character_generation_notes: string | null
  primary_thread: string | null
  // romance_content removed from UI
  primary_word_count: number | null
  metadata_model: string | null
  genre_conventions_model: string | null
  characters_model: string | null
  worldbuilding_model: string | null
  primary_thread_model: string | null
  secondary_arcs_model: string | null
  outline_model: string | null
  outline_audit_model: string | null
  entities_model: string | null
  initial_state_model: string | null
  metadata_reasoning: boolean
  genre_conventions_reasoning: boolean
  characters_reasoning: boolean
  worldbuilding_reasoning: boolean
  primary_thread_reasoning: boolean
  secondary_arcs_reasoning: boolean
  outline_reasoning: boolean
  outline_audit_reasoning: boolean
  entities_reasoning: boolean
  initial_state_reasoning: boolean
  locked: boolean
  locked_at: string | null
}

interface SecondaryThread {
  id: string
  novel_id: string
  description: string
  length: number
  priority: number
  heat: number
  word_count: number | null
}

interface WorldbuildingFact {
  id: string
  novel_id: string
  sort_order: number
  category: string
  title: string | null
  description: string | null
}

interface Worldbuilding {
  id: string
  novel_id: string
  story_type: string | null
  time_period: string | null
  anchor_location: string | null
  anchor_location_description: string | null
  facts: WorldbuildingFact[]
}

interface OutlineBeat {
  id: string
  novel_id: string
  sort_order: number
  content: string
  word_count: number | null
  title: string | null
  pov_character: string | null
  pov_voice_note: string | null
  tone: string | null
  characters_present: string[]
  items_present: string[]
  locations_present: string[]
  groups_present: string[]
  worldbuilding_facts_present: string[]
}

interface Character {
  id: string
  novel_id: string
  name: string
  role: string | null
  age: number | null
  gender: string | null
  sexuality: string | null
  occupation: string | null
  appearance: string | null
  physical_characteristics: string[]
  personality: string[]
  backstory: string | null
  fears: string[]
  flaws: string[]
  contradictions: string[]
  hobbies: string[]
  spiritual_beliefs: string[]
  character_voice: string[]
  speech_patterns: string[]
}

interface Location {
  id: string
  novel_id: string
  name: string
  description: string | null
}

interface Item {
  id: string
  novel_id: string
  name: string
  description: string | null
}

interface Group {
  id: string
  novel_id: string
  name: string
  description: string | null
  associated_characters: string[]
}

interface StoryEvent {
  id: string
  novel_id: string
  title: string
  description: string | null
  characters_involved: string[]
  groups_involved: string[]
}

interface NovelProps {
  name: string
  onNovelCreated: () => void
  onSelectNovel: (id: string | null) => void
}

const TABS = ['Prompts', 'Metadata', 'Worldbuilding', 'Characters', 'Outline', 'Locations', 'Items', 'Groups', 'Events', 'Episodes'] as const
type Tab = (typeof TABS)[number]

// Display order for the world fact categories; mirrors the generation prompt.
const WORLDBUILDING_CATEGORIES = [
  'society',
  'physical',
  'systems',
  'relationships',
  'conflict',
  'history',
  'daily_life',
  'beliefs',
] as const

function Novel({ name: id, onNovelCreated, onSelectNovel }: NovelProps) {
  const [novel, setNovel] = useState<NovelDetail | null>(null)
  const [saved, setSavedNovel] = useState<NovelDetail | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [justSaved, setJustSaved] = useState(false)
  const [activeTab, setActiveTab] = useState<Tab>('Prompts')
  // Bumped after a "Regenerate from here" (Worldbuilding/Outline) succeeds —
  // included in the load-everything effect's deps below so it re-fetches
  // whatever tabs the cascade touched, without hoisting those load functions
  // out of the effect.
  const [refreshKey, setRefreshKey] = useState(0)

  const [secondaryThreads, setSecondaryThreads] = useState<SecondaryThread[] | null>(null)

  const [characters, setCharacters] = useState<Character[] | null>(null)
  const [charactersError, setCharactersError] = useState<string | null>(null)

  const [worldbuilding, setWorldbuilding] = useState<Worldbuilding | null>(null)
  const [worldbuildingError, setWorldbuildingError] = useState<string | null>(null)
  const [savedWorldbuilding, setSavedWorldbuilding] = useState<Worldbuilding | null>(null)
  const [savingWorldbuilding, setSavingWorldbuilding] = useState(false)
  const [worldbuildingSaveError, setWorldbuildingSaveError] = useState<string | null>(null)
  const [worldbuildingJustSaved, setWorldbuildingJustSaved] = useState(false)

  const [outline, setOutline] = useState<OutlineBeat[] | null>(null)
  const [outlineError, setOutlineError] = useState<string | null>(null)

  const [locations, setLocations] = useState<Location[] | null>(null)
  const [items, setItems] = useState<Item[] | null>(null)
  const [groups, setGroups] = useState<Group[] | null>(null)
  const [events, setEvents] = useState<StoryEvent[] | null>(null)
  const [worldError, setWorldError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function loadNovel() {
      setNovel(null)
      setSavedNovel(null)
      setError(null)
      try {
        const res = await fetch(`/api/v1/novel/${id}`)
        if (!res.ok) throw new Error(`GET /api/v1/novel/${id} failed: ${res.status}`)
        const data = await res.json()
        if (!cancelled) {
          setNovel(data)
          setSavedNovel(data)
        }
      } catch (err) {
        console.error(err)
        if (!cancelled) setError('Failed to load novel.')
      }
    }

    async function loadSecondaryThreads() {
      setSecondaryThreads(null)
      try {
        const res = await fetch(`/api/v1/novel/${id}/secondary-threads`)
        if (!res.ok) throw new Error(`GET /api/v1/novel/${id}/secondary-threads failed: ${res.status}`)
        const data = await res.json()
        if (!cancelled) setSecondaryThreads(data)
      } catch (err) {
        console.error(err)
      }
    }

    async function loadCharacters() {
      setCharacters(null)
      setCharactersError(null)
      try {
        const res = await fetch(`/api/v1/novel/${id}/characters`)
        if (!res.ok) throw new Error(`GET /api/v1/novel/${id}/characters failed: ${res.status}`)
        const data = await res.json()
        if (!cancelled) setCharacters(data)
      } catch (err) {
        console.error(err)
        if (!cancelled) setCharactersError('Failed to load characters.')
      }
    }

    async function loadWorldbuilding() {
      setWorldbuilding(null)
      setWorldbuildingError(null)
      try {
        const res = await fetch(`/api/v1/novel/${id}/worldbuilding`)
        // 404 just means this novel predates the worldbuilding step.
        if (res.status === 404) return
        if (!res.ok) throw new Error(`GET /api/v1/novel/${id}/worldbuilding failed: ${res.status}`)
        const data = await res.json()
        if (!cancelled) {
          setWorldbuilding(data)
          setSavedWorldbuilding(data)
        }
      } catch (err) {
        console.error(err)
        if (!cancelled) setWorldbuildingError('Failed to load worldbuilding.')
      }
    }

    async function loadOutline() {
      setOutline(null)
      setOutlineError(null)
      try {
        const res = await fetch(`/api/v1/novel/${id}/outline`)
        if (!res.ok) throw new Error(`GET /api/v1/novel/${id}/outline failed: ${res.status}`)
        const data = await res.json()
        if (!cancelled) setOutline(data)
      } catch (err) {
        console.error(err)
        if (!cancelled) setOutlineError('Failed to load outline.')
      }
    }

    async function loadWorld() {
      setLocations(null)
      setItems(null)
      setGroups(null)
      setEvents(null)
      setWorldError(null)
      try {
        const [locationsRes, itemsRes, groupsRes, eventsRes] = await Promise.all([
          fetch(`/api/v1/novel/${id}/locations`),
          fetch(`/api/v1/novel/${id}/items`),
          fetch(`/api/v1/novel/${id}/groups`),
          fetch(`/api/v1/novel/${id}/events`),
        ])
        if (!locationsRes.ok || !itemsRes.ok || !groupsRes.ok || !eventsRes.ok) {
          throw new Error(`GET /api/v1/novel/${id}/{locations,items,groups,events} failed`)
        }
        const [locationsData, itemsData, groupsData, eventsData] = await Promise.all([
          locationsRes.json(),
          itemsRes.json(),
          groupsRes.json(),
          eventsRes.json(),
        ])
        if (!cancelled) {
          setLocations(locationsData)
          setItems(itemsData)
          setGroups(groupsData)
          setEvents(eventsData)
        }
      } catch (err) {
        console.error(err)
        if (!cancelled) setWorldError('Failed to load worldbuilding.')
      }
    }

    loadNovel()
    loadSecondaryThreads()
    loadWorldbuilding()
    loadCharacters()
    loadOutline()
    loadWorld()
    return () => {
      cancelled = true
    }
  }, [id, refreshKey])

  function updateField<K extends keyof NovelDetail>(field: K, value: NovelDetail[K]) {
    setNovel((prev) => (prev ? { ...prev, [field]: value } : prev))
    setJustSaved(false)
  }

  const isDirty = novel != null && saved != null && JSON.stringify(novel) !== JSON.stringify(saved)

  // Re-runs only the outline step. Everything upstream (characters, worldbuilding,
  // spine, entities) is reused as-is, so a failure here leaves the novel intact.
  // Core worldbuilding fields only — the facts save individually via EntityCard.
  const worldbuildingDirty =
    worldbuilding != null &&
    savedWorldbuilding != null &&
    (worldbuilding.story_type !== savedWorldbuilding.story_type ||
      worldbuilding.time_period !== savedWorldbuilding.time_period ||
      worldbuilding.anchor_location !== savedWorldbuilding.anchor_location ||
      worldbuilding.anchor_location_description !==
        savedWorldbuilding.anchor_location_description)

  function updateWorldbuildingField<K extends keyof Worldbuilding>(
    field: K,
    value: Worldbuilding[K],
  ) {
    setWorldbuilding((prev) => (prev ? { ...prev, [field]: value } : prev))
    setWorldbuildingJustSaved(false)
  }

  async function handleWorldbuildingSubmit() {
    if (!worldbuilding || !worldbuildingDirty) return
    setSavingWorldbuilding(true)
    setWorldbuildingSaveError(null)
    setWorldbuildingJustSaved(false)
    try {
      const res = await fetch(`/api/v1/novel/${id}/worldbuilding`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          story_type: worldbuilding.story_type,
          time_period: worldbuilding.time_period,
          anchor_location: worldbuilding.anchor_location,
          anchor_location_description: worldbuilding.anchor_location_description,
        }),
      })
      if (!res.ok) throw new Error(`PATCH worldbuilding failed: ${res.status}`)
      const data = await res.json()
      setWorldbuilding(data)
      setSavedWorldbuilding(data)
      setWorldbuildingJustSaved(true)
    } catch (err) {
      console.error(err)
      setWorldbuildingSaveError('Failed to save. Please try again.')
    } finally {
      setSavingWorldbuilding(false)
    }
  }

  async function handleSubmit() {
    if (!novel || !isDirty) return

    setSaving(true)
    setSaveError(null)
    setJustSaved(false)
    try {
      const res = await fetch(`/api/v1/novel/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: novel.title,
          summary: novel.summary,
          author: novel.author,
          premise: novel.premise,
          primary_genre: novel.primary_genre,
          sub_genres: novel.sub_genres,
          tone: novel.tone,
          themes: novel.themes,
          spice_level: novel.spice_level,
          literary_voice: novel.literary_voice,
          tense: novel.tense,
          perspective: novel.perspective,
          forbidden_element: novel.forbidden_element,
        }),
      })
      if (!res.ok) throw new Error(`PATCH /api/v1/novel/${id} failed: ${res.status}`)
      const data = await res.json()
      setNovel(data)
      setSavedNovel(data)
      setJustSaved(true)
    } catch (err) {
      console.error(err)
      setSaveError('Failed to save changes. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  if (error) return <p className="novels-error">{error}</p>
  if (!novel) return <p>Loading novel...</p>

  return (
    <div className="novel-detail">
      {saving && <CopyDialog title="Updating Novel" message="Saving your changes..." />}

      <menu role="tablist" className="multirows novel-detail-tabs">
        {TABS.map((tab) => (
          <li key={tab} role="tab" aria-selected={activeTab === tab}>
            <a
              href={`#${tab}`}
              onClick={(e) => {
                e.preventDefault()
                setActiveTab(tab)
              }}
            >
              {tab}
            </a>
          </li>
        ))}
      </menu>

      <div className="window" role="tabpanel">
        <div className="window-body novel-detail-tabpanel-body">
          {activeTab === 'Metadata' && (
            <>
              <div className="novel-field">
                <label htmlFor="field-title">Title</label>
                <input
                  id="field-title"
                  type="text"
                  value={novel.title}
                  onChange={(e) => updateField('title', e.target.value)}
                />
              </div>

              <div className="novel-field">
                <label htmlFor="field-summary">Summary</label>
                <AutoGrowTextarea
                  id="field-summary"
                  value={novel.summary ?? ''}
                  onChange={(e) => updateField('summary', e.target.value)}
                />
              </div>

              <div className="novel-field">
                <label htmlFor="field-author">Author</label>
                <input
                  id="field-author"
                  type="text"
                  value={novel.author ?? ''}
                  onChange={(e) => updateField('author', e.target.value)}
                />
              </div>

              <div className="novel-field">
                <label htmlFor="field-genre">Genre</label>
                <input
                  id="field-genre"
                  type="text"
                  value={novel.primary_genre ?? ''}
                  onChange={(e) => updateField('primary_genre', e.target.value)}
                />
              </div>

              <div className="novel-field">
                <label htmlFor="field-sub-genres">Sub-genres</label>
                <input
                  id="field-sub-genres"
                  type="text"
                  value={novel.sub_genres.join(', ')}
                  onChange={(e) =>
                    updateField(
                      'sub_genres',
                      e.target.value
                        .split(',')
                        .map((s) => s.trim())
                        .filter(Boolean),
                    )
                  }
                />
              </div>

              <div className="novel-field">
                <label htmlFor="field-tone">Tone</label>
                <input
                  id="field-tone"
                  type="text"
                  value={novel.tone ?? ''}
                  onChange={(e) => updateField('tone', e.target.value)}
                />
              </div>

              <div className="novel-field">
                <label htmlFor="field-themes">Themes</label>
                <input
                  id="field-themes"
                  type="text"
                  value={novel.themes.join(', ')}
                  onChange={(e) =>
                    updateField(
                      'themes',
                      e.target.value
                        .split(',')
                        .map((s) => s.trim())
                        .filter(Boolean),
                    )
                  }
                />
              </div>

              <div className="novel-field">
                <label htmlFor="field-spice">Spice Level</label>
                <select
                  id="field-spice"
                  value={novel.spice_level ?? ''}
                  onChange={(e) => updateField('spice_level', e.target.value)}
                >
                  <option value="">—</option>
                  <option value="low">low</option>
                  <option value="medium">medium</option>
                  <option value="high">high</option>
                  <option value="none">none (TV-safe)</option>
                </select>
              </div>

              <div className="novel-field">
                <label htmlFor="field-voice">Literary Voice</label>
                <input
                  id="field-voice"
                  type="text"
                  value={novel.literary_voice ?? ''}
                  onChange={(e) => updateField('literary_voice', e.target.value)}
                />
              </div>

              <div className="novel-field">
                <label htmlFor="field-tense">Tense</label>
                <select
                  id="field-tense"
                  value={novel.tense ?? ''}
                  onChange={(e) => updateField('tense', e.target.value)}
                >
                  <option value="">—</option>
                  <option value="past">past</option>
                  <option value="present">present</option>
                </select>
              </div>

              <div className="novel-field">
                <label htmlFor="field-perspective">Perspective</label>
                <select
                  id="field-perspective"
                  value={novel.perspective ?? ''}
                  onChange={(e) => updateField('perspective', e.target.value)}
                >
                  <option value="">—</option>
                  <option value="first_person">first_person</option>
                  <option value="third_person_limited">third_person_limited</option>
                  <option value="third_person_omniscient">third_person_omniscient</option>
                </select>
              </div>

              <div className="novel-field">
                <label htmlFor="field-forbidden">Forbidden Element</label>
                <AutoGrowTextarea
                  id="field-forbidden"
                  value={novel.forbidden_element ?? ''}
                  onChange={(e) => updateField('forbidden_element', e.target.value)}
                />
              </div>

              <div className="novel-field">
                <label htmlFor="field-primary-word-count">Primary Word Count</label>
                <input
                  id="field-primary-word-count"
                  type="text"
                  readOnly
                  value={
                    novel.primary_word_count != null
                      ? `${novel.primary_word_count} words (total target minus the secondary threads' share)`
                      : 'Not yet generated'
                  }
                />
              </div>

              <div className="novel-character-card-actions">
                {saveError && <span className="novels-error">{saveError}</span>}
                {justSaved && !saveError && <span className="novel-detail-saved">Saved.</span>}
                <button type="button" disabled={saving || !isDirty || novel.locked} onClick={handleSubmit}>
                  {saving ? 'Saving...' : 'Update'}
                </button>
              </div>
            </>
          )}

          {activeTab === 'Prompts' && (
            <Prompts
              novelId={id}
              title={novel.title}
              wordCount={novel.word_count ?? 20000}
              premise={novel.premise}
              toneNotes={novel.tone_notes ?? ''}
              charactersNotes={novel.characters_notes ?? ''}
              worldbuildingNotes={novel.worldbuilding_notes ?? ''}
              characterGenerationNotes={novel.character_generation_notes ?? ''}
              primaryThread={novel.primary_thread ?? ''}
              secondaryThreads={(secondaryThreads ?? []).map((t) => ({
                description: t.description,
                length: t.length,
                priority: t.priority,
                heat: t.heat,
              }))}
              primaryGenre={novel.primary_genre ?? ''}
              region={novel.region ?? 'Italy'}
              characterSeeds={novel.character_seeds ?? []}
              author={novel.author ?? ''}
              themes={novel.themes.join(', ')}
              metadataModel={novel.metadata_model ?? ''}
              genreConventionsModel={novel.genre_conventions_model ?? ''}
              charactersModel={novel.characters_model ?? ''}
              worldbuildingModel={novel.worldbuilding_model ?? ''}
              primaryThreadModel={novel.primary_thread_model ?? ''}
              secondaryArcsModel={novel.secondary_arcs_model ?? ''}
              outlineModel={novel.outline_model ?? ''}
              outlineAuditModel={novel.outline_audit_model ?? ''}
              entitiesModel={novel.entities_model ?? ''}
              initialStateModel={novel.initial_state_model ?? ''}
              metadataReasoning={novel.metadata_reasoning}
              genreConventionsReasoning={novel.genre_conventions_reasoning}
              charactersReasoning={novel.characters_reasoning}
              worldbuildingReasoning={novel.worldbuilding_reasoning}
              primaryThreadReasoning={novel.primary_thread_reasoning}
              secondaryArcsReasoning={novel.secondary_arcs_reasoning}
              outlineReasoning={novel.outline_reasoning}
              outlineAuditReasoning={novel.outline_audit_reasoning}
              entitiesReasoning={novel.entities_reasoning}
              initialStateReasoning={novel.initial_state_reasoning}
              onRegenerated={(newId) => {
                onNovelCreated()
                onSelectNovel(newId)
              }}
              onStepRegenerated={(step) => {
                setRefreshKey((k) => k + 1)
                setActiveTab(step === 'worldbuilding' ? 'Worldbuilding' : 'Outline')
              }}
            />
          )}

          {activeTab === 'Worldbuilding' && (
            <>
              {worldbuildingError && <p className="novels-error">{worldbuildingError}</p>}
              {!worldbuildingError && worldbuilding === null && (
                <p>No worldbuilding generated yet.</p>
              )}
              {!worldbuildingError && worldbuilding !== null && (
                <>
                  <div className="novel-field">
                    <label htmlFor="wb-story-type">Story Type</label>
                    <input
                      id="wb-story-type"
                      type="text"
                      value={worldbuilding.story_type ?? ''}
                      onChange={(e) => updateWorldbuildingField('story_type', e.target.value)}
                    />
                  </div>

                  <div className="novel-field">
                    <label htmlFor="wb-time-period">Time Period</label>
                    <input
                      id="wb-time-period"
                      type="text"
                      value={worldbuilding.time_period ?? ''}
                      onChange={(e) => updateWorldbuildingField('time_period', e.target.value)}
                    />
                  </div>

                  <div className="novel-field">
                    <label htmlFor="wb-anchor-location">Anchor Location</label>
                    <input
                      id="wb-anchor-location"
                      type="text"
                      value={worldbuilding.anchor_location ?? ''}
                      onChange={(e) => updateWorldbuildingField('anchor_location', e.target.value)}
                    />
                  </div>

                  <div className="novel-field">
                    <label htmlFor="wb-anchor-description">Anchor Location Description</label>
                    <AutoGrowTextarea
                      id="wb-anchor-description"
                      value={worldbuilding.anchor_location_description ?? ''}
                      onChange={(e) =>
                        updateWorldbuildingField('anchor_location_description', e.target.value)
                      }
                    />
                  </div>

                  <div className="novel-character-card-actions">
                    {worldbuildingSaveError && (
                      <span className="novels-error">{worldbuildingSaveError}</span>
                    )}
                    {worldbuildingJustSaved && !worldbuildingSaveError && (
                      <span className="novel-detail-saved">Saved.</span>
                    )}
                    <button
                      type="button"
                      disabled={savingWorldbuilding || !worldbuildingDirty || novel.locked}
                      onClick={handleWorldbuildingSubmit}
                    >
                      {savingWorldbuilding ? 'Saving...' : 'Update'}
                    </button>
                  </div>

                  {WORLDBUILDING_CATEGORIES.map((category) => {
                    const facts = worldbuilding.facts.filter((f) => f.category === category)
                    if (facts.length === 0) return null
                    return (
                      <div key={category}>
                        <h3 className="novel-worldbuilding-category">
                          {category.replace('_', ' ')}
                        </h3>
                        <div className="novel-characters-list">
                          {facts.map((fact) => (
                            <EntityCard
                              key={fact.id}
                              readOnly={novel.locked}
                              entity={fact}
                              patchUrl={`/api/v1/novel/${id}/worldbuilding-facts/${fact.id}`}
                              onSaved={(updated) =>
                                setWorldbuilding((prev) =>
                                  prev
                                    ? {
                                        ...prev,
                                        facts: prev.facts.map((f) =>
                                          f.id === updated.id ? updated : f,
                                        ),
                                      }
                                    : prev,
                                )
                              }
                              renderFields={(draft, updateField) => (
                                <>
                                  <div className="novel-field">
                                    <label htmlFor={`fact-title-${draft.id}`}>Title</label>
                                    <input
                                      id={`fact-title-${draft.id}`}
                                      type="text"
                                      value={draft.title ?? ''}
                                      onChange={(e) => updateField('title', e.target.value)}
                                    />
                                  </div>
                                  <div className="novel-field">
                                    <label htmlFor={`fact-description-${draft.id}`}>
                                      Description
                                    </label>
                                    <AutoGrowTextarea
                                      id={`fact-description-${draft.id}`}
                                      value={draft.description ?? ''}
                                      onChange={(e) => updateField('description', e.target.value)}
                                    />
                                  </div>
                                </>
                              )}
                            />
                          ))}
                        </div>
                      </div>
                    )
                  })}

                  {novel.genre_conventions.length > 0 && (
                    <>
                      <h3 className="novel-worldbuilding-category">Genre Conventions</h3>
                      {Array.from(new Set(novel.genre_conventions.map((c) => c.genre))).map((genre) => (
                        <div key={genre}>
                          <h4 className="novel-genre-conventions-genre">{genre}</h4>
                          <ul className="novel-genre-conventions-list">
                            {novel.genre_conventions
                              .filter((c) => c.genre === genre)
                              .map((c, i) => (
                                <li key={i}>
                                  <span
                                    className={`novel-genre-convention-type novel-genre-convention-type--${c.type}`}
                                  >
                                    {c.type === 'common' ? 'Common' : 'Deep Cut'}
                                  </span>{' '}
                                  {c.convention}
                                </li>
                              ))}
                          </ul>
                        </div>
                      ))}
                    </>
                  )}
                </>
              )}
            </>
          )}

          {activeTab === 'Characters' && (
            <>
              {charactersError && <p className="novels-error">{charactersError}</p>}
              {!charactersError && characters === null && <p>Loading characters...</p>}
              {!charactersError && characters !== null && characters.length === 0 && (
                <p>No characters generated yet.</p>
              )}
              {!charactersError && characters !== null && characters.length > 0 && (
                <div className="novel-characters-list">
                  {characters.map((character) => (
                    <EntityCard
                      key={character.id}
                      readOnly={novel.locked}
                      entity={character}
                      patchUrl={`/api/v1/novel/${id}/characters/${character.id}`}
                      onSaved={(updated) =>
                        setCharacters((prev) =>
                          prev ? prev.map((c) => (c.id === updated.id ? updated : c)) : prev,
                        )
                      }
                      renderFields={(draft, updateField) => {
                        const updateListField = (
                          field: 'physical_characteristics' | 'personality' | 'fears' | 'flaws' |
                            'contradictions' | 'hobbies' | 'spiritual_beliefs' | 'character_voice' |
                            'speech_patterns',
                          value: string,
                        ) =>
                          updateField(
                            field,
                            value
                              .split(',')
                              .map((s) => s.trim())
                              .filter(Boolean),
                          )
                        return (
                          <>
                            <div className="novel-field">
                              <label htmlFor={`char-name-${draft.id}`}>Name</label>
                              <input
                                id={`char-name-${draft.id}`}
                                type="text"
                                value={draft.name}
                                onChange={(e) => updateField('name', e.target.value)}
                              />
                            </div>
                            <div className="novel-field">
                              <label htmlFor={`char-role-${draft.id}`}>Role</label>
                              <input
                                id={`char-role-${draft.id}`}
                                type="text"
                                value={draft.role ?? ''}
                                onChange={(e) => updateField('role', e.target.value)}
                              />
                            </div>
                            <div className="novel-field">
                              <label htmlFor={`char-age-${draft.id}`}>Age</label>
                              <input
                                id={`char-age-${draft.id}`}
                                type="number"
                                value={draft.age ?? ''}
                                onChange={(e) =>
                                  updateField('age', e.target.value === '' ? null : Number(e.target.value))
                                }
                              />
                            </div>
                            <div className="novel-field">
                              <label htmlFor={`char-gender-${draft.id}`}>Gender</label>
                              <input
                                id={`char-gender-${draft.id}`}
                                type="text"
                                value={draft.gender ?? ''}
                                onChange={(e) => updateField('gender', e.target.value)}
                              />
                            </div>
                            <div className="novel-field">
                              <label htmlFor={`char-sexuality-${draft.id}`}>Sexuality</label>
                              <input
                                id={`char-sexuality-${draft.id}`}
                                type="text"
                                value={draft.sexuality ?? ''}
                                onChange={(e) => updateField('sexuality', e.target.value)}
                              />
                            </div>
                            <div className="novel-field">
                              <label htmlFor={`char-occupation-${draft.id}`}>Occupation</label>
                              <input
                                id={`char-occupation-${draft.id}`}
                                type="text"
                                value={draft.occupation ?? ''}
                                onChange={(e) => updateField('occupation', e.target.value)}
                              />
                            </div>
                            <div className="novel-field">
                              <label htmlFor={`char-appearance-${draft.id}`}>Appearance</label>
                              <AutoGrowTextarea
                                id={`char-appearance-${draft.id}`}
                                value={draft.appearance ?? ''}
                                onChange={(e) => updateField('appearance', e.target.value)}
                              />
                            </div>
                            <div className="novel-field">
                              <label htmlFor={`char-physical-${draft.id}`}>
                                Physical Characteristics (comma-separated)
                              </label>
                              <AutoGrowTextarea
                                id={`char-physical-${draft.id}`}
                                value={draft.physical_characteristics.join(', ')}
                                onChange={(e) => updateListField('physical_characteristics', e.target.value)}
                              />
                            </div>
                            <div className="novel-field">
                              <label htmlFor={`char-personality-${draft.id}`}>
                                Personality (comma-separated)
                              </label>
                              <AutoGrowTextarea
                                id={`char-personality-${draft.id}`}
                                value={draft.personality.join(', ')}
                                onChange={(e) => updateListField('personality', e.target.value)}
                              />
                            </div>
                            <div className="novel-field">
                              <label htmlFor={`char-backstory-${draft.id}`}>Backstory</label>
                              <AutoGrowTextarea
                                id={`char-backstory-${draft.id}`}
                                value={draft.backstory ?? ''}
                                onChange={(e) => updateField('backstory', e.target.value)}
                              />
                            </div>
                            <div className="novel-field">
                              <label htmlFor={`char-fears-${draft.id}`}>Fears (comma-separated)</label>
                              <AutoGrowTextarea
                                id={`char-fears-${draft.id}`}
                                value={draft.fears.join(', ')}
                                onChange={(e) => updateListField('fears', e.target.value)}
                              />
                            </div>
                            <div className="novel-field">
                              <label htmlFor={`char-flaws-${draft.id}`}>Flaws (comma-separated)</label>
                              <AutoGrowTextarea
                                id={`char-flaws-${draft.id}`}
                                value={draft.flaws.join(', ')}
                                onChange={(e) => updateListField('flaws', e.target.value)}
                              />
                            </div>
                            <div className="novel-field">
                              <label htmlFor={`char-contradictions-${draft.id}`}>
                                Contradictions (comma-separated)
                              </label>
                              <AutoGrowTextarea
                                id={`char-contradictions-${draft.id}`}
                                value={draft.contradictions.join(', ')}
                                onChange={(e) => updateListField('contradictions', e.target.value)}
                              />
                            </div>
                            <div className="novel-field">
                              <label htmlFor={`char-hobbies-${draft.id}`}>Hobbies (comma-separated)</label>
                              <AutoGrowTextarea
                                id={`char-hobbies-${draft.id}`}
                                value={draft.hobbies.join(', ')}
                                onChange={(e) => updateListField('hobbies', e.target.value)}
                              />
                            </div>
                            <div className="novel-field">
                              <label htmlFor={`char-beliefs-${draft.id}`}>
                                Spiritual Beliefs (comma-separated)
                              </label>
                              <AutoGrowTextarea
                                id={`char-beliefs-${draft.id}`}
                                value={draft.spiritual_beliefs.join(', ')}
                                onChange={(e) => updateListField('spiritual_beliefs', e.target.value)}
                              />
                            </div>
                            <div className="novel-field">
                              <label htmlFor={`char-voice-${draft.id}`}>
                                Character Voice (comma-separated)
                              </label>
                              <AutoGrowTextarea
                                id={`char-voice-${draft.id}`}
                                value={draft.character_voice.join(', ')}
                                onChange={(e) => updateListField('character_voice', e.target.value)}
                              />
                            </div>
                            <div className="novel-field">
                              <label htmlFor={`char-speech-${draft.id}`}>
                                Speech Patterns (comma-separated)
                              </label>
                              <AutoGrowTextarea
                                id={`char-speech-${draft.id}`}
                                value={draft.speech_patterns.join(', ')}
                                onChange={(e) => updateListField('speech_patterns', e.target.value)}
                              />
                            </div>
                          </>
                        )
                      }}
                    />
                  ))}
                </div>
              )}
            </>
          )}

          {activeTab === 'Outline' && (
            <>
              {outlineError && <p className="novels-error">{outlineError}</p>}
              {!outlineError && outline === null && <p>Loading outline...</p>}
              {!outlineError && outline !== null && outline.length === 0 && (
                <p>No outline generated yet.</p>
              )}
              {!outlineError && outline !== null && outline.length > 0 && (
                <div className="novel-characters-list">
                  {outline.map((beat, index) => (
                    <EntityCard
                      key={beat.id}
                      readOnly={novel.locked}
                      entity={beat}
                      patchUrl={`/api/v1/novel/${id}/outline-beats/${beat.id}`}
                      onSaved={(updated) =>
                        setOutline((prev) =>
                          prev ? prev.map((b) => (b.id === updated.id ? updated : b)) : prev,
                        )
                      }
                      renderFields={(draft, updateField) => (
                        <>
                          <div className="novel-field">
                            <label>Episode {index + 1}</label>
                          </div>

                          <div className="novel-field">
                            <label htmlFor={`beat-title-${draft.id}`}>Title</label>
                            <input
                              id={`beat-title-${draft.id}`}
                              type="text"
                              value={draft.title ?? ''}
                              onChange={(e) => updateField('title', e.target.value)}
                            />
                          </div>

                          <div className="novel-field">
                            <label htmlFor={`beat-content-${draft.id}`}>Content</label>
                            <AutoGrowTextarea
                              id={`beat-content-${draft.id}`}
                              value={draft.content}
                              onChange={(e) => updateField('content', e.target.value)}
                            />
                          </div>

                          <div className="novel-field">
                            <label htmlFor={`beat-pov-character-${draft.id}`}>POV Character</label>
                            <input
                              id={`beat-pov-character-${draft.id}`}
                              type="text"
                              value={draft.pov_character ?? ''}
                              onChange={(e) => updateField('pov_character', e.target.value)}
                            />
                          </div>

                          <div className="novel-field">
                            <label htmlFor={`beat-pov-voice-note-${draft.id}`}>POV Voice Note</label>
                            <AutoGrowTextarea
                              id={`beat-pov-voice-note-${draft.id}`}
                              value={draft.pov_voice_note ?? ''}
                              onChange={(e) => updateField('pov_voice_note', e.target.value)}
                            />
                          </div>

                          <div className="novel-field">
                            <label htmlFor={`beat-tone-${draft.id}`}>Tone</label>
                            <input
                              id={`beat-tone-${draft.id}`}
                              type="text"
                              value={draft.tone ?? ''}
                              onChange={(e) => updateField('tone', e.target.value)}
                            />
                          </div>

                          <div className="novel-field">
                            <label htmlFor={`beat-word-count-${draft.id}`}>Estimated Word Count</label>
                            <input
                              id={`beat-word-count-${draft.id}`}
                              type="number"
                              value={draft.word_count ?? ''}
                              onChange={(e) =>
                                updateField(
                                  'word_count',
                                  e.target.value === '' ? null : Number(e.target.value),
                                )
                              }
                            />
                          </div>
                        </>
                      )}
                    />
                  ))}
                </div>
              )}
            </>
          )}

          {activeTab === 'Locations' && (
            <>
              {worldError && <p className="novels-error">{worldError}</p>}
              {!worldError && locations === null && <p>Loading locations...</p>}
              {!worldError && locations !== null && locations.length === 0 && (
                <p>No locations generated yet.</p>
              )}
              {!worldError && locations !== null && locations.length > 0 && (
                <div className="novel-characters-list">
                  {locations.map((location) => (
                    <EntityCard
                      key={location.id}
                      readOnly={novel.locked}
                      entity={location}
                      patchUrl={`/api/v1/novel/${id}/locations/${location.id}`}
                      onSaved={(updated) =>
                        setLocations((prev) =>
                          prev ? prev.map((l) => (l.id === updated.id ? updated : l)) : prev,
                        )
                      }
                      renderFields={(draft, updateField) => (
                        <>
                          <div className="novel-field">
                            <label htmlFor={`location-name-${draft.id}`}>Name</label>
                            <input
                              id={`location-name-${draft.id}`}
                              type="text"
                              value={draft.name}
                              onChange={(e) => updateField('name', e.target.value)}
                            />
                          </div>
                          <div className="novel-field">
                            <label htmlFor={`location-description-${draft.id}`}>Description</label>
                            <AutoGrowTextarea
                              id={`location-description-${draft.id}`}
                              value={draft.description ?? ''}
                              onChange={(e) => updateField('description', e.target.value)}
                            />
                          </div>
                        </>
                      )}
                    />
                  ))}
                </div>
              )}
            </>
          )}

          {activeTab === 'Items' && (
            <>
              {worldError && <p className="novels-error">{worldError}</p>}
              {!worldError && items === null && <p>Loading items...</p>}
              {!worldError && items !== null && items.length === 0 && <p>No items generated yet.</p>}
              {!worldError && items !== null && items.length > 0 && (
                <div className="novel-characters-list">
                  {items.map((item) => (
                    <EntityCard
                      key={item.id}
                      readOnly={novel.locked}
                      entity={item}
                      patchUrl={`/api/v1/novel/${id}/items/${item.id}`}
                      onSaved={(updated) =>
                        setItems((prev) =>
                          prev ? prev.map((i) => (i.id === updated.id ? updated : i)) : prev,
                        )
                      }
                      renderFields={(draft, updateField) => (
                        <>
                          <div className="novel-field">
                            <label htmlFor={`item-name-${draft.id}`}>Name</label>
                            <input
                              id={`item-name-${draft.id}`}
                              type="text"
                              value={draft.name}
                              onChange={(e) => updateField('name', e.target.value)}
                            />
                          </div>
                          <div className="novel-field">
                            <label htmlFor={`item-description-${draft.id}`}>Description</label>
                            <AutoGrowTextarea
                              id={`item-description-${draft.id}`}
                              value={draft.description ?? ''}
                              onChange={(e) => updateField('description', e.target.value)}
                            />
                          </div>
                        </>
                      )}
                    />
                  ))}
                </div>
              )}
            </>
          )}

          {activeTab === 'Groups' && (
            <>
              {worldError && <p className="novels-error">{worldError}</p>}
              {!worldError && groups === null && <p>Loading groups...</p>}
              {!worldError && groups !== null && groups.length === 0 && (
                <p>No groups generated yet.</p>
              )}
              {!worldError && groups !== null && groups.length > 0 && (
                <div className="novel-characters-list">
                  {groups.map((group) => (
                    <EntityCard
                      key={group.id}
                      readOnly={novel.locked}
                      entity={group}
                      patchUrl={`/api/v1/novel/${id}/groups/${group.id}`}
                      onSaved={(updated) =>
                        setGroups((prev) =>
                          prev ? prev.map((g) => (g.id === updated.id ? updated : g)) : prev,
                        )
                      }
                      renderFields={(draft, updateField) => (
                        <>
                          <div className="novel-field">
                            <label htmlFor={`group-name-${draft.id}`}>Name</label>
                            <input
                              id={`group-name-${draft.id}`}
                              type="text"
                              value={draft.name}
                              onChange={(e) => updateField('name', e.target.value)}
                            />
                          </div>
                          <div className="novel-field">
                            <label htmlFor={`group-description-${draft.id}`}>Description</label>
                            <AutoGrowTextarea
                              id={`group-description-${draft.id}`}
                              value={draft.description ?? ''}
                              onChange={(e) => updateField('description', e.target.value)}
                            />
                          </div>
                          <div className="novel-field">
                            <label htmlFor={`group-characters-${draft.id}`}>
                              Associated Characters
                            </label>
                            <input
                              id={`group-characters-${draft.id}`}
                              type="text"
                              value={draft.associated_characters.join(', ')}
                              onChange={(e) =>
                                updateField(
                                  'associated_characters',
                                  e.target.value
                                    .split(',')
                                    .map((s) => s.trim())
                                    .filter(Boolean),
                                )
                              }
                            />
                          </div>
                        </>
                      )}
                    />
                  ))}
                </div>
              )}
            </>
          )}

          {activeTab === 'Events' && (
            <>
              {worldError && <p className="novels-error">{worldError}</p>}
              {!worldError && events === null && <p>Loading events...</p>}
              {!worldError && events !== null && events.length === 0 && <p>No events generated yet.</p>}
              {!worldError && events !== null && events.length > 0 && (
                <div className="novel-characters-list">
                  {events.map((event) => (
                    <EntityCard
                      key={event.id}
                      readOnly={novel.locked}
                      entity={event}
                      patchUrl={`/api/v1/novel/${id}/events/${event.id}`}
                      onSaved={(updated) =>
                        setEvents((prev) =>
                          prev ? prev.map((e) => (e.id === updated.id ? updated : e)) : prev,
                        )
                      }
                      renderFields={(draft, updateField) => (
                        <>
                          <div className="novel-field">
                            <label htmlFor={`event-title-${draft.id}`}>Title</label>
                            <input
                              id={`event-title-${draft.id}`}
                              type="text"
                              value={draft.title}
                              onChange={(e) => updateField('title', e.target.value)}
                            />
                          </div>
                          <div className="novel-field">
                            <label htmlFor={`event-description-${draft.id}`}>Description</label>
                            <AutoGrowTextarea
                              id={`event-description-${draft.id}`}
                              value={draft.description ?? ''}
                              onChange={(e) => updateField('description', e.target.value)}
                            />
                          </div>
                          <div className="novel-field">
                            <label htmlFor={`event-characters-${draft.id}`}>Characters Involved</label>
                            <input
                              id={`event-characters-${draft.id}`}
                              type="text"
                              value={draft.characters_involved.join(', ')}
                              onChange={(e) =>
                                updateField(
                                  'characters_involved',
                                  e.target.value
                                    .split(',')
                                    .map((s) => s.trim())
                                    .filter(Boolean),
                                )
                              }
                            />
                          </div>
                          <div className="novel-field">
                            <label htmlFor={`event-groups-${draft.id}`}>
                              Groups Involved
                            </label>
                            <input
                              id={`event-groups-${draft.id}`}
                              type="text"
                              value={draft.groups_involved.join(', ')}
                              onChange={(e) =>
                                updateField(
                                  'groups_involved',
                                  e.target.value
                                    .split(',')
                                    .map((s) => s.trim())
                                    .filter(Boolean),
                                )
                              }
                            />
                          </div>
                        </>
                      )}
                    />
                  ))}
                </div>
              )}
            </>
          )}

          {activeTab === 'Episodes' && (
            <Episodes
              novelId={id}
              outlineBeats={outline ?? []}
              chaptersPrepared={(outline ?? []).some((b) => b.characters_present.length > 0)}
              locked={novel.locked}
              onLockChanged={() => setRefreshKey((k) => k + 1)}
            />
          )}
        </div>
      </div>
    </div>
  )
}

export default Novel
