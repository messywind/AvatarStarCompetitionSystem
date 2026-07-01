import tournamentFirstPoster from './assets/tournament-first-poster.png'
import tournamentAvatar from './assets/tournament-avatar.jpg'

const defaultVisual = {
  avatar: tournamentAvatar,
  poster: tournamentFirstPoster,
}

const tournamentVisuals = [
  {
    id: 1,
    matchName: '第一届',
    avatar: tournamentAvatar,
    poster: tournamentFirstPoster,
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
