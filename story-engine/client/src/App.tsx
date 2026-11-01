import { useEffect, useState } from "react";
import "./App.css";
import Home from "./components/Home";
import Novels from "./components/Novels";
import Pipeline from "./components/Pipeline";
import Settings from "./components/Settings";

const PAGES = {
  home: "Home",
  novels: "Seasons",
  pipeline: "Pipeline",
  settings: "Settings",
} as const;

type PageId = keyof typeof PAGES;

interface NovelSummary {
  id: string;
  title: string;
  premise: string;
}

function App() {
  const [page, setPage] = useState<PageId>("home");
  const [novels, setNovels] = useState<NovelSummary[]>([]);
  const [selectedNovel, setSelectedNovel] = useState<string | null>(null);
  const [duplicatingId, setDuplicatingId] = useState<string | null>(null);

  async function loadNovels() {
    try {
      const res = await fetch("/api/v1/novels");
      if (!res.ok) throw new Error(`GET /api/v1/novels failed: ${res.status}`);
      setNovels(await res.json());
    } catch (err) {
      console.error(err);
      setNovels([]);
    }
  }

  useEffect(() => {
    loadNovels();
  }, []);

  // Duplicates a novel 1-for-1 under a new id (server appends _1, _2, ...
  // to the title) and refreshes the sidebar list.
  async function handleDuplicate(id: string) {
    setDuplicatingId(id);
    try {
      const res = await fetch(`/api/v1/novel/${id}/duplicate`, { method: "POST" });
      if (!res.ok) throw new Error(`POST /api/v1/novel/${id}/duplicate failed: ${res.status}`);
      await loadNovels();
    } catch (err) {
      console.error(err);
    } finally {
      setDuplicatingId(null);
    }
  }

  return (
    <div className="window" id="app-window">
      <div className="title-bar">
        <div className="title-bar-text">AI Slop Novels</div>
        <div className="title-bar-controls">
          <button aria-label="Minimize"></button>
          <button aria-label="Maximize"></button>
          <button aria-label="Close"></button>
        </div>
      </div>

      <div className="window-body app-body">
        <ul className="tree-view app-nav">
          {(Object.keys(PAGES) as PageId[]).map((id) => {
            const isActive = id === page && selectedNovel === null;

            const link = (
              <a
                href={`#${id}`}
                className={isActive ? "active" : undefined}
                onClick={(e) => {
                  e.preventDefault();
                  setPage(id);
                  setSelectedNovel(null);
                }}
              >
                {PAGES[id]}
              </a>
            );

            if (id !== "novels") {
              return <li key={id}>{link}</li>;
            }

            return (
              <li key={id}>
                <details open>
                  <summary>{link}</summary>
                  <ul>
                    {novels.map((novel) => (
                      <li key={novel.id} className="novel-row">
                        <a
                          href="#novels"
                          className={
                            page === "novels" && selectedNovel === novel.id
                              ? "active"
                              : undefined
                          }
                          onClick={(e) => {
                            e.preventDefault();
                            setPage("novels");
                            setSelectedNovel(novel.id);
                          }}
                        >
                          {novel.title}
                        </a>
                        <button
                          type="button"
                          className="novel-duplicate-btn"
                          title="Duplicate novel"
                          aria-label={`Duplicate ${novel.title}`}
                          disabled={duplicatingId === novel.id}
                          onClick={(e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            handleDuplicate(novel.id);
                          }}
                        >
                          <span
                            className={
                              duplicatingId === novel.id
                                ? "novel-duplicate-icon spinning"
                                : "novel-duplicate-icon"
                            }
                          >
                            ⧉
                          </span>
                        </button>
                      </li>
                    ))}
                  </ul>
                </details>
              </li>
            );
          })}
        </ul>

        <div className="app-content">
          {page === "home" && <Home />}
          {page === "novels" && (
            <Novels
              selectedNovel={selectedNovel}
              onSelectNovel={setSelectedNovel}
              onNovelCreated={loadNovels}
            />
          )}
          {page === "pipeline" && <Pipeline />}
          {page === "settings" && <Settings />}
        </div>
      </div>

      <div className="status-bar">
        <p className="status-bar-field">Ready</p>
        <p className="status-bar-field">CPU Usage: 67%</p>
      </div>
    </div>
  );
}

export default App;
