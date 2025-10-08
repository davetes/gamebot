import React, { useEffect, useMemo, useState } from 'react'
import './play.css'

function useQuery() {
  return useMemo(() => new URLSearchParams(window.location.search), [])
}

function initTelegram() {
  const tg = window?.Telegram?.WebApp
  if (!tg) return null
  try {
    tg.ready()
    tg.expand()
    tg.enableClosingConfirmation()
    tg.MainButton.setParams({
      text: 'Refresh',
      is_visible: true,
    })
  } catch {}
  return tg
}

export default function Play() {
  const q = useQuery()
  const stake = q.get('stake') ?? '10'
  const [active, setActive] = useState(new Set())
  const [gameId] = useState(() => Math.floor(100000 + Math.random() * 900000))
  const [activeGame] = useState(1)
  const [preview, setPreview] = useState(null) // number or null

  useEffect(() => {
    const tg = initTelegram()
    if (!tg) return
    const onMain = () => window.location.reload()
    tg.MainButton.onClick(onMain)
    return () => tg.MainButton.offClick(onMain)
  }, [])

  // Ensure body doesn't center content (override Vite template styles)
  useEffect(() => {
    document.body.classList.add('play-mode')
    return () => document.body.classList.remove('play-mode')
  }, [])

  const toggle = (n) => {
    setActive(prev => {
      const next = new Set(prev)
      if (next.has(n)) next.delete(n)
      else next.add(n)
      return next
    })
  }

  // Build a deterministic 5x5 bingo-like card from a seed (the clicked number)
  const buildCard = (seed) => {
    if (!seed) return []
    // Classic B I N G O column ranges
    const ranges = [
      [1, 15],   // B
      [16, 30],  // I
      [31, 45],  // N
      [46, 60],  // G
      [61, 75],  // O
    ]
    const columns = ranges.map(([start, end], idx) => {
      const size = end - start + 1
      const arr = Array.from({ length: size }, (_, i) => start + i)
      const offset = (seed + idx * 7) % size
      const rotated = [...arr.slice(offset), ...arr.slice(0, offset)]
      return rotated.slice(0, 5)
    })
    // Compose rows from columns; set center free
    const rows = Array.from({ length: 5 }, (_, r) =>
      Array.from({ length: 5 }, (_, c) => {
        if (r === 2 && c === 2) return '★'
        return columns[c][r]
      })
    )
    return rows
  }

  return (
    <div className="play-wrapper">
      <div className="stats">
        <div className="stat">Game<br /><strong>{gameId}</strong></div>
        <div className="stat">Bet<br /><strong>{stake} ETB</strong></div>
        <div className="stat">Active Game<br /><strong>{activeGame}</strong></div>
        <div className="stat">Wallet<br /><strong>0.00 ETB</strong></div>
        <div className="stat">Gift<br /><strong>0.00 Coin</strong></div>
      </div>

      <div className="grid-scroll">
        <div className="grid">
          {Array.from({ length: 200 }, (_, i) => i + 1).map(n => (
            <button
              key={n}
              onClick={() => setPreview(n)}
              className={active.has(n) ? 'cell active' : 'cell'}
            >
              {n}
            </button>
          ))}
        </div>
      </div>

      <div className="actions">
        <button className="refresh" onClick={() => window.location.reload()}>Refresh</button>
      </div>

      {preview && (
        <div className="modal-overlay" onClick={() => setPreview(null)}>
          <div className="modal card-preview" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Card #{preview}</h3>
              <button className="modal-close" onClick={() => setPreview(null)}>×</button>
            </div>
            <div className="modal-body">
              <div className="bingo-head">
                <span className="b">B</span>
                <span className="i">I</span>
                <span className="n">N</span>
                <span className="g">G</span>
                <span className="o">O</span>
              </div>
              <div className="card-grid">
                {buildCard(preview).map((row, ri) => (
                  <div className="row" key={ri}>
                    {row.map((val, ci) => (
                      <div className={val === '★' ? 'cg-cell free' : 'cg-cell'} key={ci}>
                        {val}
                      </div>
                    ))}
                  </div>
                ))}
              </div>

              <div className="preview-actions">
                <button className="accept" onClick={() => {
                  try {
                    const tg = window?.Telegram?.WebApp
                    tg?.sendData?.(JSON.stringify({ type: 'choose_card', card: preview, stake }))
                  } catch {}
                  toggle(preview)
                  setPreview(null)
                }}>Accept</button>
                <button className="cancel" onClick={() => setPreview(null)}>Cancel</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
