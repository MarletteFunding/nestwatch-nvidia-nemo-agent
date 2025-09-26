#!/usr/bin/env node

// Simple contrast ratio verification for NestWatch theme
// Ensures WCAG AA compliance (4.5:1 for normal text, 3:1 for large text)

const colors = {
  // NestWatch color tokens
  navy: '#011835',
  navyTint: '#092951',
  peach: '#FF8E6F',
  sunflower: '#FFDC82',
  lime: '#B8FF8D',
  beige: '#FAF7F0',
  white: '#FFFFFF',
  g700: '#36445E',
  g500: '#6F7782',
  g300: '#C5CFD9',
};

// Convert hex to RGB
function hexToRgb(hex) {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result ? {
    r: parseInt(result[1], 16),
    g: parseInt(result[2], 16),
    b: parseInt(result[3], 16)
  } : null;
}

// Calculate relative luminance
function getLuminance(r, g, b) {
  const [rs, gs, bs] = [r, g, b].map(c => {
    c = c / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
}

// Calculate contrast ratio
function getContrastRatio(color1, color2) {
  const rgb1 = hexToRgb(color1);
  const rgb2 = hexToRgb(color2);
  
  const l1 = getLuminance(rgb1.r, rgb1.g, rgb1.b);
  const l2 = getLuminance(rgb2.r, rgb2.g, rgb2.b);
  
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  
  return (lighter + 0.05) / (darker + 0.05);
}

// Test combinations
const tests = [
  // Light theme combinations
  { name: 'Navy on White (Light theme text)', fg: colors.navy, bg: colors.white, minRatio: 4.5 },
  { name: 'Navy on Beige (Light theme secondary)', fg: colors.navy, bg: colors.beige, minRatio: 4.5 },
  { name: 'G700 on White (Secondary text)', fg: colors.g700, bg: colors.white, minRatio: 4.5 },
  
  // Dark theme combinations
  { name: 'White on Navy Tint (Dark theme text)', fg: colors.white, bg: colors.navyTint, minRatio: 4.5 },
  { name: 'G300 on Navy Tint (Dark theme secondary)', fg: colors.g300, bg: colors.navyTint, minRatio: 4.5 },
  
  // Priority chip combinations
  { name: 'Navy on Peach (P1 chip)', fg: colors.navy, bg: colors.peach, minRatio: 4.5 },
  { name: 'Navy on Sunflower (P2 chip)', fg: colors.navy, bg: colors.sunflower, minRatio: 4.5 },
  { name: 'Navy on Lime (Healthy chip)', fg: colors.navy, bg: colors.lime, minRatio: 4.5 },
  
  // Button combinations
  { name: 'White on Navy Tint (Progressive button)', fg: colors.white, bg: colors.navyTint, minRatio: 4.5 },
  { name: 'Navy on Lime (Dark theme progressive)', fg: colors.navy, bg: colors.lime, minRatio: 4.5 },
];

console.log('🎨 NestWatch Contrast Verification\n');
console.log('WCAG AA Requirements:');
console.log('- Normal text: 4.5:1 minimum');
console.log('- Large text: 3.0:1 minimum');
console.log('- UI components: 3.0:1 minimum\n');

let allPassed = true;

tests.forEach(test => {
  const ratio = getContrastRatio(test.fg, test.bg);
  const passed = ratio >= test.minRatio;
  const status = passed ? '✅' : '❌';
  
  console.log(`${status} ${test.name}`);
  console.log(`   Ratio: ${ratio.toFixed(2)}:1 (min: ${test.minRatio}:1)`);
  console.log(`   Colors: ${test.fg} on ${test.bg}\n`);
  
  if (!passed) allPassed = false;
});

if (allPassed) {
  console.log('🎉 All contrast tests passed! The NestWatch theme meets WCAG AA requirements.');
  process.exit(0);
} else {
  console.log('⚠️  Some contrast tests failed. Please review the color combinations above.');
  process.exit(1);
}
