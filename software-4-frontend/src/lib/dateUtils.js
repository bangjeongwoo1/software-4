export function parseRobustDate(dateStr) {
  if (!dateStr || typeof dateStr !== 'string') return null
  
  // 1. Clean up dots and slashes (e.g. 2026.05.15 -> 2026-05-15)
  let cleaned = dateStr.replace(/\./g, '-').replace(/\//g, '-').trim()
  
  // 2. Try to extract YYYY-MM-DD
  const match = cleaned.match(/(\d{4})-(\d{1,2})-(\d{1,2})/)
  if (match) {
    const year = parseInt(match[1])
    const month = parseInt(match[2]) - 1
    const day = parseInt(match[3])
    return new Date(year, month, day)
  }
  
  // 3. Fallback to default parser
  const parsed = new Date(cleaned)
  return isNaN(parsed.getTime()) ? null : parsed
}
