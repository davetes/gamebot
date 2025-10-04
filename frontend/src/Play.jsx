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
  } catch {}
  return tg
}

export default function Play() {
  const q = useQuery()
  const initialStake = q.get('stake') ?? '10'
  const [stake, setStake] = useState(initialStake)
  const [active, setActive] = useState(new Set())
  const [gameId] = useState(() => Math.floor(100000 + Math.random() * 900000))
  const [activeGame] = useState(1)

  useEffect(() => {
    const tg = initTelegram()
    if (!tg) return
    // Initialize MainButton to reflect current stake
    try {
      tg.MainButton.setParams({ text: `Stake: ${stake} ETB`, is_visible: true })
    } catch {}
    const onMain = () => window.location.reload()
    tg.MainButton.onClick(onMain)
    return () => tg.MainButton.offClick(onMain)
  }, [])

  // Keep MainButton text in sync with stake
  useEffect(() => {
    const tg = window?.Telegram?.WebApp
    if (!tg) return
    try { tg.MainButton.setText(`Stake: ${stake} ETB`) } catch {}
  }, [stake])

  const toggle = (n) => {
    setActive(prev => {
      const next = new Set(prev)
      if (next.has(n)) next.delete(n)
      else next.add(n)
      return next
    })
  }

  const pickStake = (value) => {
    setStake(String(value))
    // Update URL (keeps mode=play) without full reload
    try {
      const url = new URL(window.location.href)
      url.searchParams.set('mode', 'play')
      url.searchParams.set('stake', String(value))
      window.history.replaceState({}, '', url)
    } catch {}
    // Optional: haptic feedback if available
    try { window?.Telegram?.WebApp?.HapticFeedback?.impactOccurred('light') } catch {}
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

      <div className="actions">
        <div className="stake-group">
          <button
            className={stake === '10' ? 'stake-btn active' : 'stake-btn'}
            onClick={() => pickStake(10)}
          >10 ETB</button>
          <button
            className={stake === '20' ? 'stake-btn active' : 'stake-btn'}
            onClick={() => pickStake(20)}
          >20 ETB</button>
          <button
            className={stake === '50' ? 'stake-btn active' : 'stake-btn'}
            onClick={() => pickStake(50)}
          >50 ETB</button>
        </div>
        <button className="refresh" onClick={() => window.location.reload()}>Refresh</button>
      </div>
    </div>
  )
}
