import { supabase } from '../lib/supabase.js'

const first = (value) => (Array.isArray(value) ? value[0] : value)

function normalizeScholarship(row) {
  const customList = first(row.customized_detail_1)
  const customDetail = first(row.customized_detail_2)
  const noticeList = first(row.notice_detail_1)
  const noticeDetail = first(row.notice_detail_2)
  const llm = first(row.notice_llm)

  const isCustomized = row.source_type === 'customized'

  return {
    id: `s-${row.scholarship_id}`,
    type: 'scholarship',

    source: isCustomized ? '맞춤형 장학' : '장학 공지',
    title:
      customDetail?.title ||
      customList?.title ||
      noticeDetail?.title ||
      noticeList?.title ||
      llm?.notice_title ||
      row.title,

    summary:
      customDetail?.summary ||
      customList?.summary ||
      llm?.summary ||
      noticeDetail?.raw_text ||
      '',

    department:
      customDetail?.campus_text ||
      noticeDetail?.campus_text ||
      noticeList?.campus_text ||
      '-',

    targetGrade: (customDetail?.grade_min ?? llm?.grade_min ?? customDetail?.grade_max ?? llm?.grade_max) == null
    ? [] 
      : Array.from(
          {
            length:
              (Number(customDetail?.grade_max ?? llm?.grade_max ?? 6)) -
              (Number(customDetail?.grade_min ?? llm?.grade_min ?? 1)) +
              1,
          },
          (_, index) => (Number(customDetail?.grade_min ?? llm?.grade_min ?? 1)) + index
        ).filter((grade) => grade >= 1 && grade <= 6),


    minGpa:
      customDetail?.gpa_prev_semester_value ||
      customDetail?.gpa_total_value ||
      llm?.gpa_min ||
      0,

    deadline:
      llm?.application_close_date ||
      customDetail?.selection_period_text ||
      noticeList?.registered_at ||
      '',

    views: noticeList?.view_count || 0,

    amount:
      customDetail?.amount_text ||
      llm?.amount_text ||
      '-',

    externalUrl:
      row.detail_url,

    tags: [
      '장학',
      isCustomized ? '맞춤형' : '공지',
      customList?.scholarship_type,
      customList?.benefit_type,
      customDetail?.scholarship_type,
      customDetail?.benefit_type,
    ].filter(Boolean),

    raw: {
      scholarship: row,
      customizedDetail1: customList,
      customizedDetail2: customDetail,
      noticeDetail1: noticeList,
      noticeDetail2: noticeDetail,
      noticeLlm: llm,
    },
  }
}

function normalizeContest(row) {
  const contestList = first(row.contest_detail_1)
  const contestDetail = first(row.contest_detail_2)

  return {
    id: `c-${row.contest_id}`,
    type: 'contest',

    source: '콘테스트코리아',
    title:
      contestDetail?.title ||
      contestList?.title ||
      row.title,

    summary:
      contestDetail?.detail_text ||
      '',

    department:
      contestDetail?.target_text ||
      contestList?.target_text ||
      '-',

    mainField:
      contestDetail?.main_field ||
      '-',
    
    targetGrade: [1, 2, 3, 4],
    minGpa: 0,

    deadline:
      contestList?.reception_end ||
      '',

    views: 0,

    amount:
      contestDetail?.award_text ||
      '',

    externalUrl:
      contestDetail?.homepage_url ||
      contestDetail?.application_url ||
      row.detail_url,

    tags: [
      '공모전',
      contestDetail?.main_field,
      contestDetail?.contest_region,
    ].filter(Boolean),

    raw: {
      contest: row,
      contestDetail1: contestList,
      contestDetail2: contestDetail,
    },
  }
}

export async function fetchItems() {
  const { data: scholarships, error: scholarshipError } = await supabase
    .from('scholarship')
    .select(`
      scholarship_id,
      source_type,
      title,
      detail_url,
      status,

      customized_detail_1(
        detail_url,
        title,
        scholarship_type,
        benefit_type,
        summary
      ),

      customized_detail_2(
        title,
        summary,
        campus_text,
        scholarship_type,
        benefit_type,
        nationality_type,
        student_type,
        grade_min,
        grade_max,
        income_level_min,
        income_level_max,
        enrollment_type,
        department_humanities,
        department_science,
        department_engineering,
        department_arts,
        credit_prev_value,
        gpa_prev_semester_value,
        gpa_total_value,
        amount_text,
        selection_period_text,
        requires_recommendation,
        requires_recommendation_text,
        selection_method_text,
        eligibility_text,
        application_method_text,
        related_document_url,
        note_text
      ),

      notice_detail_1(
        detail_url,
        is_notice,
        campus_text,
        title,
        author,
        registered_at,
        view_count
      ),

      notice_detail_2(
        title,
        campus_text,
        author,
        contact_phone,
        raw_text,
        attachment_file_url,
        attachment_file_type,
        image_file_url
      ),

      notice_llm(
        notice_title,
        summary,
        amount_text,
        department_text,
        grade_text,
        grade_min,
        grade_max,
        gpa_min,
        application_start_date,
        application_close_date
      )
    `)

  if (scholarshipError) throw scholarshipError

  const { data: contests, error: contestError } = await supabase
    .from('contest')
    .select(`
      contest_id,
      title,
      detail_url,
      status,

      contest_detail_1(
        detail_url,
        title,
        host,
        target_text,
        reception_start,
        reception_end,
        review_start,
        review_end,
        announcement_date,
        d_day
      ),

      contest_detail_2(
        host_organization,
        main_field,
        target_text,
        reception_period_text,
        review_period_text,
        contest_region,
        award_text,
        homepage_url,
        application_method,
        application_url,
        participation_fee,
        detail_text
      )
    `)

  if (contestError) throw contestError

  return [
    ...(scholarships || []).map(normalizeScholarship),
    ...(contests || []).map(normalizeContest),
  ]
}

export async function fetchItemById(id) {
  const items = await fetchItems()
  return items.find((item) => item.id === id) || null
}
