/** Strip LLM-added emoji/bullet prefixes; UI renders its own bullets. */
export function stripExplanationLinePrefix(line) {
  return String(line || '')
    .replace(/^👉\s*/u, '')
    .replace(/^[-•]\s*/, '')
    // Single-asterisk bullet only; do not strip the opening ** of markdown bold
    .replace(/^\*(?!\*)\s*/, '')
    .trim()
}

export function splitExplanationLines(text) {
  return String(text || '')
    .split('\n')
    .map((line) => stripExplanationLinePrefix(line))
    .filter(Boolean)
}
