/**
 * Format a UTC datetime string into user's local time display.
 * @param {string | number | Date} value - UTC datetime string or Date
 * @param {Intl.DateTimeFormatOptions} options - Additional formatting options
 * @returns {string}
 */
export function formatLocalDateTime(value, options = {}) {
  if (!value) return '-'

  const date = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(date.getTime())) {
    return typeof value === 'string' ? value : '-'
  }

  const formatter = new Intl.DateTimeFormat(undefined, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: options.includeSeconds ? '2-digit' : undefined,
    hour12: false,
    ...options,
  })

  return formatter.format(date)
}

