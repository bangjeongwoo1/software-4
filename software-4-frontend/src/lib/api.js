const BASE_URL = 'http://localhost:8000'

async function request(endpoint, options = {}) {
  const token = localStorage.getItem('access_token')
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  }

  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    let errorMessage = '요청 중 오류가 발생했습니다.'
    try {
      const errorData = await response.json()
      if (errorData && errorData.detail) {
        errorMessage = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail)
      }
    } catch (e) {
      // JSON 파싱 실패 시 기본 에러 유지
    }
    throw new Error(errorMessage)
  }

  // 204 No Content 등의 경우 처리
  if (response.status === 204) {
    return null
  }

  return response.json()
}

export const api = {
  // Authentication
  async signup(data) {
    return request('/api/auth/signup', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  async login(email, password) {
    const res = await request('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
    if (res && res.access_token) {
      localStorage.setItem('access_token', res.access_token)
      localStorage.setItem('user', JSON.stringify(res.user))
    }
    return res
  },

  logout() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
  },

  // Users
  async getMe() {
    return request('/api/users/me')
  },

  async updateMe(data) {
    return request('/api/users/me', {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  },

  // Scholarships
  async getScholarships(params = {}) {
    const query = new URLSearchParams()
    Object.entries(params).forEach(([key, val]) => {
      if (val !== undefined && val !== null && val !== '') {
        query.append(key, val)
      }
    })
    const queryString = query.toString()
    return request(`/api/scholarships${queryString ? `?${queryString}` : ''}`)
  },

  async getScholarshipDetail(id) {
    return request(`/api/scholarships/${id}`)
  },

  // Contests
  async getContests(params = {}) {
    const query = new URLSearchParams()
    Object.entries(params).forEach(([key, val]) => {
      if (val !== undefined && val !== null && val !== '') {
        query.append(key, val)
      }
    })
    const queryString = query.toString()
    return request(`/api/contests${queryString ? `?${queryString}` : ''}`)
  },

  async getContestDetail(id) {
    return request(`/api/contests/${id}`)
  },

  // Recommendations
  async getRecommendations(type, limit = 10) {
    return request(`/api/recommendations?type=${type}&limit=${limit}`)
  },

  // Notifications
  async getNotifications(params = {}) {
    const query = new URLSearchParams()
    Object.entries(params).forEach(([key, val]) => {
      if (val !== undefined && val !== null && val !== '') {
        query.append(key, val)
      }
    })
    const queryString = query.toString()
    return request(`/api/notifications${queryString ? `?${queryString}` : ''}`)
  },

  async readNotification(id) {
    return request(`/api/notifications/${id}/read`, {
      method: 'PATCH',
    })
  },
}
