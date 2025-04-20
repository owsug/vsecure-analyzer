import * as fs from 'fs-extra';
import * as path from 'path';
import JSZip from 'jszip';

/**
 * Recursively adds files and directories to a JSZip instance.
 * @param dir The directory to zip.
 * @param zipFolder The JSZip folder instance.
 */
async function addFilesToZip(dir: string, zipFolder: JSZip): Promise<void> {
  const items = await fs.readdir(dir);
  for (const item of items) {
    const fullPath = path.join(dir, item);
    const stat = await fs.stat(fullPath);
    if (stat.isDirectory()) {
      const subFolder = zipFolder.folder(item);
      if (subFolder) {
        await addFilesToZip(fullPath, subFolder);
      }
    } else {
      const fileData = await fs.readFile(fullPath);
      zipFolder.file(item, fileData);
    }
  }
}

/**
 * Creates a zip archive of the given directory.
 * @param rootPath The root directory to zip.
 * @returns A Buffer containing the zip file.
 */
export async function createZipFromDirectory(rootPath: string): Promise<Buffer> {
  const zip = new JSZip();
  await addFilesToZip(rootPath, zip);
  return zip.generateAsync({ type: 'nodebuffer' });
}