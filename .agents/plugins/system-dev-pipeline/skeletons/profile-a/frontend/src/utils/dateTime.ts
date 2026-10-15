/**
 * Aware UTC 日時文字列を日本標準時 (JST) 表記へフォーマットするユーティリティ
 */
export function formatToJST(
  utcDateString: string | null | undefined,
  includeTime: boolean = true
): string {
  if (!utcDateString) return '-';

  try {
    const date = new Date(utcDateString);
    if (isNaN(date.getTime())) return '-';

    const options: Intl.DateTimeFormatOptions = {
      timeZone: 'Asia/Tokyo',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      ...(includeTime
        ? {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false,
          }
        : {}),
    };

    return new Intl.DateTimeFormat('ja-JP', options).format(date);
  } catch {
    return '-';
  }
}
