// 로그인된 학생 정보 더미
export const currentUser = {
  id: 'won48120',
  name: '김원재',
  department: '소프트웨어학과',
  grade: 3,
  gpa: 3.78,
  interests: ['개발', 'AI', '장학'],
  email: 'won48120@example-univ.ac.kr',
  phone: '010-****-1234',
  // 대회 참여 이력
  contestHistory: [
    {
      id: 'h-1',
      title: '교내 알고리즘 경진대회',
      date: '2025-11-08',
      result: '장려상',
    },
    {
      id: 'h-2',
      title: 'SW 마에스트로 사전 부트캠프',
      date: '2025-08-15',
      result: '수료',
    },
  ],
  // 알림 수신 설정
  notificationPrefs: {
    email: true,
    sms: false,
    push: true,
    deadlineReminderDays: 3,
  },
}
