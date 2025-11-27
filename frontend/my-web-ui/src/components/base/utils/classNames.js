export function cx(...values) {
  return values
    .flat(Infinity)
    .filter((value) => typeof value === 'string' ? value.trim().length > 0 : Boolean(value))
    .join(' ');
}

export function mergeStyle(base = {}, override = {}) {
  return { ...base, ...override };
}

