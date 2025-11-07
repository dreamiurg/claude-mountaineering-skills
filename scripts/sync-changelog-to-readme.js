#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

const CHANGELOG_PATH = path.join(__dirname, '..', 'CHANGELOG.md');
const README_PATH = path.join(__dirname, '..', 'README.md');
const START_MARKER = '<!-- recent-updates:start -->';
const END_MARKER = '<!-- recent-updates:end -->';
const MAX_RELEASES = 5;

function parseChangelog(changelogContent) {
  const releases = [];

  // Match release headers: ## [version](url) (date)
  const releaseRegex = /## \[(\d+\.\d+\.\d+)\]\([^)]+\) \((\d{4}-\d{2}-\d{2})\)/g;
  const matches = [...changelogContent.matchAll(releaseRegex)];

  for (let i = 0; i < matches.length; i++) {
    const match = matches[i];
    const version = match[1];
    const date = match[2];
    const startIndex = match.index + match[0].length;
    const endIndex = i < matches.length - 1 ? matches[i + 1].index : changelogContent.length;

    const releaseContent = changelogContent.substring(startIndex, endIndex);

    // Extract features and fixes
    const features = extractBulletPoints(releaseContent, '### Features');
    const fixes = extractBulletPoints(releaseContent, '### Bug Fixes');

    // Combine all highlights
    const highlights = [...features, ...fixes];

    if (highlights.length > 0) {
      releases.push({ version, date, highlights });
    }
  }

  return releases.slice(0, MAX_RELEASES);
}

function extractBulletPoints(content, sectionHeader) {
  const sectionIndex = content.indexOf(sectionHeader);
  if (sectionIndex === -1) return [];

  const afterSection = content.substring(sectionIndex + sectionHeader.length);
  const nextSectionIndex = afterSection.search(/###\s/);
  const sectionContent = nextSectionIndex === -1
    ? afterSection
    : afterSection.substring(0, nextSectionIndex);

  // Extract bullet points and clean them
  const bulletRegex = /^\* (.+)$/gm;
  const bullets = [...sectionContent.matchAll(bulletRegex)];

  return bullets.map(match => {
    let text = match[1];
    // Remove PR links like ([#123](...))
    text = text.replace(/\s*\(\[#\d+\]\([^)]+\)\)/g, '');
    // Remove commit hashes like ([abc1234](...))
    text = text.replace(/\s*\(\[[a-f0-9]+\]\([^)]+\)\)/g, '');
    return text.trim();
  });
}

function generateSimplifiedFormat(releases) {
  let output = '\n';

  for (const release of releases) {
    output += `### v${release.version} (${release.date})\n`;
    for (const highlight of release.highlights) {
      output += `- ${highlight}\n`;
    }
    output += '\n';
  }

  output += '[View complete changelog →](./CHANGELOG.md)\n';
  return output;
}

function updateReadme(readmeContent, updatedSection) {
  const startIndex = readmeContent.indexOf(START_MARKER);
  const endIndex = readmeContent.indexOf(END_MARKER);

  if (startIndex === -1 && endIndex === -1) {
    console.log('→ No recent-updates markers found in README.md, skipping');
    return null;
  }

  if (startIndex === -1 || endIndex === -1) {
    console.error('✗ Error: Incomplete markers in README.md');
    console.error(`  Found start marker: ${startIndex !== -1}`);
    console.error(`  Found end marker: ${endIndex !== -1}`);
    process.exit(1);
  }

  if (startIndex >= endIndex) {
    console.error('✗ Error: End marker appears before start marker');
    process.exit(1);
  }

  const before = readmeContent.substring(0, startIndex + START_MARKER.length);
  const after = readmeContent.substring(endIndex);

  return before + updatedSection + after;
}

function main() {
  // Check if README exists
  if (!fs.existsSync(README_PATH)) {
    console.error('✗ Error: README.md not found');
    process.exit(1);
  }

  // Check if CHANGELOG exists
  if (!fs.existsSync(CHANGELOG_PATH)) {
    console.log('→ CHANGELOG.md not found, skipping');
    process.exit(0);
  }

  // Read files
  const changelogContent = fs.readFileSync(CHANGELOG_PATH, 'utf8');
  const readmeContent = fs.readFileSync(README_PATH, 'utf8');

  // Parse changelog
  let releases;
  try {
    releases = parseChangelog(changelogContent);
  } catch (error) {
    console.error('✗ Error: Failed to parse CHANGELOG.md');
    console.error(error.message);
    process.exit(1);
  }

  if (releases.length === 0) {
    console.log('→ No releases found in CHANGELOG.md, skipping');
    process.exit(0);
  }

  console.log(`Syncing last ${releases.length} releases from CHANGELOG.md to README.md`);

  // Generate simplified format
  const updatedSection = generateSimplifiedFormat(releases);

  // Update README
  const updatedReadme = updateReadme(readmeContent, updatedSection);

  if (updatedReadme === null) {
    process.exit(0);
  }

  // Write updated README
  try {
    fs.writeFileSync(README_PATH, updatedReadme);
    console.log(`✓ README.md updated with ${releases.length} releases`);
  } catch (error) {
    console.error('✗ Error: Failed to write README.md');
    console.error(error.message);
    process.exit(1);
  }
}

main();
