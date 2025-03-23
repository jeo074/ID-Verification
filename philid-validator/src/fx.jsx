export function dataURLToFile(dataURL, fileName) {
  // Decode the base64 string into binary data
  const arr = dataURL.split(",");
  const mime = arr[0].match(/:(.*?);/)[1]; // Extract MIME type
  const bstr = atob(arr[1]); // Decode base64 string
  let n = bstr.length;
  const u8arr = new Uint8Array(n);

  while (n--) {
    u8arr[n] = bstr.charCodeAt(n); // Convert binary string to byte array
  }

  // Create a new file object
  return new File([u8arr], fileName, { type: mime });
}