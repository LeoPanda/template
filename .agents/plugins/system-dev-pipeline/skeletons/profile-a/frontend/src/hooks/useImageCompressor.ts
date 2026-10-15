import { useCallback } from 'react';

interface CompressOptions {
  maxWidth?: number;
  maxHeight?: number;
  quality?: number;
}

export function useImageCompressor() {
  const compressToWebP = useCallback(
    (file: File, options: CompressOptions = {}): Promise<Blob> => {
      const { maxWidth = 700, maxHeight = 700, quality = 0.8 } = options;

      return new Promise((resolve, reject) => {
        const img = new Image();
        img.src = URL.createObjectURL(file);
        img.onload = () => {
          URL.revokeObjectURL(img.src);
          let width = img.width;
          let height = img.height;

          // アスペクト比を維持して最大サイズ内に収める
          if (width > height) {
            if (width > maxWidth) {
              height = Math.round((height * maxWidth) / width);
              width = maxWidth;
            }
          } else {
            if (height > maxHeight) {
              width = Math.round((width * maxHeight) / height);
              height = maxHeight;
            }
          }

          const canvas = document.createElement('canvas');
          canvas.width = width;
          canvas.height = height;
          const ctx = canvas.getContext('2d');
          if (!ctx) {
            reject(new Error('Failed to get canvas 2D context'));
            return;
          }

          ctx.drawImage(img, 0, 0, width, height);
          canvas.toBlob(
            (blob) => {
              if (blob) resolve(blob);
              else reject(new Error('Canvas toBlob failed'));
            },
            'image/webp',
            quality
          );
        };
        img.onerror = () => reject(new Error('Failed to load image for compression'));
      });
    },
    []
  );

  return { compressToWebP };
}
