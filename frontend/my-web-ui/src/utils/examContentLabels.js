/** Display labels for original_texts.exam_content slugs from API */
export const EXAM_CONTENT_LABELS = {
  toefl: 'TOEFL',
  ielts: 'IELTS',
  hsk: 'HSK',
  jlpt: 'JLPT',
  topik: 'TOPIK',
  testdaf: 'TestDaF',
  goethe: 'Goethe',
  dele: 'DELE',
  delf: 'DELF',
  torfl: 'TORFL',
  cet: 'CET',
}

export const formatExamContentLabel = (slug) => {
  if (!slug) return null
  const key = String(slug).trim().toLowerCase()
  return EXAM_CONTENT_LABELS[key] || String(slug).toUpperCase()
}
