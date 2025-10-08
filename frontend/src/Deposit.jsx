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
  const [submitMsg, setSubmitMsg] = useState('')

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
        <span>Copyright © Allora-Groups 2025</span>
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
                <li> የደረሳችሁን አጭር የጹሁፍ መለክት (SMS) ሙሉዉን ኮፒ (copy) በማረግ ከታሽ ባለው የጹሁፍ ማስገቢያው ላይ ፔስት (paste) በማረግ ይላኩት</li>
              </ol>

              <p style={{margin:'8px 0 12px 0', color:'#333'}}>
              የሚያጋጥማቹ የክፍያ ችግር ካለ ኤጀንቱን ማዋራት ይችላሉ ወይም <a href="https://t.me/cartelabingo_support" target="_blank" rel="noreferrer">@cartelabingo_support</a> በዚ ሰፖርት ማዉራት ይችላሉ።
              </p>

              <div className="verify-title">Verify Transaction</div>
              <div className="verify-row">
                <input
                  value={telebirrTxn}
                  onChange={e => {
                    setTelebirrTxn(e.target.value)
                    if (e.target.value.trim().length >= 8) setTelebirrTxnErr('')
                  }}
                  placeholder="Enter Telebirr transaction num"
                  className={telebirrTxnErr ? 'input-error' : ''}
                />
                <button className="verify-btn" disabled={submitting} onClick={() => {
                  const tg = window?.Telegram?.WebApp
                  const ok = /^[A-Za-z0-9]{8,}$/.test(telebirrTxn.trim())
                  if (!ok) { setTelebirrTxnErr('Invalid transaction'); return }
                  setSubmitting(true)
                  try {
                    tg?.sendData(JSON.stringify({ type: 'verify_deposit', method: 'telebirr', amount, ref: telebirrTxn.trim() }))
                    setSubmitMsg('Submitted. Please check the chat with the bot for confirmation.')
                    // Optionally auto-close after a short delay
                    setTimeout(() => { try { tg?.close?.() } catch {} }, 1200)
                  } finally {
                    setSubmitting(false)
                  }
                }}> {submitting ? 'Sending…' : 'Verify'} </button>
              </div>
              {telebirrTxnErr && <div className="error-text">{telebirrTxnErr}</div>}
              {submitMsg && <div className="hint" style={{color:'#1a7f37'}}>{submitMsg}</div>}
              <div className="hint">E.g Format: CA999DASAD</div>
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
                <li>የደረሳችሁን አጭር የጹሁፍ መለክት (SMS) ሙሉዉን ኮፒ (copy) በማረግ ከታሽ ባለው የጹሁፍ ማስገቢያው ላይ ፔስት (paste) በማረግ ይላኩት</li>
              </ol>

              <div className="verify-title">Sender Phone Number</div>
              <div className="verify-row">
                <input
                  value={cbeBirrPhone}
                  onChange={e => {
                    setCbeBirrPhone(e.target.value)
                    if (/^2519\d{8}$/.test(e.target.value.trim())) setCbeBirrPhoneErr('')
                  }}
                  placeholder="2519...."
                  className={cbeBirrPhoneErr ? 'input-error' : ''}
                />
              </div>
              {cbeBirrPhoneErr && <div className="error-text">{cbeBirrPhoneErr}</div>}

              <div className="verify-title">Verify Transaction</div>
              <div className="verify-row">
                <input
                  value={cbeBirrTxn}
                  onChange={e => {
                    setCbeBirrTxn(e.target.value)
                    if (/^[A-Za-z0-9]{8,}$/.test(e.target.value.trim())) setCbeBirrTxnErr('')
                  }}
                  placeholder="Enter CBE Birr transaction num"
                  className={cbeBirrTxnErr ? 'input-error' : ''}
                />
                <button className="verify-btn" disabled={submitting} onClick={() => {
                  const tg = window?.Telegram?.WebApp
                  const phoneOk = /^2519\d{8}$/.test(cbeBirrPhone.trim())
                  if (!phoneOk) { setCbeBirrPhoneErr('Invalid Phone Number'); return }
                  const txnOk = /^[A-Za-z0-9]{8,}$/.test(cbeBirrTxn.trim())
                  if (!txnOk) { setCbeBirrTxnErr('Invalid transaction'); return }
                  setSubmitting(true)
                  try {
                    tg?.sendData(JSON.stringify({ type: 'verify_deposit', method: 'cbe-birr', amount, phone: cbeBirrPhone.trim(), ref: cbeBirrTxn.trim() }))
                    setSubmitMsg('Submitted. Please check the chat with the bot for confirmation.')
                    setTimeout(() => { try { tg?.close?.() } catch {} }, 1200)
                  } finally {
                    setSubmitting(false)
                  }
                }}>{submitting ? 'Sending…' : 'Verify'}</button>
              </div>
              {(cbeBirrTxnErr && <div className="error-text">{cbeBirrTxnErr}</div>)}
              {submitMsg && <div className="hint" style={{color:'#1a7f37'}}>{submitMsg}</div>}
              <div className="hint">E.g Format: FT25160PLPSH88713517</div>
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
                <li>የደረሳችሁን አጭር የጹሁፍ መለክት (SMS) ሙሉዉን ኮፒ (copy) በማረግ ከታሽ ባለው የጹሁፍ ማስገቢያው ላይ ፔስት (paste) በማረግ ይላኩት</li>
              </ol>

              <p style={{margin:'8px 0 12px 0', color:'#333'}}>
              የሚያጋጥማቹ የክፍያ ችግር ካለ ኤጀንቱን ማዋራት ይችላሉ ወይም<a href="https://t.me/cartelabingo_support" target="_blank" rel="noreferrer">@cartelabingo_support</a>በዚ ሰፖርት ማዉራት ይችላሉ።
              </p>

              <div className="verify-title">Verify Transaction</div>
              <div className="verify-row">
                <input
                  value={boaTxn}
                  onChange={e => {
                    setBoaTxn(e.target.value)
                    if (/^[A-Za-z0-9]{8,}$/.test(e.target.value.trim())) setBoaTxnErr('')
                  }}
                  placeholder="Enter BOA transaction number"
                  className={boaTxnErr ? 'input-error' : ''}
                />
                <button className="verify-btn" disabled={submitting} onClick={() => {
                  const tg = window?.Telegram?.WebApp
                  const ok = /^[A-Za-z0-9]{8,}$/.test(boaTxn.trim())
                  if (!ok) { setBoaTxnErr('Invalid transaction'); return }
                  setSubmitting(true)
                  try {
                    tg?.sendData(JSON.stringify({ type: 'verify_deposit', method: 'boa', amount, ref: boaTxn.trim() }))
                    setSubmitMsg('Submitted. Please check the chat with the bot for confirmation.')
                    setTimeout(() => { try { tg?.close?.() } catch {} }, 1200)
                  } finally {
                    setSubmitting(false)
                  }
                }}>{submitting ? 'Sending…' : 'Verify'}</button>
              </div>
              {boaTxnErr && <div className="error-text">{boaTxnErr}</div>}
              {submitMsg && <div className="hint" style={{color:'#1a7f37'}}>{submitMsg}</div>}
              <div className="hint">E.g Format: FT25165P0KSV62395</div>
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
                <li> የደረሳችሁን አጭር የጹሁፍ መለክት (SMS) ሙሉዉን ኮፒ (copy) በማረግ ከታሽ ባለው የጹሁፍ ማስገቢያው ላይ ፔስት (paste) በማረግ ይላኩት</li>
              </ol>

              <p style={{margin:'8px 0 12px 0', color:'#333'}}>
              የሚያጋጥማቹ የክፍያ ችግር ካለ ኤጀንቱን ማዋራት ይችላሉ ወይም <a href="https://t.me/cartelabingo_support" target="_blank" rel="noreferrer">@cartelabingo_support</a> በዚ ሰፖርት ማዉራት ይችላሉ።
              </p>

              <div className="verify-title">Verify Transaction</div>
              <div className="verify-row">
                <input
                  value={cbeTxn}
                  onChange={e => {
                    setCbeTxn(e.target.value)
                    if (/^[A-Za-z0-9]{8,}$/.test(e.target.value.trim())) setCbeTxnErr('')
                  }}
                  placeholder="Enter CBE Bank transaction num"
                  className={cbeTxnErr ? 'input-error' : ''}
                />
                <button className="verify-btn" disabled={submitting} onClick={() => {
                  const tg = window?.Telegram?.WebApp
                  const ok = /^[A-Za-z0-9]{8,}$/.test(cbeTxn.trim())
                  if (!ok) { setCbeTxnErr('Invalid transaction'); return }
                  setSubmitting(true)
                  try {
                    tg?.sendData(JSON.stringify({ type: 'verify_deposit', method: 'cbe', amount, ref: cbeTxn.trim() }))
                    setSubmitMsg('Submitted. Please check the chat with the bot for confirmation.')
                    setTimeout(() => { try { tg?.close?.() } catch {} }, 1200)
                  } finally {
                    setSubmitting(false)
                  }
                }}>{submitting ? 'Sending…' : 'Verify'}</button>
              </div>
              {cbeTxnErr && <div className="error-text">{cbeTxnErr}</div>}
              {submitMsg && <div className="hint" style={{color:'#1a7f37'}}>{submitMsg}</div>}
              <div className="hint">E.g Format: FT25160PLPSH88713517</div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
