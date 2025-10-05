import React, { useEffect } from 'react'
import './deposit.css'

export default function Deposit() {
  const params = new URLSearchParams(window.location.search)
  const amount = params.get('amount') || '—'

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
          <button key={b.key} className="bank-card" onClick={() => alert(`${b.name} selected`) }>
            <img src={b.img} alt={b.name} />
            <span>{b.name}</span>
          </button>
        ))}
      </div>

      <footer className="deposit-footer">
        <span>Copyright © Allora-Groups 2025</span>
      </footer>
    </div>
  )
}
