// Static set of 200 bingo cards derived from fixed seeds.
// Each card is a 5x5 grid using classic B I N G O column ranges with a free center.
// Access via getCard(index) where index is 1..200.

const RANGES = [
  [1, 15],   // B
  [16, 30],  // I
  [31, 45],  // N
  [46, 60],  // G
  [61, 75],  // O
]

function buildCardFromSeed(seed) {
  // Build 5 columns deterministically from the seed
  const columns = RANGES.map(([start, end], idx) => {
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

// Fixed seeds 1..200 create a stable, reproducible set of cards.
const SEEDS = Array.from({ length: 200 }, (_, i) => i + 1)

export const CARDS = SEEDS.map(buildCardFromSeed)
export const CARD_COUNT = CARDS.length

export function getCard(index) {
  // index is 1-based; clamp to valid range
  const i = Math.max(1, Math.min(index, CARDS.length))
  return CARDS[i - 1]
}

export default CARDS
