export function getBookmarks() {
  const data = localStorage.getItem('bookmarks')
  try {
    return data ? JSON.parse(data) : []
  } catch (e) {
    return []
  }
}

export function toggleBookmark(id) {
  const bookmarks = getBookmarks()
  const has = bookmarks.includes(id)
  const next = has ? bookmarks.filter(b => b !== id) : [...bookmarks, id]
  localStorage.setItem('bookmarks', JSON.stringify(next))
  return next
}

export function isBookmarked(id) {
  return getBookmarks().includes(id)
}
