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
  } catch {}
  return tg
}

export default function Play() {
  const q = useQuery()
  const stake = q.get('stake') ?? '10'
  const gameRunning = q.get('started') === '1' || q.get('running') === '1' || q.get('active') === '1'
  const [selected, setSelected] = useState(null) // single selected card number or null
  const [gameId] = useState(() => Math.floor(100000 + Math.random() * 900000))
  const [activeGame] = useState(1)
  const [preview, setPreview] = useState(null) // number or null
  const [notice, setNotice] = useState(null) // string | null
  const [countdown, setCountdown] = useState(() => (gameRunning ? 20 : 0))
  const [phase, setPhase] = useState(() => (gameRunning ? 'choosing' : 'idle')) // idle | choosing | started
  const [currentNumber, setCurrentNumber] = useState(null)
  const [calls, setCalls] = useState([])
  const [muted, setMuted] = useState(false)
  const [bonusOn, setBonusOn] = useState(false)

  useEffect(() => {
    const tg = initTelegram()
    if (!tg) return
    const onMain = () => window.location.reload()
    tg.MainButton.onClick(onMain)
    return () => tg.MainButton.offClick(onMain)
  }, [])

  // Auto-hide notice after a short delay
  useEffect(() => {
    if (!notice) return
    const t = setTimeout(() => setNotice(null), 2500)
    return () => clearTimeout(t)
  }, [notice])

  // Ensure body doesn't center content (override Vite template styles)
  useEffect(() => {
    document.body.classList.add('play-mode')
    return () => document.body.classList.remove('play-mode')
  }, [])

  // If a game is currently running, auto-show the waiting notice immediately
  useEffect(() => {
    if (!gameRunning) return
    setNotice('running')
    setCountdown(20)
    setPhase('choosing')
    try {
      const tg = window?.Telegram?.WebApp
      tg?.showAlert?.('Starting soon. Please wait...')
    } catch {}
  }, [gameRunning])

  // Countdown timer during choosing phase; when hits 0, start game and play sound
  useEffect(() => {
    if (phase !== 'choosing') return
    if (countdown <= 0) {
      setPhase('started')
      try { playStartSound() } catch {}
      // seed a starting number to show in the overlay
      const startNum = Math.floor(1 + Math.random() * 75)
      setCurrentNumber(startNum)
      // create a list of prior calls + the current number
      const prior = new Set()
      while (prior.size < 8) {
        const n = Math.floor(1 + Math.random() * 75)
        if (n !== startNum) prior.add(n)
      }
      const arr = [...prior]
      setCalls([...arr, startNum])
      // speak the first call
      try { playCallBlip(startNum) } catch {}
      return
    }
    const t = setInterval(() => setCountdown((s) => (s > 0 ? s - 1 : 0)), 1000)
    return () => clearInterval(t)
  }, [phase, countdown])

  const locked = (phase === 'choosing')

  function playStartSound() {
    if (muted) return
    const synth = window.speechSynthesis
    if (!synth || typeof window.SpeechSynthesisUtterance === 'undefined') return
    const utter = new window.SpeechSynthesisUtterance('Game starting')
    utter.lang = 'en-US'
    utter.rate = 1
    utter.pitch = 1
    utter.volume = 1
    synth.cancel()
    synth.speak(utter)
  }

  // Speak the letter-number for each call, e.g., "B 10"
  function playCallBlip(n) {
    if (muted) return
    const synth = window.speechSynthesis
    if (!synth || typeof window.SpeechSynthesisUtterance === 'undefined') return
    if (!n || typeof n !== 'number') return
    const letters = ['B','I','N','G','O']
    const letter = letters[Math.floor((n - 1) / 15)] || ''
    const utter = new window.SpeechSynthesisUtterance(`${letter} ${n}`)
    utter.lang = 'en-US'
    utter.rate = 0.95
    utter.pitch = 1
    utter.volume = 1
    synth.cancel()
    synth.speak(utter)
  }

  // After started, generate periodic calls
  useEffect(() => {
    if (phase !== 'started') return
    // ensure first call exists
    if (!currentNumber) return
    const seen = new Set(calls)
    // interval to add next call every 4 seconds
    const int = setInterval(() => {
      if (seen.size >= 75) { clearInterval(int); return }
      let n = Math.floor(1 + Math.random() * 75)
      while (seen.has(n)) n = Math.floor(1 + Math.random() * 75)
      seen.add(n)
      setCalls(prev => [...prev, n])
      setCurrentNumber(n)
      try { playCallBlip(n) } catch {}
    }, 4000)
    return () => clearInterval(int)
  }, [phase, currentNumber])

  const toggle = (n) => {
    setSelected(prev => (prev === n ? null : n))
  }

  // Static cards are provided by bingoCards.js (getCard, CARD_COUNT)

  return (
    <div className="play-wrapper">
      {notice && (
        <div
          className="notice-banner"
          style={{
            position: 'fixed',
            top: 12,
            left: '50%',
            transform: 'translateX(-50%)',
            zIndex: 1000,
            background: '#fff4e5',
            border: '1px solid #ffcc80',
            color: '#8a4b08',
            padding: '10px 12px',
            borderRadius: 10,
            boxShadow: '0 6px 18px rgba(0,0,0,.12)',
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            maxWidth: '92vw'
          }}
        >
          <span style={{fontWeight:800}}>Wait until the next game starts</span>
          <button
            aria-label="Close"
            onClick={() => setNotice(null)}
            style={{marginLeft:'auto', background:'transparent', border:'none', fontSize:18, cursor:'pointer', color:'#8a4b08'}}
          >×</button>
        </div>
      )}

      {/* Game overlay after countdown finishes */}
      {phase === 'started' && (
        <div style={{position:'fixed', inset:0, background:'linear-gradient(180deg,#330a5c,#2a0845)', overflowY:'auto', zIndex:1000, padding:'12px'}}>
          <div style={{display:'flex', gap:8, flexWrap:'wrap', alignItems:'center'}}>
            <div style={{background:'#5e2b91', color:'#fff', padding:'6px 12px', borderRadius:18, fontWeight:200}}>Call {calls.length}</div>
            <div style={{background:'#1e90ff', color:'#fff', padding:'6px 12px', borderRadius:18, fontWeight:200}}>Players 50</div>
            <div style={{background:'#2e8b57', color:'#fff', padding:'6px 12px', borderRadius:18, fontWeight:200}}>Stake {stake}</div>
            <div style={{background:'#2e8b57', color:'#fff', padding:'6px 12px', borderRadius:18, fontWeight:200}}>Derash 400</div>
            <div style={{background:'#2d3436', color:'#fff', padding:'6px 12px', borderRadius:18, fontWeight:200}}>Game {gameId}</div>
            {/* Bonus toggle and sound icon */}
            <div style={{marginLeft:'auto', display:'flex', alignItems:'center', gap:8}}>
              <div style={{background:'#3b2f75', color:'#fff', padding:'6px 10px', borderRadius:18, fontWeight:800, display:'flex', alignItems:'center', gap:10}}>
                <span>Bonus</span>
                <label style={{display:'inline-flex', alignItems:'center', gap:6, cursor:'pointer'}}>
                  <input type="checkbox" checked={bonusOn} onChange={(e)=>setBonusOn(e.target.checked)} style={{display:'none'}} />
                  <span style={{width:36, height:20, background: bonusOn ? '#2ecc71' : '#777', borderRadius:999, position:'relative', transition:'all .2s'}}>
                    <span style={{position:'absolute', top:2, left: bonusOn ? 18 : 2, width:16, height:16, background:'#fff', borderRadius:'50%', transition:'all .2s'}}></span>
                  </span>
                </label>
              </div>
              <button onClick={()=>setMuted(m=>!m)} aria-label="toggle-sound" style={{background:'#ffcc66', border:'none', color:'#3b0066', fontWeight:900, padding:'6px 10px', borderRadius:18}}>{muted ? '🔇' : '🔊'}</button>
          </div>
          </div>

          {/* call board */}
          <div style={{marginTop:10, background:'rgba(255,255,255,0.12)', borderRadius:14, padding:10, border:'1px solid rgba(255,255,255,0.2)'}}>
            {['B','I','N','G','O'].map((h, hi) => (
              <div key={hi} style={{display:'grid', gridTemplateColumns:'repeat(16,1fr)', gap:6, alignItems:'center', marginBottom:6}}>
                <div style={{gridColumn:'span 1', color:'#9fd3ff', fontWeight:900}}>{h}</div>
                <div style={{gridColumn:'span 15', display:'grid', gridTemplateColumns:'repeat(15,1fr)', gap:6}}>
                  {Array.from({length:15}, (_,i)=> hi*15 + i + 1).map(n => {
                    const hit = calls.includes(n)
                    return (
                      <div key={n} style={{height:22, borderRadius:999, background: hit ? '#ff6b6b' : '#f3e8ff', color: hit ? '#fff' : '#555', fontSize:12, display:'flex', alignItems:'center', justifyContent:'center', boxShadow: hit ? 'inset 0 -2px 0 rgba(0,0,0,.15)' : 'none'}}>{n}</div>
                    )
                  })}
                </div>
              </div>
            ))}
          </div>

          {/* current ball and recent balls row */}
          <div style={{display:'flex', flexDirection:'column', alignItems:'center', margin:'14px 0'}}>
            {/* Lettered big ball */}
            {(() => { const n = currentNumber || 0; const letters = ['B','I','N','G','O']; const letter = n? letters[Math.floor((n-1)/15)] : ''; return (
              <div style={{position:'relative'}}>
                <div style={{width:96, height:96, borderRadius:'50%', background:'#ff5e57', color:'#fff', display:'flex', alignItems:'center', justifyContent:'center', fontWeight:900, fontSize:36, boxShadow:'0 10px 30px rgba(0,0,0,.25)'}}>
                  {n || '--'}
                </div>
                <div style={{position:'absolute', top:-12, left:'50%', transform:'translateX(-50%)', background:'#fff', color:'#d82e5f', width:28, height:28, borderRadius:'50%', display:'flex', alignItems:'center', justifyContent:'center', fontWeight:900}}>{letter}</div>
              </div>
            )})()}
            {/* recent balls with letter colors */}
            <div style={{display:'flex', gap:8, marginTop:10}}>
              {calls.slice(-5).map((n, idx) => { const col = ['#2ecc71','#e74c3c','#f1c40f','#3498db','#9b59b6'][Math.floor((n-1)/15)]; return (
                <div key={idx} style={{width:36, height:36, borderRadius:'50%', background:col, color:'#fff', display:'flex', alignItems:'center', justifyContent:'center', fontWeight:900}}>{n}</div>
              )})}
            </div>
          </div>

          {/* Your selected card view */}
          <div style={{position:'relative', maxWidth:520, margin:'0 auto', background:'linear-gradient(#6d2ca3,#4a1571)', padding:16, borderRadius:18, boxShadow:'0 10px 30px rgba(0,0,0,.35)'}}>
            <div style={{display:'grid', gridTemplateColumns:'repeat(5,1fr)', gap:8, marginBottom:8}}>
              {['#2ecc71','#e74c3c','#f1c40f','#3498db','#9b59b6'].map((bg, i) => (
                <span key={i} style={{display:'block', textAlign:'center', color:'#fff', fontWeight:900, borderRadius:10, padding:'8px 0', background:bg, boxShadow:'inset 0 2px 0 rgba(255,255,255,.5)'}}>{'BINGO'[i]}</span>
              ))}
            </div>
            <div style={{display:'flex', flexDirection:'column', gap:10, background:'linear-gradient(#ffffff,#f0f0f0)', borderRadius:16, padding:12, border:'3px solid rgba(255,255,255,0.4)'}}>
              {(selected ? getCard(selected) : getCard(1)).map((row, ri) => (
                <div key={ri} style={{display:'grid', gridTemplateColumns:'repeat(5,1fr)', gap:10}}>
                  {row.map((val, ci) => {
                    const isHit = typeof val === 'number' && calls.includes(val)
                    const bg = val === '★' ? 'linear-gradient(#ffbe76,#f0932b)' : isHit ? 'linear-gradient(#a66df0,#7a3bd1)' : 'linear-gradient(#f7f9fc,#e9eef5)'
                    const col = isHit ? '#fff' : '#222'
                    return (
                      <div key={ci} style={{background:bg, color:col, borderRadius:14, textAlign:'center', padding:'12px 0', fontWeight:900, boxShadow:'0 2px 0 rgba(0,0,0,.15)'}}>
                        {val}
                      </div>
                    )
                  })}
                </div>
              ))}
            </div>
            {/* Left/right arrows */}
            <button aria-label="prev" style={{position:'absolute', left:-12, top:'50%', transform:'translateY(-50%)', width:28, height:28, borderRadius:'50%', border:'none', background:'#6d2ca3', color:'#fff', fontWeight:900}}>{'<'}</button>
            <button aria-label="next" style={{position:'absolute', right:-12, top:'50%', transform:'translateY(-50%)', width:28, height:28, borderRadius:'50%', border:'none', background:'#6d2ca3', color:'#fff', fontWeight:900}}>{'>'}</button>
            <div style={{display:'flex', justifyContent:'center', marginTop:14}}>
              <button style={{background:'linear-gradient(#ffdf6e,#d4ac0d)', color:'#2b2b2b', border:'none', borderRadius:12, padding:'12px 20px', fontWeight:900, boxShadow:'0 4px 12px rgba(0,0,0,.25)'}}>BINGO</button>
            </div>
          </div>

          {/* bottom-left blue chip */}
          <div style={{position:'fixed', left:10, bottom:14, width:42, height:42, borderRadius:'50%', background:'#2d7ef7', color:'#fff', display:'flex', alignItems:'center', justifyContent:'center', fontWeight:900}}>{currentNumber ?? ''}</div>
        </div>
      )}
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
              onClick={() => {
                if (locked) {
                  setNotice('running')
                  try {
                    const tg = window?.Telegram?.WebApp
                    tg?.showAlert?.('Wait until the next game starts')
                  } catch {}
                  return
                }
                setPreview(n)
              }}
              className={selected === n ? 'cell active' : 'cell'}
              disabled={false}
            >
              {n}
            </button>
          ))}
        </div>
      </div>

      <div className="actions">
        <button className="refresh" onClick={() => window.location.reload()}>Refresh</button>
      </div>

      {/* Header pills similar to the provided platform */}
      {phase === 'choosing' && (
        <div style={{position:'fixed', top:8, left:'50%', transform:'translateX(-50%)', display:'flex', gap:10, zIndex:3}}>
          <div style={{background:'#2e8b57', color:'#fff', padding:'6px 10px', borderRadius:20, fontWeight:800, boxShadow:'0 4px 12px rgba(0,0,0,.18)'}}>Derash {stake}</div>
          <div style={{background:'#6c5ce7', color:'#fff', padding:'6px 10px', borderRadius:20, fontWeight:800, boxShadow:'0 4px 12px rgba(0,0,0,.18)'}}>
            {countdown > 0 ? `Starting On ${countdown}` : 'Starting Now'}
          </div>
        </div>
      )}

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
            <div className="modal-body" style={{padding:10}}>
              <div className="card-grid" style={{
                display:'grid', gridTemplateColumns:'repeat(5,1fr)', gap:3, background:'#ffa63a', borderRadius:12, padding:4, border:'3px solid #e08924'
              }}>
                {['B','I','N','G','O'].map((h, i) => (
                  <span
                    key={i}
                    className={h.toLowerCase()}
                    style={{
                      display:'flex', alignItems:'center', justifyContent:'center',
                      color:'#fff', fontWeight:900, borderRadius:8, fontSize:14,
                      aspectRatio:'1 / 1',
                      background: ({B:'#2ecc71', I:'#e74c3c', N:'#f1c40f', G:'#3498db', O:'#9b59b6'})[h]
                    }}
                  >{h}</span>
                ))}
                {(() => { const flat = getCard(preview).flat(); return flat.map((val, idx) => (
                  <div
                    key={idx}
                    className={val === '★' ? 'cg-cell free' : 'cg-cell'}
                    style={{
                      background: val === '★' ? '#1f7a4f' : '#fff',
                      borderRadius: 10, color: val === '★' ? '#fff' : '#222', fontWeight:800,
                      aspectRatio: '1 / 1', display:'flex', alignItems:'center', justifyContent:'center', padding:0, fontSize:14
                    }}
                  >
                    {val}
                  </div>
                )) })()}
              </div>

              <div className="preview-actions" style={{display:'flex', gap:10, justifyContent:'center', marginTop:12}}>
                <button className="accept" style={{background:'#19c37d', border:'none', color:'#fff', padding:'10px 14px', borderRadius:10, fontWeight:800}}
                  onClick={() => {
                  try {
                    const tg = window?.Telegram?.WebApp
                    tg?.sendData?.(JSON.stringify({ type: 'choose_card', card: preview, stake }))
                  } catch {}
                  setSelected(preview)
                  setPreview(null)
                  setCountdown(20)
                  setPhase('choosing')
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
