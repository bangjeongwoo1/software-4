-- =====================================================
-- Kangwon scholarship renewal schema for Supabase
-- Based on kangwon_scholarship_crawling_design.md
-- =====================================================

DROP TABLE IF EXISTS public.notice_detail_2 CASCADE;
DROP TABLE IF EXISTS public.notice_detail_1 CASCADE;
DROP TABLE IF EXISTS public.customized_detail_2 CASCADE;
DROP TABLE IF EXISTS public.customized_detail_1 CASCADE;
DROP TABLE IF EXISTS public.scholarship CASCADE;
DROP TABLE IF EXISTS public.source_site CASCADE;


-- =====================================================
-- 1. source_site
-- =====================================================

CREATE TABLE public.source_site (
    site_id BIGSERIAL PRIMARY KEY,
    site_name TEXT NOT NULL UNIQUE,
    base_url TEXT,
    site_type TEXT NOT NULL DEFAULT 'scholarship',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- =====================================================
-- 2. scholarship: common parent table
-- =====================================================

CREATE TABLE public.scholarship (
    scholarship_id BIGSERIAL PRIMARY KEY,
    site_id BIGINT REFERENCES public.source_site(site_id) ON DELETE SET NULL,
    source_type TEXT NOT NULL CHECK (source_type IN ('customized', 'notice')),
    title TEXT NOT NULL,
    detail_url TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'closed', 'upcoming')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- =====================================================
-- 3. customized_detail_1: customized list-level data
-- =====================================================

CREATE TABLE public.customized_detail_1 (
    customized_detail_id BIGSERIAL PRIMARY KEY,
    scholarship_id BIGINT NOT NULL UNIQUE REFERENCES public.scholarship(scholarship_id) ON DELETE CASCADE,
    detail_url TEXT NOT NULL UNIQUE,
    title TEXT,
    scholarship_type TEXT,
    benefit_type TEXT,
    summary TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- =====================================================
-- 4. customized_detail_2: customized detail-level data
-- =====================================================

CREATE TABLE public.customized_detail_2 (
    customized_detail_id BIGSERIAL PRIMARY KEY,
    scholarship_id BIGINT NOT NULL UNIQUE REFERENCES public.scholarship(scholarship_id) ON DELETE CASCADE,
    title TEXT,
    summary TEXT,
    campus_text TEXT,
    scholarship_type TEXT,
    benefit_type TEXT,
    nationality_type TEXT,
    student_type TEXT,
    grade_min INT,
    grade_max INT,
    income_level_min INT,
    income_level_max INT,
    enrollment_type TEXT,
    department_humanities BOOLEAN,
    department_science BOOLEAN,
    department_engineering BOOLEAN,
    department_arts BOOLEAN,
    credit_prev_value DOUBLE PRECISION,
    gpa_prev_semester_value DOUBLE PRECISION,
    gpa_total_value DOUBLE PRECISION,
    amount_text TEXT,
    selection_period_text TEXT,
    requires_recommendation BOOLEAN,
    requires_recommendation_text TEXT,
    selection_method_text TEXT,
    eligibility_text TEXT,
    application_method_text TEXT,
    related_document_text TEXT,
    note_text TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- =====================================================
-- 5. notice_detail_1: notice list-level data
-- =====================================================

CREATE TABLE public.notice_detail_1 (
    notice_detail_id BIGSERIAL PRIMARY KEY,
    scholarship_id BIGINT NOT NULL UNIQUE REFERENCES public.scholarship(scholarship_id) ON DELETE CASCADE,
    detail_url TEXT NOT NULL UNIQUE,
    is_notice BOOLEAN,
    campus_text TEXT,
    title TEXT,
    author TEXT,
    registered_at TEXT,
    view_count INT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- =====================================================
-- 6. notice_detail_2: notice detail-level data
-- =====================================================

CREATE TABLE public.notice_detail_2 (
    notice_detail_id BIGSERIAL PRIMARY KEY,
    scholarship_id BIGINT NOT NULL UNIQUE REFERENCES public.scholarship(scholarship_id) ON DELETE CASCADE,
    title TEXT,
    campus_text TEXT,
    author TEXT,
    contact_phone TEXT,
    raw_text TEXT,
    attachment_file_url TEXT,
    attachment_file_type TEXT,
    image_file_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- =====================================================
-- Indexes
-- =====================================================

CREATE INDEX idx_scholarship_site_id ON public.scholarship(site_id);
CREATE INDEX idx_scholarship_source_type ON public.scholarship(source_type);
CREATE INDEX idx_scholarship_status ON public.scholarship(status);
CREATE INDEX idx_customized_grade ON public.customized_detail_2(grade_min, grade_max);
CREATE INDEX idx_customized_income ON public.customized_detail_2(income_level_min, income_level_max);
CREATE INDEX idx_notice_registered_at ON public.notice_detail_1(registered_at);


-- =====================================================
-- updated_at trigger
-- =====================================================

CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_source_site_updated_at
BEFORE UPDATE ON public.source_site
FOR EACH ROW
EXECUTE FUNCTION public.set_updated_at();

CREATE TRIGGER trg_scholarship_updated_at
BEFORE UPDATE ON public.scholarship
FOR EACH ROW
EXECUTE FUNCTION public.set_updated_at();

CREATE TRIGGER trg_customized_detail_1_updated_at
BEFORE UPDATE ON public.customized_detail_1
FOR EACH ROW
EXECUTE FUNCTION public.set_updated_at();

CREATE TRIGGER trg_customized_detail_2_updated_at
BEFORE UPDATE ON public.customized_detail_2
FOR EACH ROW
EXECUTE FUNCTION public.set_updated_at();

CREATE TRIGGER trg_notice_detail_1_updated_at
BEFORE UPDATE ON public.notice_detail_1
FOR EACH ROW
EXECUTE FUNCTION public.set_updated_at();

CREATE TRIGGER trg_notice_detail_2_updated_at
BEFORE UPDATE ON public.notice_detail_2
FOR EACH ROW
EXECUTE FUNCTION public.set_updated_at();
