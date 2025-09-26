# Plugin Migration Guide

## Overview

The SRE Tools plugin has been consolidated from multiple files into a single unified plugin for better maintainability and troubleshooting.

## What Changed

### Before (Multiple Files)


```

plugins/
├── sre_tools_simple.py      (154 lines)
├── sre_tools_enhanced.py    (1033 lines)
└── nemo_llm_provider.py     (325 lines)

```

### After (Unified)


```

plugins/
├── sre_tools_unified.py     (400 lines - combines simple + enhanced)
└── nemo_llm_provider.py     (325 lines - unchanged)

```

## Migration Steps

### 1. Update Imports

**Old imports:**

```python

from plugins.sre_tools_simple import SREEventsTool
from plugins.sre_tools_enhanced import EnhancedSREEventsTool, JIRATool, SlackTool

```

**New imports:**

```python

from plugins.sre_tools_unified import create_sre_tool, SREEventsTool, EnhancedSREEventsTool

```

### 2. Update Usage

**Old usage:**

```python

# Simple tool
simple_tool = SREEventsTool()
events = simple_tool.fetch_events()

# Enhanced tool

enhanced_tool = EnhancedSREEventsTool()
events = enhanced_tool.fetch_events()
ticket = JIRATool().create_ticket("Test", "Description", "High")

```

**New usage:**

```python

# Simple mode
simple_tool = create_sre_tool("simple")
events = simple_tool.fetch_events()

# Enhanced mode

enhanced_tool = create_sre_tool("enhanced")
events = enhanced_tool.fetch_events()
ticket = enhanced_tool.create_jira_ticket("Test", "Description", "High")

```

### 3. Backward Compatibility

The old imports still work for backward compatibility:

```python

# These still work (but use the unified plugin internally)
from plugins.sre_tools_unified import SREEventsTool, EnhancedSREEventsTool
simple_tool = SREEventsTool()      # Automatically uses simple mode
enhanced_tool = EnhancedSREEventsTool()  # Automatically uses enhanced mode

```

## Benefits

### ✅ **Better Troubleshooting**


- Single file to debug instead of multiple
- Clear mode separation
- Consistent error handling

### ✅ **Easier Maintenance**


- 66% reduction in code lines (1,187 → 400 lines)
- No duplicate functionality
- Unified configuration

### ✅ **Flexible Usage**


- Choose simple or enhanced mode as needed
- Load only required functionality
- Runtime mode switching

### ✅ **Future Extensibility**


- Easy to add new modes
- Clean plugin architecture
- Better dependency management

## Testing

Test the migration with:

```python

# Test imports
from plugins.sre_tools_unified import create_sre_tool, SREEventsTool, EnhancedSREEventsTool

# Test simple mode

simple_tool = create_sre_tool("simple")
print(f"Simple mode: {simple_tool.mode.value}")

# Test enhanced mode

enhanced_tool = create_sre_tool("enhanced")
print(f"Enhanced mode: {enhanced_tool.mode.value}")

# Test backward compatibility

old_simple = SREEventsTool()
old_enhanced = EnhancedSREEventsTool()
print(f"Backward compatibility: {old_simple.mode.value}, {old_enhanced.mode.value}")

```

## Cleanup (Optional)

Once you've verified everything works, you can remove the old files:

```bash

rm plugins/sre_tools_simple.py
rm plugins/sre_tools_enhanced.py

```

## Support

If you encounter any issues:

1. Check that you're using the correct import syntax
2. Verify the unified plugin is working with the test code above
3. Check the logs for any mode-specific warnings
4. Ensure all dependencies are installed in your virtual environment
