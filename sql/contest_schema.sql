-- =====================================================
-- Contestkorea contest schema for Supabase
-- Based on contestkorea_crawling_design.md
-- =====================================================

DROP TABLE IF EXISTS public.contest_detail_2 CASCADE;
DROP TABLE IF EXISTS public.contest_detail_1 CASCADE;
DROP TABLE IF EXISTS public.contest CASCADE;


-- =====================================================
-- 1. contest: common parent table
-- =====================================================

CREATE TABLE public.contest (
    contest_id BIGSERIAL PRIMARY KEY,
    site_id BIGINT REFERENCES public.source_site(site_id) ON DELETE SET NULL,
    source_type TEXT NOT NULL CHECK (source_type IN ('contestkorea')),
    title TEXT NOT NULL,
    detail_url TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL CHECK (status IN ('upcoming', 'open', 'closing')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- =====================================================
-- 2. contest_detail_1: list-level data
-- =====================================================

CREATE TABLE public.contest_detail_1 (
    contest_detail_id BIGSERIAL PRIMARY KEY,
    contest_id BIGINT NOT NULL UNIQUE REFERENCES public.contest(contest_id) ON DELETE CASCADE,
    detail_url TEXT NOT NULL UNIQUE,
    title TEXT,
    host TEXT,
    target_text TEXT,
    reception_start DATE,
    reception_end DATE,
    review_start DATE,
    review_end DATE,
    announcement_date DATE,
    d_day INT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- =====================================================
-- 3. contest_detail_2: detail-level data
-- =====================================================

CREATE TABLE public.contest_detail_2 (
    contest_detail_id BIGSERIAL PRIMARY KEY,
    contest_id BIGINT NOT NULL UNIQUE REFERENCES public.contest(contest_id) ON DELETE CASCADE,
    host_organization TEXT,
    main_field TEXT,
    target_text TEXT,
    reception_period_text TEXT,
    review_period_text TEXT,
    contest_region TEXT,
    award_text TEXT,
    homepage_url TEXT,
    application_method TEXT,
    application_url TEXT,
    participation_fee TEXT,
    detail_text TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- =====================================================
-- Indexes
-- =====================================================

CREATE INDEX idx_contest_site_id ON public.contest(site_id);
CREATE INDEX idx_contest_source_type ON public.contest(source_type);
CREATE INDEX idx_contest_status ON public.contest(status);
CREATE INDEX idx_contest_detail_1_reception_end ON public.contest_detail_1(reception_end DESC);
CREATE INDEX idx_contest_detail_1_d_day ON public.contest_detail_1(d_day);


-- =====================================================
-- updated_at trigger
-- =====================================================

CREATE OR REPLACE FUNCTION public.set_contest_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_contest_updated_at
BEFORE UPDATE ON public.contest
FOR EACH ROW
EXECUTE FUNCTION public.set_contest_updated_at();

CREATE TRIGGER trg_contest_detail_1_updated_at
BEFORE UPDATE ON public.contest_detail_1
FOR EACH ROW
EXECUTE FUNCTION public.set_contest_updated_at();

CREATE TRIGGER trg_contest_detail_2_updated_at
BEFORE UPDATE ON public.contest_detail_2
FOR EACH ROW
EXECUTE FUNCTION public.set_contest_updated_at();
