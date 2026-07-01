// Deadlines are stored/compared as naive local datetimes on the backend, so the
// frontend can slice/format without timezone math.

// ISO ("2026-07-31T14:21:40") -> value for <input type="datetime-local"> ("2026-07-31T14:21")
export function toLocalInput(iso) {
  if (!iso) return ''
  return iso.slice(0, 16)
}

// Human-friendly deadline, e.g. "2026年07月31日 14:21"
export function formatDeadline(iso) {
  if (!iso) return '—'
  const [date, time = ''] = iso.split('T')
  const [y, m, d] = date.split('-')
  return `${y}年${m}月${d}日 ${time.slice(0, 5)}`
}

// Milliseconds remaining until the deadline (may be negative).
export function msUntil(iso) {
  if (!iso) return 0
  return new Date(iso).getTime() - Date.now()
}

// Compact countdown like "剩 3 天 5 小时" / "剩 12 分钟"
export function countdown(iso) {
  const ms = msUntil(iso)
  if (ms <= 0) return '已截止'
  const mins = Math.floor(ms / 60000)
  const days = Math.floor(mins / 1440)
  const hours = Math.floor((mins % 1440) / 60)
  const m = mins % 60
  if (days > 0) return `剩 ${days} 天 ${hours} 小时`
  if (hours > 0) return `剩 ${hours} 小时 ${m} 分钟`
  return `剩 ${m} 分钟`
}
