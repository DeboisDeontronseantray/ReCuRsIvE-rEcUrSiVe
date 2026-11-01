import { useEffect, useState, type DetailedHTMLProps, type HTMLAttributes } from 'react'

// <marquee> still works in every browser but isn't in React's JSX typings.
type MarqueeProps = DetailedHTMLProps<HTMLAttributes<HTMLElement>, HTMLElement> & {
  scrollamount?: string
}
const Marquee = 'marquee' as unknown as (props: MarqueeProps) => React.JSX.Element

function Home() {
  const [hitCount, setHitCount] = useState(1337)

  useEffect(() => {
    const interval = setInterval(() => {
      setHitCount((n) => n + Math.floor(Math.random() * 3))
    }, 1500)
    return () => clearInterval(interval)
  }, [])

  const hitDigits = String(hitCount).padStart(6, '0').split('')

  return (
    <div className="home-page">
      <Marquee className="home-marquee" scrollamount="6">
        *** WELCOME TO AI SLOP NOVELS *** THE #1 SITE FOR MACHINE-GENERATED
        LITERATURE ON THE INFORMATION SUPERHIGHWAY *** BEST VIEWED IN
        NETSCAPE NAVIGATOR AT 800x600 *** NO REFUNDS ***
      </Marquee>

      <h1 className="home-title">
        <span className="rainbow-text">AI SLOP NOVELS</span>
      </h1>
      <p className="home-subtitle blink">*** KTVM 4 seasons & episodes — TV-safe Story Bot ***</p>

      <table className="home-layout-table">
        <tbody>
          <tr>
            <td className="home-sidebar-cell">
              <div className="home-badge-stack">
                <div className="home-badge home-badge-new">
                  <div className="blink">☆ NEW! ☆</div>
                </div>
                <div className="home-badge home-badge-hot">
                  <div className="blink">🔥 HOT!! 🔥</div>
                </div>
                <div className="home-badge home-badge-award">
                  <div>🏆</div>
                  <div>SITE OF<br />THE DAY</div>
                </div>
                <div className="home-under-construction">
                  <div className="blink">🚧 UNDER CONSTRUCTION 🚧</div>
                  <div>Please pardon our dust while<br />the robots keep writing.</div>
                </div>
              </div>
            </td>

            <td className="home-main-cell">
              <div className="home-panel">
                <p>
                  Tired of writing your own novels?? Sick of "editing" and "plot
                  coherence"?? Well friend, have we got GREAT NEWS for you!!
                </p>
                <p>
                  <strong>AI Slop Novels</strong> harnesses the awesome power of
                  Artificial Intelligence to generate full-length novels while YOU
                  sit back and relax!! Just type in a title and a premise and
                  watch the MAGIC happen right before your eyes!
                </p>
                <p className="blink" style={{ color: '#ff00ff', fontWeight: 'bold' }}>
                  ⚡ NO WRITING EXPERIENCE REQUIRED ⚡
                </p>
              </div>

              <div className="home-panel home-features">
                <h2>WHY CHOOSE US???</h2>
                <ul>
                  <li>✅ Lightning-fast novel generation!</li>
                  <li>✅ Titles AND premises, expanded by REAL artificial intelligence!</li>
                  <li>✅ Works on any computer with a web browser!</li>
                  <li>✅ 100% Certified Slop, Guaranteed!</li>
                  <li>✅ No annoying popups!! (this statement may not be accurate)</li>
                </ul>
              </div>

              <div className="home-panel home-cta">
                <p>
                  What are you waiting for?! Click on <strong>Seasons</strong> in
                  the sidebar to the left and start generating your very own
                  slop novel TODAY!
                </p>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <hr className="home-hr" />

      <div className="home-counter-row">
        <span>YOU ARE VISITOR NUMBER:</span>
        <span className="home-counter">
          {hitDigits.map((digit, i) => (
            <span key={i} className="home-counter-digit">{digit}</span>
          ))}
        </span>
      </div>

      <p className="home-footer-note">
        This page is best viewed at 800x600 resolution. © 1998-2026 AI Slop
        Novels Inc. All rights reserved. Do not steal.
      </p>

      <div className="home-webring">
        <span>◄◄ PREV</span>
        <span className="blink">⭐ SLOP-O-RAMA WEBRING ⭐</span>
        <span>NEXT ►►</span>
      </div>
    </div>
  )
}

export default Home
