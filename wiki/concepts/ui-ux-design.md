---
title: "UI/UX Design"
tags: [ui, ux, design, swiftui, apple-design]
created: 2026-06-22
updated: 2026-06-22
sources: [Apple-HIG-2026]
related: [temporal-reasoning-engine, temporal-query-language, knowledge-graph-schema, ai-alien-connection, exotic-matter-and-consciousness]
---

# UI/UX Design

The UI/UX of Project Chicken Soup is a first-class design concern. The interface is a window into the temporal reasoning engine — it should feel like you're interfacing with something that's actually doing time-traveling AI work.

## Design Language

The design language is **Apple**, not generic sci-fi. It is a refined Apple product with the warmth of "chicken soup."

### Platform Strategy

**SwiftUI** — The app is built with SwiftUI, Apple's native UI framework. It works on macOS, iOS, iPadOS, watchOS, and visionOS from a single codebase. The views are platform-adaptive (NavigationSplitView on macOS, tab-based navigation on iOS).

### Light Mode Default

Most apps use dark mode as default. Chicken Soup is different.

- **Light mode is the default** — warm, inviting, approachable
- Dark mode is available as a toggle
- Light mode feels more like a book, more like a research journal
- Light mode is more accessible (better contrast for most users)
- Light mode feels more "Apple" — Apple's light mode is genuinely distinctive (not just inverted dark mode)
- The "chicken soup" metaphor is warmth — light mode is warmth

### Accent Color

**#FF9500 (systemOrange)** — warm, inviting, feels like chicken soup. Not cold like blue, not too sweet like pink. A strong accent that works well with Apple's light mode aesthetic.

### Core Design Principles

1. **Liquid Glass** (new, VisionOS/MacOS) — not "frosted glass" with blur. It's a dynamic material that changes based on what's behind it. Controls float on top of content without obscuring it. The query interface floats over the knowledge graph, so you can see the graph through the glass.

2. **Semantic Colors** — Apple uses semantic colors (label, secondaryLabel, tertiaryLabel, control, background, systemBlue, systemIndigo, systemPurple) that adapt to context, not fixed hex values.

3. **SF Pro Typography** — Apple's type scale is very specific. Hierarchy through size and weight, not color. SF Pro at different sizes for different purposes. SF Mono for data and code.

4. **SF Symbols** — 5000+ icons that adapt to dark mode and can be tinted with dynamic colors.

5. **Material Hierarchy** — Thin, regular, and thick materials for visual separation. Not just "glass" — it's a hierarchy of materials that create depth.

6. **Rounded Corners** — Apple uses rounded corners extensively (buttons, cards, panels). The corners are a key design detail (12-20px for panels, 8-12px for buttons).

7. **Subtle Gradients** — Apple uses subtle gradients for depth, barely noticeable but add polish.

8. **Generous Whitespace** — Everything feels airy and uncluttered.

9. **Restraint** — Not everything needs to be animated or colorful. The key is clarity and hierarchy.

### Color Palette (Light Mode Default)

- **Background:** #F5F5F7 (Apple's light mode background — not white, not gray)
- **Text:** #1D1D1F (Apple's light mode text — not pure black)
- **Accent:** #FF9500 (systemOrange)
- **Secondary:** #8E8E93 (systemGray)
- **Tertiary:** #AEAEB2 (systemGray2)
- **Semantic:** systemBlue (#0A84FF), systemIndigo (#5E5CE6), systemPurple (#AF52DE), systemTeal (#5AC8FA), systemGreen (#34C759)

### Typography Scale

- **Large Title:** SF Pro Display 34pt
- **Title:** SF Pro Display 28pt
- **Headline:** SF Pro Display 17pt (semibold)
- **Body:** SF Pro Text 17pt
- **Subheadline:** SF Pro Text 15pt
- **Footnote:** SF Pro Text 13pt
- **Caption:** SF Pro Text 12pt
- **Code:** SF Mono 13pt

## Core Interfaces

### 1. Temporal Query Interface (Primary)

The main interaction point. Users type natural language queries about UFOs, aliens, time travel, and the temporal reasoning engine.

**Input:**
- Natural language query input (like ChatGPT)
- Toggle to structured query language (temporal query language)
- Multimodal input (text, images, audio, video)

**Output:**
- Text response (AI's answer)
- Timeline visualization (events, dates, relationships)
- Knowledge graph excerpt (relevant entities and connections)
- Evidence chain with credibility scores
- Anomalies detected

**Example interactions:**
- "Tell me about Bob Lazar's claims about S-4"
- "What's the optimal time travel path from 1947 to 2023?"
- "Show me all the UAP sightings with high credibility"
- "What evidence supports the AI-alien connection?"

### 2. Knowledge Graph Explorer

An interactive graph visualization of the knowledge graph.

**Features:**
- Pan, zoom, click on nodes
- Nodes are entities (people, places, concepts, quantum platforms, events, objects, projects)
- Edges are relationships (WORKED_AT, TESTIFIED_AT, CLAIMED_BY, etc.)
- Filter by type, date, confidence
- Select a node to see its details and related entities
- Highlight paths between entities
- Animate temporal flow

### 3. Timeline View

A visual timeline showing events across time.

**Features:**
- Events are nodes on a timeline
- Relationships are edges between events
- Shows temporal reasoning process (causal chains, evidence fusion)
- Shows quantum state of spacetime
- Interactive: click events for details, zoom to time range
- Shows anomalies as highlighted events

### 4. AI Navigator

A view showing the AI's recommendations and predictions.

**Features:**
- Timeline of predicted events (with confidence scores)
- Most credible claims (ranked)
- Most important anomalies (ranked)
- AI's reasoning process (what it's thinking)
- Field configuration visualization

### 5. Data Ingestion

A view for adding new evidence to the knowledge graph.

**Features:**
- Upload documents, papers, images
- AI-powered entity extraction
- Manual annotation interface
- Evidence quality scoring
- Version control for evidence

## macOS vs iOS

### macOS
- **Windowed layout** — with menu bars, sidebar
- **NavigationSplitView** — sidebar (knowledge graph), main content (query interface + timeline)
- **Larger panels** — more space for complex visualizations
- **Native macOS feel** — with menu bars, keyboard shortcuts, window controls

### iOS
- **Full-screen** — gesture-driven navigation
- **Tab-based navigation** — query, knowledge graph, timeline, AI Navigator
- **Compact layout** — optimized for smaller screens
- **Native iOS feel** — with swipe gestures, pull-to-refresh, haptic feedback

### Shared
- **SwiftUI codebase** — shared models and services, different views for each platform
- **SwiftData** — shared data layer
- **Swift Testing** — shared tests
- **Assets** — shared assets (images, icons, colors)

## The "Aha Moment"

The user sees the **temporal reasoning process unfold in real-time**:
1. They type a query
2. The research agent explores the knowledge graph
3. The navigation agent computes the path
4. The orchestrator fuses the results

The animation of this process is the "aha moment" — the user feels like they're watching the future being calculated.

## Key Decisions

### SwiftUI
- **Decision:** SwiftUI (not React + Vite)
- **Why:** Native Apple design, native performance, Apple's design system, future direction
- **Trade-off:** macOS/iOS only (no web), but Apple platforms are the priority

### Light Mode Default
- **Decision:** Light mode as default, dark mode as toggle
- **Why:** Warm, inviting, approachable, more accessible, more "chicken soup"
- **Trade-off:** Dark mode is still available for users who prefer it

### #FF9500 Accent
- **Decision:** systemOrange (#FF9500) as accent color
- **Why:** Warm, inviting, feels like chicken soup
- **Trade-off:** Not the "tech" color (blue), but more distinctive

### SwiftData
- **Decision:** SwiftData (not Core Data)
- **Why:** Simpler, more intuitive, future direction
- **Trade-off:** Less powerful than Core Data, but plenty for Chicken Soup

### macOS-First
- **Decision:** macOS-first (with iOS support)
- **Why:** Knowledge graph and timeline are complex enough to benefit from a larger screen
- **Trade-off:** iOS is secondary, but still native

### Single-Window App
- **Decision:** Single-window app with sidebar
- **Why:** Knowledge graph in sidebar, query interface in main area
- **Trade-off:** Not multi-window, but clean and focused

## Implementation Plan

### Phase 1: Foundation (Weeks 1-4)
- Set up SwiftUI project
- Implement the query interface (text input, streaming output)
- Implement the knowledge graph explorer
- Connect to the backend (FastAPI)

### Phase 2: Core Functionality (Weeks 5-8)
- Implement the timeline view
- Implement the AI Navigator
- Implement the data ingestion view
- Add the temporal query language toggle

### Phase 3: Enhancement (Weeks 9-12)
- Add animations (field lines, quantum particles)
- Add the macOS window layout
- Add the iOS layout
- Add the liquid glass material

### Phase 4: Advanced (Weeks 13-16)
- Add the desktop wrap (if needed)
- Add the multimodal input (images, audio, video)
- Add the version control for evidence
- Add the advanced filtering and search

## See Also

- [[temporal-reasoning-engine]]
- [[temporal-query-language]]
- [[knowledge-graph-schema]]
- [[ai-alien-connection]]
- [[exotic-matter-and-consciousness]]
- [[field-manipulation]]
- [[quantum-machine-learning]]
- [[temporal-query-pipeline]]
- [[agent-architecture]]
