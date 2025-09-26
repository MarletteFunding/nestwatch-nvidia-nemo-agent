# NestWatch Theme System

An additive design system for the NestWatch SRE dashboard, implemented behind the `THEME_NESTWATCH` feature flag to ensure zero breaking changes.

## 🎯 Overview

The NestWatch theme system provides:
- Modern visual tokens (colors, shadows, radii)
- Consistent icon system with severity-based colors
- Reusable component classes
- Dark/light theme support
- Accessibility-first design
- Reduced motion support

## 🚀 Usage

### Enabling the Theme

Set the feature flag in your environment:
```bash
NEXT_PUBLIC_THEME_NESTWATCH=true
```

Or enable it dynamically:
```javascript
localStorage.setItem('THEME_NESTWATCH', 'true');
```

### Using Icons

```tsx
import { CriticalDiamond, WarningTriangle, HawkGeo } from '@/ui/icons/nestwatch';

// Basic usage
<CriticalDiamond className="text-red-600" />

// With custom size
<WarningTriangle size={32} className="text-orange-500" />

// Brand icon for Hawky
<HawkGeo className="text-lime-600" />
```

### Using Component Classes

```tsx
// Priority chips
<div className="nw-chip nw-chip--p1">Critical Event</div>
<div className="nw-chip nw-chip--p2">High Priority</div>
<div className="nw-chip nw-chip--p3">Medium Priority</div>

// Cards
<div className="nw-card p-6">Regular card</div>
<div className="nw-card nw-card--critical p-6">Critical event card</div>

// Buttons
<button className="nw-btn--progressive">Primary Action</button>
<button className="nw-btn--action">Secondary Action</button>

// Typography
<h1 className="nw-heading">Main Heading</h1>
<h2 className="nw-subtitle">Section Title</h2>
<p className="nw-body">Body text</p>
<p className="nw-hint">Helper text</p>
```

### Using the HawkyFab Component

```tsx
import { HawkyFab } from '@/ui/fab/HawkyFab';

<HawkyFab onClick={() => openAssistant()} />
```

### Theme Management

```tsx
import { useNestWatchTheme, applyNestWatchTheme } from '@/ui/utils/theme';

const { enabled, theme, toggleTheme } = useNestWatchTheme();

// Toggle theme
toggleTheme('dark');
toggleTheme('light');
toggleTheme('auto');

// Apply theme programmatically
applyNestWatchTheme('dark');
```

## 🎨 Design Tokens

### Colors
- `--nw-navy`: #011835 (Primary dark)
- `--nw-navy-tint`: #092951 (Secondary dark)
- `--nw-peach`: #FF8E6F (Critical/P1)
- `--nw-sunflower`: #FFDC82 (High/P2)
- `--nw-lime`: #B8FF8D (Healthy/Success)
- `--nw-beige`: #FAF7F0 (Light surface)
- `--nw-white`: #FFFFFF (Primary light)

### Radius
- `--nw-radius-sm`: 8px
- `--nw-radius-md`: 12px
- `--nw-radius-lg`: 16px

### Shadows
- `--nw-shadow-sm`: Light shadow for controls
- `--nw-shadow-md`: Medium shadow for cards
- `--nw-shadow-lg`: Large shadow for elevated states

## 📱 Accessibility

- All components include proper focus rings
- WCAG AA contrast ratios maintained
- Reduced motion support via `prefers-reduced-motion`
- Semantic color usage with proper fallbacks
- Screen reader friendly with proper ARIA labels

## 🔧 Development

### Adding New Icons

1. Create SVG in `ui/icons/nestwatch/raw/`
2. Create React component in `ui/icons/nestwatch/`
3. Export from `ui/icons/nestwatch/index.tsx`
4. Add to Storybook stories

### Icon Guidelines

- 24x24 viewBox
- 2px stroke weight
- Rounded geometry consistent with design system
- Both outline and solid variants for status icons
- Proper TypeScript interfaces

### Component Guidelines

- All classes prefixed with `.nw-` to avoid collisions
- Feature flag gated via `[data-nestwatch-theme="true"]`
- Additive only - no modifications to existing components
- Proper hover and focus states
- Transition timing: 150-200ms ease-out

## 🧪 Testing

Run Storybook to see all components:
```bash
npm run storybook
```

Stories available:
- `NestWatch/Icons` - All icon variants
- `NestWatch/HawkyFab` - FAB component
- `NestWatch/Components` - CSS component classes

## 🚫 Non-Breaking Guarantees

- Feature flag disabled by default
- No modifications to existing components
- No changes to existing CSS classes
- All exports are additive
- Existing functionality remains unchanged
- Bundle size impact only when used (tree-shakable)

## 📦 Bundle Impact

When feature flag is disabled:
- Zero runtime impact
- CSS is imported but scoped to `[data-nestwatch-theme="true"]`
- JavaScript exports are tree-shakable

When enabled:
- ~8KB additional CSS
- ~4KB additional JavaScript (icons + components)
- No impact on existing components or functionality
