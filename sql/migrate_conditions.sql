USE scholarship_db;

ALTER TABLE scholarship
    ADD COLUMN benefit_type VARCHAR(100) NULL AFTER scholarship_type,
    ADD COLUMN campus_text VARCHAR(255) NULL AFTER amount_text,
    ADD COLUMN selection_period_text VARCHAR(255) NULL AFTER apply_end_date,
    ADD COLUMN selection_criteria_text TEXT NULL AFTER eligibility_text,
    ADD COLUMN application_method_text TEXT NULL AFTER selection_criteria_text,
    ADD COLUMN source_site VARCHAR(100) NULL AFTER detail_url,
    ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER created_at,
    ADD INDEX idx_scholarship_type (scholarship_type),
    ADD INDEX idx_scholarship_source_site (source_site);

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
