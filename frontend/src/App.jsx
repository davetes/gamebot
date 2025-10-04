import React from 'react'
import Leaderboard from './Leaderboard'
import Play from './Play'
import './leaderboard.css'

function App() {
  const params = new URLSearchParams(window.location.search)
  const mode = params.get('mode')
  if (mode === 'play') {
    return <Play />
  }
  return <Leaderboard />
}

export default App
