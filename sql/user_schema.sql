-- =====================================================
-- Kangwon user schema for Supabase
-- Authentication, profile, interests, competition history
-- =====================================================

DROP TABLE IF EXISTS public.user_competition CASCADE;
DROP TABLE IF EXISTS public.user_interest CASCADE;
DROP TABLE IF EXISTS public.user_profile CASCADE;
DROP TABLE IF EXISTS public.user_account CASCADE;


-- =====================================================
-- 1. user_account: authentication
-- =====================================================

CREATE TABLE public.user_account (
    student_id TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- =====================================================
-- 2. user_profile: search condition profile (1:1)
-- =====================================================

CREATE TABLE public.user_profile (
    student_id TEXT PRIMARY KEY REFERENCES public.user_account(student_id) ON DELETE CASCADE,
    name TEXT,
    college TEXT,
    department TEXT,
    phone TEXT,
    email TEXT,
    campus TEXT NOT NULL DEFAULT '춘천' CHECK (campus IN ('춘천', '삼척')),
    scholarship_category TEXT NOT NULL DEFAULT '전체' CHECK (scholarship_category IN ('전체', '국가', '교내', '교외')),
    department_field TEXT CHECK (department_field IN ('인문', '자연', '공학', '예체능')),
    scholarship_nature TEXT CHECK (scholarship_nature IN ('등록금보조', '생활비지원')),
    nationality_type TEXT NOT NULL DEFAULT '내국인' CHECK (nationality_type IN ('내국인', '외국인')),
    student_type TEXT NOT NULL CHECK (student_type IN ('신입생', '재학생')),
    grade TEXT NOT NULL DEFAULT '전학년' CHECK (grade IN ('전학년', '1학년', '2학년', '3학년', '4학년', '5학년')),
    income_level TEXT NOT NULL DEFAULT '제한없음' CHECK (income_level IN ('0-8구간', '9구간', '제한없음')),
    credit_prev DOUBLE PRECISION CHECK (credit_prev IS NULL OR credit_prev >= 0),
    gpa_prev DOUBLE PRECISION CHECK (gpa_prev IS NULL OR gpa_prev BETWEEN 0.0 AND 4.5),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- =====================================================
-- 3. user_interest: interest tags (1:N)
-- =====================================================

CREATE TABLE public.user_interest (
    interest_id BIGSERIAL PRIMARY KEY,
    student_id TEXT NOT NULL REFERENCES public.user_account(student_id) ON DELETE CASCADE,
    interest_name TEXT NOT NULL CHECK (interest_name IN ('장학', '대회', '개발', '데이터', 'AI', '창업', '어학', '근로', '학업')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (student_id, interest_name)
);


-- =====================================================
-- 4. user_competition: competition history (1:N)
-- =====================================================

CREATE TABLE public.user_competition (
    competition_id BIGSERIAL PRIMARY KEY,
    student_id TEXT NOT NULL REFERENCES public.user_account(student_id) ON DELETE CASCADE,
    competition_name TEXT NOT NULL,
    participated_at DATE NOT NULL,
    result TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- =====================================================
-- Indexes
-- =====================================================

CREATE INDEX idx_user_interest_student_id ON public.user_interest(student_id);
CREATE INDEX idx_user_competition_student_id ON public.user_competition(student_id);
CREATE INDEX idx_user_competition_participated_at ON public.user_competition(participated_at DESC);


-- =====================================================
-- updated_at trigger
-- =====================================================

CREATE OR REPLACE FUNCTION public.set_user_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_user_account_updated_at
BEFORE UPDATE ON public.user_account
FOR EACH ROW
EXECUTE FUNCTION public.set_user_updated_at();

CREATE TRIGGER trg_user_profile_updated_at
BEFORE UPDATE ON public.user_profile
FOR EACH ROW
EXECUTE FUNCTION public.set_user_updated_at();

CREATE TRIGGER trg_user_competition_updated_at
BEFORE UPDATE ON public.user_competition
FOR EACH ROW
EXECUTE FUNCTION public.set_user_updated_at();