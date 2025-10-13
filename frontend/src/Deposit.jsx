import React, { useEffect, useState } from 'react'
import './deposit.css'

export default function Deposit() {
  const params = new URLSearchParams(window.location.search)
  const amount = params.get('amount') || '—'
  const [telebirrOpen, setTelebirrOpen] = useState(false)
  const [telebirrTxn, setTelebirrTxn] = useState('')
  const [telebirrTxnErr, setTelebirrTxnErr] = useState('')
  const [cbeOpen, setCbeOpen] = useState(false)
  const [cbeTxn, setCbeTxn] = useState('')
  const [cbeTxnErr, setCbeTxnErr] = useState('')
  const [boaOpen, setBoaOpen] = useState(false)
  const [boaTxn, setBoaTxn] = useState('')
  const [boaTxnErr, setBoaTxnErr] = useState('')
  const [cbeBirrOpen, setCbeBirrOpen] = useState(false)
  const [cbeBirrPhone, setCbeBirrPhone] = useState('')
  const [cbeBirrTxn, setCbeBirrTxn] = useState('')
  const [cbeBirrPhoneErr, setCbeBirrPhoneErr] = useState('')
  const [cbeBirrTxnErr, setCbeBirrTxnErr] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [telebirrReceipt, setTelebirrReceipt] = useState(null)
  const [cbeReceipt, setCbeReceipt] = useState(null)
  const [boaReceipt, setBoaReceipt] = useState(null)
  const [cbeBirrReceipt, setCbeBirrReceipt] = useState(null)
  const [telebirrReceiptErr, setTelebirrReceiptErr] = useState('')
  const [cbeReceiptErr, setCbeReceiptErr] = useState('')
  const [boaReceiptErr, setBoaReceiptErr] = useState('')
  const [cbeBirrReceiptErr, setCbeBirrReceiptErr] = useState('')
  const [telebirrSubmitMsg, setTelebirrSubmitMsg] = useState('')
  const [cbeBirrSubmitMsg, setCbeBirrSubmitMsg] = useState('')
  const [boaSubmitMsg, setBoaSubmitMsg] = useState('')
  const [cbeSubmitMsg, setCbeSubmitMsg] = useState('')

  useEffect(() => {
    const tg = window?.Telegram?.WebApp
    try {
      tg?.ready()
      tg?.expand()
    } catch {}
  }, [])

  

  const banks = [
    { key: 'telebirr', name: 'Telebirr', img: '/telebirr.jpg' },
    { key: 'cbe', name: 'CBE Bank', img: '/cbe.jpg' },
    { key: 'boa', name: 'BOA', img: '/boa.jpg' },
    { key: 'cbe-birr', name: 'CBE Birr', img: '/cbebirr.jpg' },
  ]

  return (
    <div className="deposit-wrap">
      <div className="brand">
        <img alt="Cartela Bingo" className="brand-logo" src="/vite.svg" />
      </div>

      <h2 className="title">Manual Deposit</h2>
      <p className="subtitle">Select your bank to deposit funds</p>

      <div className="amount">Amount: <strong>{amount}</strong> ETB</div>

      <div className="bank-grid">
        {banks.map(b => (
          <button key={b.key} className="bank-card" onClick={() => {
            if (b.key === 'telebirr') setTelebirrOpen(true)
            else if (b.key === 'cbe') setCbeOpen(true)
            else if (b.key === 'boa') setBoaOpen(true)
            else if (b.key === 'cbe-birr') setCbeBirrOpen(true)
            else alert(`${b.name} selected`)
          }}>
            <img src={b.img} alt={b.name} />
            <span>{b.name}</span>
          </button>
        ))}
      </div>

      <footer className="deposit-footer">
        <span>Copyright © luckybet 2025</span>
      </footer>

      {telebirrOpen && (
        <div className="modal-overlay" onClick={() => setTelebirrOpen(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Telebirr {amount} ETB Deposit</h3>
              <button className="modal-close" onClick={() => setTelebirrOpen(false)}>×</button>
            </div>
            <div className="modal-body">
              <h4 className="acc-title">የቴሌብር አካውንት</h4>
              <div className="acc-number">
                <span>251931162223</span>
                <button className="copy" onClick={() => {
                  navigator.clipboard.writeText('251931162223')
                }}>📋</button>
              </div>

              <ol className="steps">
                <li> ከላይ ባለው የቴሌብር አካውንት ብር ያስገቡ</li>
                <li>  የደረሳችሁን አጭር የጹሁፍ መለክት ስክሪንሻት(Screenshot) በማረግ ከታሽ ባለው የupload ማስገቢያው ላይ upload በማረግ ይላኩት</li>
              </ol>

              <p style={{margin:'8px 0 12px 0', color:'#333'}}>
              የሚያጋጥማቹ የክፍያ ችግር ካለ ኤጀንቱን ማዋራት ይችላሉ ወይም <a href="https://t.me/Afamedawa" target="_blank" rel="noreferrer">@luckybet_support</a> በዚ ሰፖርት ማዉራት ይችላሉ።
              </p>

              <div className="verify-title">Upload Receipt Screenshot</div>
              <div className="verify-row">
                <input type="file" accept="image/*" className={telebirrReceiptErr ? 'input-error' : ''} onChange={e => { setTelebirrReceipt(e.target.files?.[0] || null); setTelebirrReceiptErr('') }} />
                <button className="verify-btn" disabled={submitting} onClick={async () => {
                  const tg = window?.Telegram?.WebApp
                  if (!telebirrReceipt) { setTelebirrReceiptErr('እባክዎን የደረሰኙን ስክሪንሻት (screenshot) አስቀድመው ይስቀሉ'); return }
                  const user = tg?.initDataUnsafe?.user
                  const fd = new FormData()
                  fd.append('method', 'telebirr')
                  fd.append('amount', String(amount))
                  if (user?.id) fd.append('user_id', String(user.id))
                  if (user?.username) fd.append('username', user.username)
                  const fullName = [user?.first_name, user?.last_name].filter(Boolean).join(' ')
                  if (fullName) fd.append('full_name', fullName)
                  fd.append('photo', telebirrReceipt)
                  setSubmitting(true)
                  try {
                    const res = await fetch('/api/upload-receipt', { method: 'POST', body: fd })
                    const data = await res.json().catch(() => ({}))
                    if (!res.ok || data?.error) {
                      setTelebirrSubmitMsg('Failed to send. Please try again.')
                    } else {
                      setTelebirrSubmitMsg('መልዕክትዎ በተሳካ  ሁኔታ ተልኳል')
                    }
                  } catch (e) {
                    setTelebirrSubmitMsg('Network error. Please try again.')
                  } finally {
                    setSubmitting(false)
                  }
                }}>{submitting ? 'Sending…' : 'send screenshot'}</button>
              </div>
              {telebirrReceiptErr && <div className="error-text">{telebirrReceiptErr}</div>}
              {telebirrSubmitMsg && <div className="hint" style={{color:'#1a7f37'}}>{telebirrSubmitMsg}</div>}
            </div>
          </div>
        </div>
      )}

      {cbeBirrOpen && (
        <div className="modal-overlay" onClick={() => setCbeBirrOpen(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>CBE Birr {amount} ETB Deposit</h3>
              <button className="modal-close" onClick={() => setCbeBirrOpen(false)}>×</button>
            </div>
            <div className="modal-body">
              <h4 className="acc-title">ሲቢኢ ብር ባንክ አካውንት</h4>
              <div className="acc-number" style={{color:'#7b22a7'}}>
                <span>251931162223</span>
                <button className="copy" onClick={() => {
                  navigator.clipboard.writeText('251931162223')
                }}>📋</button>
              </div>

              <ol className="steps">
                <li>ከላይ ባለው ሲቢኢ ብር አካውንት ብር ያስገቡ</li>
                <li>የደረሳችሁን አጭር የጹሁፍ መለክት ስክሪንሻት(Screenshot) በማረግ ከታሽ ባለው የupload ማስገቢያው ላይ upload በማረግ ይላኩት</li>
              </ol>
          <p style={{margin:'8px 0 12px 0', color:'#333'}}>
              የሚያጋጥማቹ የክፍያ ችግር ካለ ኤጀንቱን ማዋራት ይችላሉ ወይም<a href="https://t.me/Afamedawa" target="_blank" rel="noreferrer">@luckybet_support</a>በዚ ሰፖርት ማዉራት ይችላሉ።
              </p>
              <div className="verify-title">Upload Receipt Screenshot</div>
              <div className="verify-row">
                <input type="file" accept="image/*" className={cbeBirrReceiptErr ? 'input-error' : ''} onChange={e => { setCbeBirrReceipt(e.target.files?.[0] || null); setCbeBirrReceiptErr('') }} />
                <button className="verify-btn" disabled={submitting} onClick={async () => {
                  const tg = window?.Telegram?.WebApp
                  if (!cbeBirrReceipt) { setCbeBirrReceiptErr('እባክዎን የደረሰኙን ስክሪንሻት (screenshot) አስቀድመው ይስቀሉ'); return }
                  const user = tg?.initDataUnsafe?.user
                  const fd = new FormData()
                  fd.append('method', 'cbe-birr')
                  fd.append('amount', String(amount))
                  if (user?.id) fd.append('user_id', String(user.id))
                  if (user?.username) fd.append('username', user.username)
                  const fullName = [user?.first_name, user?.last_name].filter(Boolean).join(' ')
                  if (fullName) fd.append('full_name', fullName)
                  fd.append('photo', cbeBirrReceipt)
                  setSubmitting(true)
                  try {
                    const res = await fetch('/api/upload-receipt', { method: 'POST', body: fd })
                    const data = await res.json().catch(() => ({}))
                    if (!res.ok || data?.error) {
                      setCbeBirrSubmitMsg('Failed to send. Please try again.')
                    } else {
                      setCbeBirrSubmitMsg('መልዕክትዎ በተሳካ  ሁኔታ ተልኳል')
                    }
                  } catch (e) {
                    setCbeBirrSubmitMsg('Network error. Please try again.')
                  } finally {
                    setSubmitting(false)
                  }
                }}>{submitting ? 'Sending…' : 'send screenshot'}</button>
              </div>
              {cbeBirrReceiptErr && <div className="error-text">{cbeBirrReceiptErr}</div>}
              {cbeBirrSubmitMsg && <div className="hint" style={{color:'#1a7f37'}}>{cbeBirrSubmitMsg}</div>}
            </div>
          </div>
        </div>
      )}

      {boaOpen && (
        <div className="modal-overlay" onClick={() => setBoaOpen(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>BOA {amount} ETB Deposit</h3>
              <button className="modal-close" onClick={() => setBoaOpen(false)}>×</button>
            </div>
            <div className="modal-body">
              <h4 className="acc-title">አቢሲኒያ ባንክ አካውንት</h4>
              <div className="acc-number" style={{color:'#b1802b'}}>
                <span>101311686</span>
                <button className="copy" onClick={() => {
                  navigator.clipboard.writeText('101311686')
                }}>📋</button>
              </div>

              <ol className="steps">
                <li>ከላይ ባለው አቢስንያ ባንክ አካውንት ብር ያስገቡ</li>
                <li>የደረሳችሁን አጭር የጹሁፍ መለክት ስክሪንሻት(Screenshot) በማረግ ከታሽ ባለው የupload ማስገቢያው ላይ upload በማረግ ይላኩት</li>
              </ol>

              <p style={{margin:'8px 0 12px 0', color:'#333'}}>
              የሚያጋጥማቹ የክፍያ ችግር ካለ ኤጀንቱን ማዋራት ይችላሉ ወይም<a href="https://t.me/Afamedawa" target="_blank" rel="noreferrer">@luckybet_support</a>በዚ ሰፖርት ማዉራት ይችላሉ።
              </p>

              <div className="verify-title">Upload Receipt Screenshot</div>
              <div className="verify-row">
                <input type="file" accept="image/*" className={boaReceiptErr ? 'input-error' : ''} onChange={e => { setBoaReceipt(e.target.files?.[0] || null); setBoaReceiptErr('') }} />
                <button className="verify-btn" disabled={submitting} onClick={async () => {
                  const tg = window?.Telegram?.WebApp
                  if (!boaReceipt) { setBoaReceiptErr('እባክዎን የደረሰኙን ስክሪንሻት (screenshot) አስቀድመው ይስቀሉ'); return }
                  const user = tg?.initDataUnsafe?.user
                  const fd = new FormData()
                  fd.append('method', 'boa')
                  fd.append('amount', String(amount))
                  if (user?.id) fd.append('user_id', String(user.id))
                  if (user?.username) fd.append('username', user.username)
                  const fullName = [user?.first_name, user?.last_name].filter(Boolean).join(' ')
                  if (fullName) fd.append('full_name', fullName)
                  fd.append('photo', boaReceipt)
                  setSubmitting(true)
                  try {
                    const res = await fetch('/api/upload-receipt', { method: 'POST', body: fd })
                    const data = await res.json().catch(() => ({}))
                    if (!res.ok || data?.error) {
                      setBoaSubmitMsg('Failed to send. Please try again.')
                    } else {
                      setBoaSubmitMsg('መልዕክትዎ በተሳካ  ሁኔታ ተልኳል')
                    }
                  } catch (e) {
                    setBoaSubmitMsg('Network error. Please try again.')
                  } finally {
                    setSubmitting(false)
                  }
                }}>{submitting ? 'Sending…' : 'send screenshot'}</button>
              </div>
              {boaReceiptErr && <div className="error-text">{boaReceiptErr}</div>}
              {boaSubmitMsg && <div className="hint" style={{color:'#1a7f37'}}>{boaSubmitMsg}</div>}
            </div>
          </div>
        </div>
      )}

      {cbeOpen && (
        <div className="modal-overlay" onClick={() => setCbeOpen(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>CBE Bank {amount} ETB Deposit</h3>
              <button className="modal-close" onClick={() => setCbeOpen(false)}>×</button>
            </div>
            <div className="modal-body">
              <h4 className="acc-title">ኢትዮጵያ ንግድ ባንክ አካውንት</h4>
              <div className="acc-number" style={{color:'#b1802b'}}>
                <span>1000188713517</span>
                <button className="copy" onClick={() => {
                  navigator.clipboard.writeText('1000188713517')
                }}>📋</button>
              </div>

              <ol className="steps">
                <li>ከላይ ባለው የኢትዮጵያ ንግድ ባንክ አካውንት ብር ያስገቡ</li>
                <li> የደረሳችሁን አጭር የጹሁፍ መለክት(sms) ስክሪንሻት(Screenshot) በማረግ ከታሽ ባለው የupload ማስገቢያው ላይ upload በማረግ ይላኩት</li>
              </ol>

              <p style={{margin:'8px 0 12px 0', color:'#333'}}>
              የሚያጋጥማቹ የክፍያ ችግር ካለ ኤጀንቱን ማዋራት ይችላሉ ወይም <a href="https://t.me/Afamedawa" target="_blank" rel="noreferrer">@luckybet_support</a> በዚ ሰፖርት ማዉራት ይችላሉ።
              </p>

              <div className="verify-title">Upload Receipt Screenshot</div>
              <div className="verify-row">
                <input type="file" accept="image/*" className={cbeReceiptErr ? 'input-error' : ''} onChange={e => { setCbeReceipt(e.target.files?.[0] || null); setCbeReceiptErr('') }} />
                <button className="verify-btn" disabled={submitting} onClick={async () => {
                  const tg = window?.Telegram?.WebApp
                  if (!cbeReceipt) { setCbeReceiptErr('እባክዎን የደረሰኙን ስክሪንሻት (screenshot) አስቀድመው ይስቀሉ'); return }
                  const user = tg?.initDataUnsafe?.user
                  const fd = new FormData()
                  fd.append('method', 'cbe')
                  fd.append('amount', String(amount))
                  if (user?.id) fd.append('user_id', String(user.id))
                  if (user?.username) fd.append('username', user.username)
                  const fullName = [user?.first_name, user?.last_name].filter(Boolean).join(' ')
                  if (fullName) fd.append('full_name', fullName)
                  fd.append('photo', cbeReceipt)
                  setSubmitting(true)
                  try {
                    const res = await fetch('/api/upload-receipt', { method: 'POST', body: fd })
                    const data = await res.json().catch(() => ({}))
                    if (!res.ok || data?.error) {
                      setCbeSubmitMsg('Failed to send. Please try again.')
                    } else {
                      setCbeSubmitMsg('መልዕክትዎ በተሳካ  ሁኔታ ተልኳል')
                    }
                  } catch (e) {
                    setCbeSubmitMsg('Network error. Please try again.')
                  } finally {
                    setSubmitting(false)
                  }
                }}>{submitting ? 'Sending…' : 'send screenshot'}</button>
              </div>
              {cbeReceiptErr && <div className="error-text">{cbeReceiptErr}</div>}
              {cbeSubmitMsg && <div className="hint" style={{color:'#1a7f37'}}>{cbeSubmitMsg}</div>}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
