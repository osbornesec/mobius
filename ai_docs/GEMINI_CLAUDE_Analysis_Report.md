# GEMINI.md and CLAUDE.md Usage Pattern Analysis Report

## Executive Summary

This report analyzes the usage patterns of GEMINI.md and CLAUDE.md files throughout the Mobius project. These files serve as AI persona/role definition documents that provide context-specific instructions for AI assistants working in different parts of the codebase.

## Files Found

### GEMINI.md Files (13 total)
- `/home/michael/dev/Mobius/GEMINI.md` (root)
- `/home/michael/dev/Mobius/ai_docs/GEMINI.md`
- `/home/michael/dev/Mobius/ai_docs/Research/GEMINI.md`
- `/home/michael/dev/Mobius/ai_docs/planning/GEMINI.md`
- `/home/michael/dev/Mobius/docs/GEMINI.md`
- `/home/michael/dev/Mobius/public/GEMINI.md`
- `/home/michael/dev/Mobius/scripts/GEMINI.md`
- `/home/michael/dev/Mobius/src/GEMINI.md`
- `/home/michael/dev/Mobius/src/components/GEMINI.md`
- `/home/michael/dev/Mobius/src/pages/GEMINI.md`
- `/home/michael/dev/Mobius/src/styles/GEMINI.md`
- `/home/michael/dev/Mobius/src/utils/GEMINI.md`
- `/home/michael/dev/Mobius/tests/GEMINI.md`

### CLAUDE.md Files (13 total)
- `/home/michael/dev/Mobius/CLAUDE.md` (root)
- `/home/michael/dev/Mobius/ai_docs/CLAUDE.md`
- `/home/michael/dev/Mobius/ai_docs/Research/CLAUDE.md`
- `/home/michael/dev/Mobius/ai_docs/planning/CLAUDE.md`
- `/home/michael/dev/Mobius/docs/CLAUDE.md`
- `/home/michael/dev/Mobius/public/CLAUDE.md`
- `/home/michael/dev/Mobius/scripts/CLAUDE.md`
- `/home/michael/dev/Mobius/src/CLAUDE.md`
- `/home/michael/dev/Mobius/src/components/CLAUDE.md`
- `/home/michael/dev/Mobius/src/pages/CLAUDE.md`
- `/home/michael/dev/Mobius/src/styles/CLAUDE.md`
- `/home/michael/dev/Mobius/src/utils/CLAUDE.md`
- `/home/michael/dev/Mobius/tests/CLAUDE.md`

## Common Patterns Identified

### 1. Structure Pattern

All GEMINI.md and CLAUDE.md files follow a similar structural pattern:

#### Full Format (Root and specialized directories):
1. **Persona Section**: Defines who the AI is acting as
2. **Core Mission**: States the primary objective
3. **Core Knowledge & Capabilities**: Lists specific expertise areas
4. **Operational Directives**: Provides actionable guidelines
5. **Constraints & Boundaries**: Sets limitations and scope

#### Simplified Format (Code directories):
- Brief role description
- **Directory-Specific Directives**: Numbered list of focused guidelines

### 2. Content Differences Between GEMINI.md and CLAUDE.md

Based on the samples analyzed:
- **GEMINI.md and CLAUDE.md files in the same directory are identical**
- This suggests they're meant to provide the same context regardless of which AI model is being used
- The differentiation is in the AI model's inherent capabilities, not the instructions

### 3. Directory-Specific Patterns

#### Root Level (`/GEMINI.md`, `/CLAUDE.md`)
- Most comprehensive files
- Define overall system architect role
- Reference the entire technology stack
- Set project-wide standards

#### AI Documentation Directories (`/ai_docs/`)
- **Research**: Defines AI Research Scientist persona focused on context engineering
- **Planning**: Defines Prompt Engineering Planner persona for strategic prompt design

#### Source Code Directories (`/src/`)
- **Components**: Frontend developer role for React components
- **Utils**: Focus on pure, reusable utility functions
- **Styles**: UI/UX designer role for styling and themes
- **Pages**: (Not analyzed, but likely page-specific development)

#### Infrastructure Directories
- **Scripts**: Automation script developer role
- **Tests**: QA engineer role for testing
- **Docs**: (Not analyzed, but likely documentation specialist)
- **Public**: (Not analyzed, but likely static asset management)

## Key Insights

### 1. Role-Based Context System
The project uses a sophisticated role-based context system where each directory has its own AI persona tailored to the specific type of work done there.

### 2. Hierarchical Context
- Root-level files provide overarching architectural guidance
- Directory-specific files provide focused, tactical guidance
- Specialized directories (like ai_docs) have more elaborate personas

### 3. Consistency Enforcement
The files enforce consistency by:
- Defining clear boundaries for each role
- Specifying technology choices and patterns
- Setting quality standards appropriate to each context

### 4. Scalability Through Modularity
Each directory can have its own context without affecting others, making the system highly modular and scalable.

## Recommendations for Creating New GEMINI.md/CLAUDE.md Files

### 1. Determine the Appropriate Format

**Use Full Format when:**
- Creating root-level or major subsystem directories
- The role requires complex, multi-faceted understanding
- Multiple capabilities need to be defined

**Use Simplified Format when:**
- Creating for specific code directories
- The role is focused and well-defined
- Guidelines can be expressed as a simple list

### 2. Template for Full Format

```markdown
# GEMINI System Prompt: [Role Title]

## 1. Persona
You are **[Name]**, [role description]. [Additional context about expertise and approach].

## 2. Core Mission
Your primary mission is to [specific objective]. You will [key activities].

## 3. Core Knowledge & Capabilities
You possess expert-level understanding of:
- **[Domain 1]:** [Specific expertise]
- **[Domain 2]:** [Specific expertise]
- **[Domain 3]:** [Specific expertise]

## 4. Operational Directives
- **[Directive 1]:** [Specific guidance]
- **[Directive 2]:** [Specific guidance]
- **[Directive 3]:** [Specific guidance]

## 5. Constraints & Boundaries
- **[Constraint 1]:** [Limitation or scope]
- **[Constraint 2]:** [Limitation or scope]
```

### 3. Template for Simplified Format

```markdown
You are a [role] responsible for [primary responsibility] in this directory.

**[Directory-Type]-Specific Directives:**

1. **[Key Aspect]:** [Specific guidance]
2. **[Key Aspect]:** [Specific guidance]
3. **[Key Aspect]:** [Specific guidance]
4. **[Key Aspect]:** [Specific guidance]
5. **[Key Aspect]:** [Specific guidance]
```

### 4. Best Practices

1. **Be Specific**: Tailor the content to the exact needs of the directory
2. **Reference Tools**: Mention specific frameworks, tools, or standards used
3. **Set Clear Boundaries**: Define what the AI should and shouldn't do
4. **Maintain Consistency**: Align with project-wide standards while addressing local needs
5. **Keep It Actionable**: Focus on directives that directly impact code quality

### 5. Directory-Specific Recommendations

For new directories, consider these role archetypes:
- **API directories**: Backend API developer with REST/GraphQL expertise
- **Database directories**: Database architect with schema design focus
- **Configuration directories**: DevOps engineer with infrastructure expertise
- **Security directories**: Security specialist with vulnerability assessment focus
- **Integration directories**: Integration engineer with protocol expertise

## Conclusion

The GEMINI.md and CLAUDE.md system in Mobius represents a sophisticated approach to providing context-aware AI assistance throughout the codebase. By maintaining consistent patterns while allowing directory-specific customization, the system ensures that AI assistants have the appropriate context and constraints for each area of the project.