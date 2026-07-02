import jsQR from 'jsqr';

export async function decodeQrImage(file: File): Promise<string> {
  if (!file.type.startsWith('image/')) {
    throw new Error('Please upload a QR image file such as PNG, JPG, or WEBP.');
  }

  const imageBitmap = await createImageBitmap(file);
  const canvas = document.createElement('canvas');
  canvas.width = imageBitmap.width;
  canvas.height = imageBitmap.height;
  const context = canvas.getContext('2d');
  if (!context) throw new Error('Could not prepare image canvas for QR decoding.');

  context.drawImage(imageBitmap, 0, 0);
  const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
  const result = jsQR(imageData.data, imageData.width, imageData.height);
  if (!result?.data) {
    throw new Error('No readable QR code was found in this image. Try a clearer image.');
  }

  return result.data;
}
