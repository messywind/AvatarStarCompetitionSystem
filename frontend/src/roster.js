export const PROFESSIONS = ['生化', '突击', '护卫', '重装']

// Returns { formalCount, counts, errors[] }
export const MAX_SUBSTITUTES = 1

export function validateRoster(players) {
  const formal = players.filter((p) => !p.is_substitute)
  const subs = players.filter((p) => p.is_substitute)
  const counts = Object.fromEntries(PROFESSIONS.map((p) => [p, 0]))
  for (const p of formal) {
    if (counts[p.profession] !== undefined) counts[p.profession] += 1
  }

  const errors = []
  // every player must have a nickname
  if (players.some((p) => !p.nickname || !p.nickname.trim())) {
    errors.push('每位选手都需要填写称呼')
  }
  if (formal.length !== 5) {
    errors.push(`正式队员必须严格为 5 人（当前 ${formal.length} 人）`)
  }
  if (subs.length > MAX_SUBSTITUTES) {
    errors.push(`替补队员最多 ${MAX_SUBSTITUTES} 人（当前 ${subs.length} 人）`)
  }
  for (const prof of PROFESSIONS) {
    const c = counts[prof]
    if (c === 0) errors.push(`职业「${prof}」的人数不得为 0`)
    else if (c > 2) errors.push(`职业「${prof}」的人数不得超过 2 个`)
  }
  return { formalCount: formal.length, counts, errors }
}
