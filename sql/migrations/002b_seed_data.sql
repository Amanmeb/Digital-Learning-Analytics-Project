-- Migration 002b
-- Seed data for static dimension tables
-- CDLAID Analytics Platform

-- DimGrade
INSERT INTO mart.dim_grade (grade_id, grade_level, grade_label) VALUES
    ('GR00',  0, 'Non-grade'),
    ('GR01',  1, 'Grade 1'),
    ('GR02',  2, 'Grade 2'),
    ('GR03',  3, 'Grade 3'),
    ('GR04',  4, 'Grade 4'),
    ('GR05',  5, 'Grade 5'),
    ('GR06',  6, 'Grade 6'),
    ('GR07',  7, 'Grade 7'),
    ('GR08',  8, 'Grade 8'),
    ('GR09',  9, 'Grade 9'),
    ('GR10', 10, 'Grade 10'),
    ('GR11', 11, 'Grade 11'),
    ('GR12', 12, 'Grade 12')
ON CONFLICT DO NOTHING;

-- DimLanguage
INSERT INTO mart.dim_language (language_id, language_name) VALUES
    ('LANG_EN', 'English'),
    ('LANG_AM', 'Amharic'),
    ('LANG_OM', 'Afan Oromo'),
    ('LANG_TI', 'Tigrinya'),
    ('LANG_SO', 'Somali'),
    ('LANG_SI', 'Sidamic'),
    ('LANG_AF', 'Afar')
ON CONFLICT DO NOTHING;

-- DimContentType
INSERT INTO mart.dim_content_type (content_type_id, content_type_name) VALUES
    ('CT_VIDEO',  'Video'),
    ('CT_TEXT',   'Textbook'),
    ('CT_QUIZ',   'Quiz'),
    ('CT_EXAM',   'Exam'),
    ('CT_SIM',    'Simulation'),
    ('CT_GAME',   'Game'),
    ('CT_RADIO',  'Radio'),
    ('CT_LAB',    'Science Lab'),
    ('CT_CODE',   'Coding'),
    ('CT_PDF',    'PDF'),
    ('CT_AUDIO',  'Audio')
ON CONFLICT DO NOTHING;

-- DimPlatform
INSERT INTO mart.dim_platform
    (platform_id, platform_name, platform_type, is_offline, tracking_method, tracking_depth, has_ai) VALUES
    ('PLT_OA',     'Offline Academy',   'Offline',   TRUE,  'xapi_custom',  'full',       FALSE),
    ('PLT_CS',     'Camara Studio',     'Offline',   TRUE,  'xapi_custom',  'full',       FALSE),
    ('PLT_GAME',   'Game Apps',         'Offline',   TRUE,  'xapi_custom',  'full',       FALSE),
    ('PLT_RADIO',  'Radio',             'Offline',   TRUE,  'xapi_custom',  'partial',    FALSE),
    ('PLT_LAB',    'Science Lab',       'Offline',   TRUE,  'xapi_custom',  'full',       FALSE),
    ('PLT_MANUAL', 'Parenting Manuals', 'Offline',   TRUE,  'xapi_native',  'click_only', FALSE),
    ('PLT_PHET',   'PhET Simulations',  'Offline',   TRUE,  'scorm',        'partial',    FALSE),
    ('PLT_RACHEL', 'Rachel',            'Offline',   TRUE,  'url_only',     'click_only', FALSE),
    ('PLT_H5P',    'H5P',               'Offline',   TRUE,  'xapi_native',  'full',       FALSE),
    ('PLT_W3',     'W3Schools',         'Flexible',  FALSE, 'url_only',     'click_only', FALSE),
    ('PLT_LTI',    'LTI External',      'Flexible',  FALSE, 'lti',          'partial',    FALSE),
    ('PLT_SCORM',  'SCORM Package',     'Offline',   TRUE,  'scorm',        'partial',    FALSE)
ON CONFLICT DO NOTHING;

-- DimAIService
INSERT INTO mart.dim_ai_service (ai_service_id, ai_type, ai_scope, ai_mode, description) VALUES
    ('AI_ASSIST', 'AI Assistance', 'CurriculumOnly', 'moodle_plugin',  'Camara AI Assistant built into Moodle'),
    ('AI_QUERY',  'AI Query',      'GeneralQuery',   'standalone_app', 'Standalone AI query application')
ON CONFLICT DO NOTHING;

-- DimRole
INSERT INTO mart.dim_role (role_id, role_name) VALUES
    ('ROL_STU',   'Student'),
    ('ROL_TEA',   'Teacher'),
    ('ROL_PRIN',  'Principal'),
    ('ROL_VPRIN', 'Vice Principal'),
    ('ROL_DEPT',  'Department Head'),
    ('ROL_ADM',   'School Admin'),
    ('ROL_CURR',  'Curriculum Coordinator'),
    ('ROL_ICT',   'ICT Coordinator'),
    ('ROL_SNE',   'Special Needs Coordinator'),
    ('ROL_REG',   'Regional Monitor'),
    ('ROL_PROG',  'Programme Officer')
ON CONFLICT DO NOTHING;

-- DimRegion -- Ethiopia starter set
INSERT INTO mart.dim_region (region_id, region_name, country) VALUES
    ('ET-AA', 'Addis Ababa',        'Ethiopia'),
    ('ET-OR', 'Oromia',             'Ethiopia'),
    ('ET-AM', 'Amhara',             'Ethiopia'),
    ('ET-TI', 'Tigray',             'Ethiopia'),
    ('ET-SO', 'Somali',             'Ethiopia'),
    ('ET-AF', 'Afar',               'Ethiopia'),
    ('ET-BN', 'Benshangul-Gumuz',   'Ethiopia'),
    ('ET-GA', 'Gambella',           'Ethiopia'),
    ('ET-HA', 'Harari',             'Ethiopia'),
    ('ET-SN', 'SNNPR',              'Ethiopia'),
    ('ET-SW', 'South West Ethiopia','Ethiopia'),
    ('ET-SI', 'Sidama',             'Ethiopia'),
    ('ET-DD', 'Dire Dawa',          'Ethiopia'),
    ('ET-CN', 'Central Ethiopia',   'Ethiopia')
ON CONFLICT DO NOTHING;

-- DimSubject -- starter set
INSERT INTO mart.dim_subject (subject_id, subject_name) VALUES
    ('SUBJ_MATH',  'Mathematics'),
    ('SUBJ_ENG',   'English'),
    ('SUBJ_AMH',   'Amharic'),
    ('SUBJ_SCI',   'General Science'),
    ('SUBJ_BIO',   'Biology'),
    ('SUBJ_CHEM',  'Chemistry'),
    ('SUBJ_PHY',   'Physics'),
    ('SUBJ_SOC',   'Social Studies'),
    ('SUBJ_HIST',  'History'),
    ('SUBJ_GEO',   'Geography'),
    ('SUBJ_CIV',   'Civics and Ethics'),
    ('SUBJ_ICT',   'ICT and Computing'),
    ('SUBJ_PE',    'Physical Education'),
    ('SUBJ_ART',   'Art and Music'),
    ('SUBJ_REL',   'Religious Education')
ON CONFLICT DO NOTHING;
