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
              onClick={() => toggle(n)}
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
    </div>
  )
}
