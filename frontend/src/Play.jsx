import React, { useEffect, useMemo, useState } from 'react'
import './play.css'
import { getCard, CARD_COUNT } from './bingoCards'

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
      is_visible: false,

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

  // Static cards are provided by bingoCards.js (getCard, CARD_COUNT)

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
          {Array.from({ length: CARD_COUNT }, (_, i) => i + 1).map(n => (
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
        <div
          className="modal-overlay"
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 999,
          }}
          onClick={() => setPreview(null)}
        >
          <div
            className="modal card-preview"
            style={{
              width: 'min(440px,92vw)',
              background: 'linear-gradient(#ffd27a,#ffb54e)',
              borderRadius: 12,
              boxShadow: '0 10px 30px rgba(0,0,0,.25)',
              overflow: 'hidden',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="modal-header" style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '12px 14px', borderBottom: '1px solid #eee', background: 'transparent'
            }}>
              <div style={{display:'flex', alignItems:'center', gap:8}}>
                <div style={{
                  background:'#ffcc4d', color:'#6b3e00', fontWeight:900,
                  borderRadius:999, padding:'4px 10px', boxShadow:'inset 0 2px 0 rgba(255,255,255,.6)',
                  border:'2px solid #f39c12'
                }}></div>
                <h3 style={{margin:0,color:'#2b2b2b'}}>Card #{preview}</h3>
              </div>
              <button className="modal-close" style={{background:'transparent', border:'none', fontSize:22, lineHeight:1, cursor:'pointer'}} onClick={() => setPreview(null)}>×</button>
            </div>
            <div className="modal-body" style={{padding:14}}>
              <div className="bingo-head" style={{display:'grid', gridTemplateColumns:'repeat(5,1fr)', gap:6, marginBottom:8}}>
                <span className="b" style={{display:'block', textAlign:'center', color:'#fff', fontWeight:900, borderRadius:8, padding:'6px 0', background:'#2ecc71'}}>B</span>
                <span className="i" style={{display:'block', textAlign:'center', color:'#fff', fontWeight:900, borderRadius:8, padding:'6px 0', background:'#e74c3c'}}>I</span>
                <span className="n" style={{display:'block', textAlign:'center', color:'#fff', fontWeight:900, borderRadius:8, padding:'6px 0', background:'#f1c40f'}}>N</span>
                <span className="g" style={{display:'block', textAlign:'center', color:'#fff', fontWeight:900, borderRadius:8, padding:'6px 0', background:'#3498db'}}>G</span>
                <span className="o" style={{display:'block', textAlign:'center', color:'#fff', fontWeight:900, borderRadius:8, padding:'6px 0', background:'#9b59b6'}}>O</span>
              </div>
              <div className="card-grid" style={{
                display:'flex', flexDirection:'column', gap:6, background:'#ffa63a', borderRadius:12, padding:8, border:'3px solid #e08924'
              }}>
                {getCard(preview).map((row, ri) => (
                  <div className="row" key={ri} style={{display:'grid', gridTemplateColumns:'repeat(5,1fr)', gap:6}}>
                    {row.map((val, ci) => (
                      <div
                        className={val === '★' ? 'cg-cell free' : 'cg-cell'}
                        key={ci}
                        style={{
                          background: val === '★' ? '#1f7a4f' : '#222',
                          borderRadius: 10, color: '#fff', textAlign:'center', padding:'10px 0', fontWeight:800
                        }}
                      >
                        {val}
                      </div>
                    ))}
                  </div>
                ))}
              </div>

              <div className="preview-actions" style={{display:'flex', gap:10, justifyContent:'center', marginTop:12}}>
                <button className="accept" style={{background:'#19c37d', border:'none', color:'#fff', padding:'10px 14px', borderRadius:10, fontWeight:800}}
                  onClick={() => {
                  try {
                    const tg = window?.Telegram?.WebApp
                    tg?.sendData?.(JSON.stringify({ type: 'choose_card', card: preview, stake }))
                  } catch {}
                  toggle(preview)
                  setPreview(null)
                }}>Accept</button>
                <button className="cancel" style={{background:'#d0d3d4', border:'none', color:'#222', padding:'10px 14px', borderRadius:10, fontWeight:800}} onClick={() => setPreview(null)}>Cancel</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
