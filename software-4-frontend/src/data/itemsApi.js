import { api } from '../lib/api.js'

export function normalizeScholarship(s) {
  return {
    id: `s-${s.id}`,
    type: 'scholarship',
    source: s.organization || '장학공지',
    title: s.title,
    summary: s.summary || `${s.organization}에서 제공하는 ${s.category} 장학금입니다.`,
    campus: s.campus || '-',
    department: s.target_departments && s.target_departments.length ? s.target_departments.join(', ') : '전체 학과',
    targetGrade: s.target_grades || [1, 2, 3, 4],
    minGpa: s.eligibility && s.eligibility.includes('3.5') ? 3.5 : (s.eligibility && s.eligibility.includes('3.0') ? 3.0 : 0),
    deadline: s.deadline || s.application_end || '',
    views: s.d_day ? Math.max(0, 100 - s.d_day) : 42,
    amount: s.amount ? `${s.amount.toLocaleString()}` : '상세 공고 참조',
    externalUrl: s.detail_url || '#',
    tags: [s.category, '장학', s.organization].filter(Boolean),
    raw: s
  }
}

export function normalizeContest(c) {
  return {
    id: `c-${c.id}`,
    type: 'contest',
    source: c.host || '대회공지',
    title: c.title,
    target: c.target,
    summary: c.description || `${c.host}에서 주최하는 ${c.field} 공모전입니다.`,
    department: '전체 학과',
    mainField: c.field || '-',
    targetGrade: [1, 2, 3, 4, 5, 6],
    minGpa: 0,
    deadline: c.deadline || c.application_end || '',
    views: c.d_day ? Math.max(0, 150 - c.d_day) : 88,
    amount: c.prize ? `최고 상금 ${c.prize.toLocaleString()}` : '상세 공고 참조',
    externalUrl: c.detail_url || '#',
    tags: [c.field, c.host_type, c.participation_type, ...(c.tags || [])].filter(Boolean),
    raw: c
  }
}

export async function fetchItems() {
  try {
    const sRes = await api.getScholarships({ page: 1, size: 100 })
    const cRes = await api.getContests({ page: 1, size: 100 })

    const scholarships = (sRes?.items || []).map(normalizeScholarship)
    const contests = (cRes?.items || []).map(normalizeContest)

    return [...scholarships, ...contests]
  } catch (error) {
    console.error('Error fetching items from FastAPI:', error)
    throw error
  }
}

export async function fetchItemById(id) {
  try {
    const [typePrefix, ...rest] = id.split('-')
    const rawId = Number(rest.join('-'))

    if (typePrefix === 's') {
      const s = await api.getScholarshipDetail(rawId)
      return normalizeScholarship(s)
    } else if (typePrefix === 'c') {
      const c = await api.getContestDetail(rawId)
      return normalizeContest(c)
    }
    return null
  } catch (error) {
    console.error(`Error fetching item detail by id ${id}:`, error)
    throw error
  }
}
