import tournamentAvatar from './assets/tournament-avatar.jpg'

// Poster content is now generated from each tournament's configurable data
// (see components/Poster.vue); only the card avatar remains a static asset.
const defaultVisual = {
  avatar: tournamentAvatar,
}

const tournamentVisuals = [
  {
    id: 1,
    matchName: '第一届',
    avatar: tournamentAvatar,
  },
]

export function tournamentVisual(tournament) {
  if (!tournament) return defaultVisual

  return (
    tournamentVisuals.find((item) => item.id === tournament.id) ||
    tournamentVisuals.find((item) => item.matchName && tournament.name.includes(item.matchName)) ||
    defaultVisual
  )
}
