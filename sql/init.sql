CREATE DATABASE IF NOT EXISTS scholarship_db
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE scholarship_db;

CREATE TABLE IF NOT EXISTS scholarship (
    scholarship_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    title VARCHAR(255) NOT NULL,
    organization VARCHAR(255) NULL,
    scholarship_type VARCHAR(100) NULL,
    benefit_type VARCHAR(100) NULL,
    amount_text VARCHAR(255) NULL,
    campus_text VARCHAR(255) NULL,
    apply_start_date DATE NULL,
    apply_end_date DATE NULL,
    selection_period_text VARCHAR(255) NULL,
    eligibility_text TEXT NULL,
    selection_criteria_text TEXT NULL,
    application_method_text TEXT NULL,
    detail_url VARCHAR(1000) NOT NULL,
    source_site VARCHAR(100) NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'open',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (scholarship_id),
    UNIQUE KEY uq_scholarship_detail_url (detail_url(768)),
    INDEX idx_scholarship_status (status),
    INDEX idx_scholarship_apply_end_date (apply_end_date),
    INDEX idx_scholarship_type (scholarship_type),
    INDEX idx_scholarship_source_site (source_site)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS scholarship_condition (
    condition_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    scholarship_id BIGINT UNSIGNED NOT NULL,
    grade_min TINYINT UNSIGNED NULL,
    grade_max TINYINT UNSIGNED NULL,
    gpa_min DECIMAL(3, 2) NULL,
    credit_min SMALLINT UNSIGNED NULL,
    income_level_min TINYINT UNSIGNED NULL,
    income_level_max TINYINT UNSIGNED NULL,
    is_new_student BOOLEAN NULL,
    is_enrolled_student BOOLEAN NULL,
    is_transfer_student BOOLEAN NULL,
    is_foreign_student BOOLEAN NULL,
    department_text VARCHAR(255) NULL,
    raw_condition_text TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (condition_id),
    UNIQUE KEY uq_condition_scholarship (scholarship_id),
    INDEX idx_condition_grade (grade_min, grade_max),
    INDEX idx_condition_gpa (gpa_min),
    INDEX idx_condition_income (income_level_min, income_level_max),
    CONSTRAINT fk_condition_scholarship
        FOREIGN KEY (scholarship_id)
        REFERENCES scholarship (scholarship_id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

