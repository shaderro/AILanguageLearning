-- LinkText: backfill preset article difficulty (PostgreSQL / pgAdmin)
-- Match rows by original_texts.language + text_title

ALTER TABLE original_texts ADD COLUMN IF NOT EXISTS difficulty VARCHAR(32);
ALTER TABLE original_texts ADD COLUMN IF NOT EXISTS exam_content VARCHAR(64);

BEGIN;

UPDATE original_texts SET difficulty = 'advanced' WHERE language = '阿拉伯语' AND text_title = 'التحول الرقمي في العالم العربي: التحديات والفرص';
UPDATE original_texts SET exam_content = NULL WHERE language = '阿拉伯语' AND text_title = 'التحول الرقمي في العالم العربي: التحديات والفرص';
UPDATE original_texts SET difficulty = 'beginner' WHERE language = '阿拉伯语' AND text_title = 'الثقافة العربية والتقاليد';
UPDATE original_texts SET exam_content = NULL WHERE language = '阿拉伯语' AND text_title = 'الثقافة العربية والتقاليد';
UPDATE original_texts SET difficulty = 'intermediate' WHERE language = '阿拉伯语' AND text_title = 'الأدب العربي الحديث: بين التراث والمعاصرة';
UPDATE original_texts SET exam_content = NULL WHERE language = '阿拉伯语' AND text_title = 'الأدب العربي الحديث: بين التراث والمعاصرة';
UPDATE original_texts SET difficulty = 'advanced' WHERE language = '德文' AND text_title = 'Ethische Herausforderungen künstlicher Intelligenz';
UPDATE original_texts SET exam_content = NULL WHERE language = '德文' AND text_title = 'Ethische Herausforderungen künstlicher Intelligenz';
UPDATE original_texts SET difficulty = 'beginner' WHERE language = '德文' AND text_title = 'Der kleine Prinz (Auszug)';
UPDATE original_texts SET exam_content = NULL WHERE language = '德文' AND text_title = 'Der kleine Prinz (Auszug)';
UPDATE original_texts SET difficulty = 'intermediate' WHERE language = '德文' AND text_title = 'Die Berliner Mauer: Geschichte und Erinnerung';
UPDATE original_texts SET exam_content = NULL WHERE language = '德文' AND text_title = 'Die Berliner Mauer: Geschichte und Erinnerung';
UPDATE original_texts SET difficulty = 'advanced' WHERE language = '英文' AND text_title = 'Climate Policy: Balancing Economic Growth and Environmental Sustainability';
UPDATE original_texts SET exam_content = NULL WHERE language = '英文' AND text_title = 'Climate Policy: Balancing Economic Growth and Environmental Sustainability';
UPDATE original_texts SET difficulty = 'beginner' WHERE language = '英文' AND text_title = 'Climate Change Today';
UPDATE original_texts SET exam_content = NULL WHERE language = '英文' AND text_title = 'Climate Change Today';
UPDATE original_texts SET difficulty = 'intermediate' WHERE language = '英文' AND text_title = 'The Rise of Streaming Culture';
UPDATE original_texts SET exam_content = NULL WHERE language = '英文' AND text_title = 'The Rise of Streaming Culture';
UPDATE original_texts SET difficulty = 'advanced' WHERE language = '西班牙语' AND text_title = 'Estudios migratorios contemporáneos: perspectivas interdisciplinarias';
UPDATE original_texts SET exam_content = NULL WHERE language = '西班牙语' AND text_title = 'Estudios migratorios contemporáneos: perspectivas interdisciplinarias';
UPDATE original_texts SET difficulty = 'beginner' WHERE language = '西班牙语' AND text_title = 'La cultura de la comida en España';
UPDATE original_texts SET exam_content = NULL WHERE language = '西班牙语' AND text_title = 'La cultura de la comida en España';
UPDATE original_texts SET difficulty = 'intermediate' WHERE language = '西班牙语' AND text_title = 'La evolución de la música latina en el siglo XXI';
UPDATE original_texts SET exam_content = NULL WHERE language = '西班牙语' AND text_title = 'La evolución de la música latina en el siglo XXI';
UPDATE original_texts SET difficulty = 'advanced' WHERE language = '法语' AND text_title = 'L''intégration européenne: défis théoriques et pratiques';
UPDATE original_texts SET exam_content = NULL WHERE language = '法语' AND text_title = 'L''intégration européenne: défis théoriques et pratiques';
UPDATE original_texts SET difficulty = 'beginner' WHERE language = '法语' AND text_title = 'La vie à Paris';
UPDATE original_texts SET exam_content = NULL WHERE language = '法语' AND text_title = 'La vie à Paris';
UPDATE original_texts SET difficulty = 'intermediate' WHERE language = '法语' AND text_title = 'Le cinéma français: entre tradition et innovation';
UPDATE original_texts SET exam_content = NULL WHERE language = '法语' AND text_title = 'Le cinéma français: entre tradition et innovation';
UPDATE original_texts SET difficulty = 'advanced' WHERE language = '日语' AND text_title = '超高齢社会の日本的課題：社会保障制度の再構築';
UPDATE original_texts SET exam_content = NULL WHERE language = '日语' AND text_title = '超高齢社会の日本的課題：社会保障制度の再構築';
UPDATE original_texts SET difficulty = 'beginner' WHERE language = '日语' AND text_title = '日本の四季';
UPDATE original_texts SET exam_content = NULL WHERE language = '日语' AND text_title = '日本の四季';
UPDATE original_texts SET difficulty = 'intermediate' WHERE language = '日语' AND text_title = 'アニメ文化の世界的広がり';
UPDATE original_texts SET exam_content = NULL WHERE language = '日语' AND text_title = 'アニメ文化の世界的広がり';
UPDATE original_texts SET difficulty = 'advanced' WHERE language = '韩语' AND text_title = '한국 디지털 경제의 구조적 특성과 발전 과제';
UPDATE original_texts SET exam_content = NULL WHERE language = '韩语' AND text_title = '한국 디지털 경제의 구조적 특성과 발전 과제';
UPDATE original_texts SET difficulty = 'beginner' WHERE language = '韩语' AND text_title = '한국의 대표 음식';
UPDATE original_texts SET exam_content = NULL WHERE language = '韩语' AND text_title = '한국의 대표 음식';
UPDATE original_texts SET difficulty = 'intermediate' WHERE language = '韩语' AND text_title = 'K팝의 세계적 현상과 문화적 영향';
UPDATE original_texts SET exam_content = NULL WHERE language = '韩语' AND text_title = 'K팝의 세계적 현상과 문화적 영향';
UPDATE original_texts SET difficulty = 'advanced' WHERE language = '俄语' AND text_title = 'Постсоветский переход: политико-экономический анализ';
UPDATE original_texts SET exam_content = NULL WHERE language = '俄语' AND text_title = 'Постсоветский переход: политико-экономический анализ';
UPDATE original_texts SET difficulty = 'beginner' WHERE language = '俄语' AND text_title = 'Русские традиции и праздники';
UPDATE original_texts SET exam_content = NULL WHERE language = '俄语' AND text_title = 'Русские традиции и праздники';
UPDATE original_texts SET difficulty = 'intermediate' WHERE language = '俄语' AND text_title = 'Золотой век русской литературы';
UPDATE original_texts SET exam_content = NULL WHERE language = '俄语' AND text_title = 'Золотой век русской литературы';
UPDATE original_texts SET difficulty = 'advanced' WHERE language = '中文' AND text_title = '人工智能与意识哲学：图灵测试的当代反思';
UPDATE original_texts SET exam_content = NULL WHERE language = '中文' AND text_title = '人工智能与意识哲学：图灵测试的当代反思';
UPDATE original_texts SET difficulty = 'beginner' WHERE language = '中文' AND text_title = '小镇的一天';
UPDATE original_texts SET exam_content = NULL WHERE language = '中文' AND text_title = '小镇的一天';
UPDATE original_texts SET difficulty = 'intermediate' WHERE language = '中文' AND text_title = '数字游民：新时代的工作与生活方式';
UPDATE original_texts SET exam_content = NULL WHERE language = '中文' AND text_title = '数字游民：新时代的工作与生活方式';

COMMIT;

-- Check results:
SELECT language, difficulty, COUNT(*) AS cnt
FROM original_texts
WHERE difficulty IS NOT NULL
GROUP BY language, difficulty
ORDER BY language, difficulty;

SELECT text_id, language, text_title, difficulty, exam_content
FROM original_texts
WHERE difficulty IS NULL AND language IN ('德文','英文','中文','日语','西班牙语','法语','韩语','阿拉伯语','俄语');