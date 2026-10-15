/**
 * 統一タイムゾーン変換ユーティリティ
 * (DBや通信はAware UTC、UI表示直前でのみJST変換)
 */
export const formatToJST = (utcString: string | null | undefined): string => {
  if (!utcString) return '-';
  try {
    const date = new Date(utcString);
    if (isNaN(date.getTime())) return '-';
    return new Intl.DateTimeFormat('ja-JP', {
      timeZone: 'Asia/Tokyo',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    }).format(date);
  } catch {
    return '-';
  }
};
