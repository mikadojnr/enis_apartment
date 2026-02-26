import fs from 'fs';
import path from 'path';
import archiver from 'archiver';

const projectRoot = '/vercel/share/v0-project';
const distDir = path.join(projectRoot, 'dist');

// Create dist directory if it doesn't exist
if (!fs.existsSync(distDir)) {
  fs.mkdirSync(distDir, { recursive: true });
}

const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
const zipPath = path.join(distDir, `eni-apartments-complete-${timestamp}.zip`);

// Files and directories to exclude
const excludePatterns = [
  '.git',
  'node_modules',
  '__pycache__',
  '.venv',
  'venv',
  '.env.local',
  '.pytest_cache',
  '.vscode',
  '.idea',
  'dist',
  '.DS_Store',
  '*.pyc',
  '*.pyo'
];

function shouldExclude(filePath) {
  return excludePatterns.some(pattern => {
    if (pattern.includes('*')) {
      const regex = new RegExp(pattern.replace(/\*/g, '.*'));
      return regex.test(path.basename(filePath));
    }
    return filePath.includes(pattern);
  });
}

function addDirToZip(zipArchive, dirPath, zipPath = '') {
  const items = fs.readdirSync(dirPath);
  
  for (const item of items) {
    const itemPath = path.join(dirPath, item);
    const itemZipPath = path.join(zipPath, item);
    
    if (shouldExclude(itemPath)) {
      console.log(`[v0] Excluding: ${itemPath}`);
      continue;
    }
    
    const stat = fs.statSync(itemPath);
    
    if (stat.isDirectory()) {
      addDirToZip(zipArchive, itemPath, itemZipPath);
    } else if (stat.isFile()) {
      const fileContent = fs.readFileSync(itemPath);
      zipArchive.append(fileContent, { name: itemZipPath });
      console.log(`[v0] Adding: ${itemZipPath}`);
    }
  }
}

// Create zip
const output = fs.createWriteStream(zipPath);
const archive = archiver('zip', {
  zlib: { level: 9 }
});

output.on('close', () => {
  const stats = fs.statSync(zipPath);
  const sizeInMB = (stats.size / 1024 / 1024).toFixed(2);
  
  console.log(`[v0] ✓ Zip file created successfully!`);
  console.log(`[v0] Location: ${zipPath}`);
  console.log(`[v0] Size: ${sizeInMB} MB`);
  
  // Create latest symlink
  const latestLink = path.join(distDir, 'eni-apartments-latest.zip');
  try {
    if (fs.existsSync(latestLink)) {
      fs.unlinkSync(latestLink);
    }
    fs.copyFileSync(zipPath, latestLink);
    console.log(`[v0] Latest link created: ${latestLink}`);
  } catch (err) {
    console.log(`[v0] Note: Could not create latest link (${err.message})`);
  }
});

archive.on('error', (err) => {
  console.error(`[v0] Error creating zip: ${err.message}`);
  process.exit(1);
});

output.on('error', (err) => {
  console.error(`[v0] Stream error: ${err.message}`);
  process.exit(1);
});

console.log(`[v0] Creating zip file: ${zipPath}`);
console.log(`[v0] Project root: ${projectRoot}`);

archive.pipe(output);

try {
  addDirToZip(archive, projectRoot, 'eni-apartments');
  archive.finalize();
} catch (err) {
  console.error(`[v0] Error: ${err.message}`);
  process.exit(1);
}
