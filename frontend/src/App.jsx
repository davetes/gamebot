import React from 'react'
import Leaderboard from './Leaderboard'
import Play from './Play'
import Deposit from './Deposit'
import './leaderboard.css'

function App() {
  const params = new URLSearchParams(window.location.search)
  const mode = params.get('mode')
  if (mode === 'play') {
    return <Play />
  }
  if (mode === 'deposit') {
    return <Deposit />
  }
  return <Leaderboard />
}

export default App
