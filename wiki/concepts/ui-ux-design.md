---
created: 2026-06-22
protected: true
related:
- temporal-reasoning-engine
- temporal-query-language
- knowledge-graph-schema
- ai-alien-connection
- exotic-matter-and-consciousness
- field-manipulation
- quantum-machine-learning
- temporal-query-pipeline
- agent-architecture
- key-decisions
sources:
- Apple-HIG-2026
- SwiftUI-2026
- SwiftData-2026
tags:
- ui
- ux
- design
- swiftui
- apple-design
- liquid-glass
title: UI/UX Design
updated: '2026-06-25'
---

# UI/UX Design

The UI/UX of Project Chicken Soup is a first-class design concern. The interface is a window into the temporal reasoning engine — it should feel like you're interfacing with something that's actually doing time-traveling AI work.

## Design Language

The design language is **Apple**, not generic sci-fi. It is a refined Apple product with the warmth of "chicken soup."

### Platform Strategy

**50/50 macOS + iOS** — Both platforms are treated as first-class citizens, not one as primary.

**SwiftUI** — The app is built with SwiftUI from a single shared codebase, with structural platform overrides where needed.

**Navigation by device:**

| Device | Container | Behavior |
|--------|-----------|----------|
| macOS | `NavigationSplitView` | True persistent multi-column sidebar |
| iPad (regular width) | `NavigationSplitView` | Desktop treatment with sidebar |
| iPhone (compact) | `TabView` + `NavigationStack` | Bottom tab bar for thumb reach |

**Desktop elements on mobile:**
- **Hover:** `.onHover` works seamlessly — iOS ignores for touch, works with trackpad
- **Keyboard shortcuts:** `.keyboardShortcut` — iOS strips without external keyboard
- **Context menus:** `.contextMenu` — native on both platforms (right-click macOS, long-press iOS)
- **List styles:** `.sidebar` on macOS/iPad, `.insetGrouped` on iPhone
- **Toolbar:** Items in `.navigation` placement on macOS shift to `.bottomBar` on iPhone

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

- **Background:** #F2F2F7 (iOS systemGroupedBackground — clean and modern)
- **Text:** #1D1D1F (Apple primary text — charcoal-black)
- **Accent (Fills/Buttons):** #FF9500 (systemOrange — vibrant saffron/orange)
- **Accent (Text/Labels):** #E65100 (systemOrangeText — high-contrast accessible orange for small labels/text)
- **Secondary:** #6E6E73 (Apple secondary text — slate gray)
- **Semantic Fills:** systemBlue (#007AFF), systemGreen (#34C759), systemPurple (#AF52DE), systemRed (#FF3B30)
- **Semantic Text/Standby:** #1E6B30 (systemGreenText — high-contrast accessible pine-green)

### Contrast & Separation Standards

- **Panel Shadows:** Glassmorphic overlays and floating panels use deep shadows (radius: `12`, offset: `y: 6`, color: `Color.black.opacity(0.14)`) to separate them clearly from the background canvas.
- **Card Outlines:** White cards on light gray backgrounds use a clear border stroke of `Color.black.opacity(0.12)` to prevent edge blending.
- **Sidebar Boundaries:** The sidebar utilizes a 1pt vertical border overlay (`Color.black.opacity(0.12)`) on its trailing edge to demarcate it from the main detail views.
- **Custom Slider Inputs:** Standard sliders are replaced by a custom `PremiumSlider` featuring a thick progress fill (`systemOrange`) and a highly visible white knob outlined with a sharp `systemOrangeText` stroke and drop shadow.

### Typography Scale

- **Large Title:** SF Pro Display 34pt
- **Title:** SF Pro Display 28pt
- **Headline:** SF Pro Display 17pt (semibold)
- **Body:** SF Pro Text 17pt
- **Subheadline:** SF Pro Text 15pt
- **Footnote:** SF Pro Text 13pt
- **Caption:** SF Pro Text 12pt
- **Code:** SF Mono 13pt

## The Layout: Custom, Not Generic

This is not a generic "sidebar + content + tabs" layout. The layout is **custom and unique** to the app.

### The Three Layers

1. **Timeline (base layer)** — Fills the screen. This is the primary view. Events flow along a horizontal axis (time). Branches appear as parallel streams. Depth is used selectively (small amounts of depth throughout).

2. **Query Overlay (control layer)** — Floats over the timeline using Liquid Glass. Can be collapsed to a search bar, expanded to a full overlay, or persistent as a mini-input. The timeline scrolls behind it.

3. **AI Navigator (thinking layer)** — The AI's thinking appears as overlays on the timeline (predictions, suggestions, confidence scores). The AI is not a separate view — it's the layer that sits on top of everything.

### No Generic UI

- **No tabs** — The primary interaction is the timeline itself.
- **No generic sidebar** — The sidebar is a **live knowledge graph** (not a list of items).
- **No generic bottom bar** — The query interface is a **floating overlay** (not a fixed bar).
- **No generic cards** — The timeline is a **spatial layout** where events have depth, relationships, and connections.
- **Custom layout for the timeline** — Using the `Layout` protocol (SwiftUI's custom layout system) to create a timeline that flows naturally.

## Timeline as Primary View

The timeline is the primary view — not the query interface, not the knowledge graph, not the AI Navigator.

### How It Works

- Events flow along a **horizontal axis** (time) on macOS, **vertical axis** (time) on iOS.
- Events are **nodes** on the timeline with depth (shadow, blur, scale).
- Relationships are **edges** between events.
- The timeline is **interactive** — click to expand, drag to pan, scroll to zoom.
- The timeline is **spatial** — events have depth, relationships have depth.

### Branching Timeline (Many-Worlds)

The timeline is **linear yet branching where necessary**:

- **Linear time** — The main timeline is a continuous flow.
- **Branching where needed** — When the many-worlds interpretation applies, branches appear as parallel streams (like a river splitting).
- **Collapsible branches** — You can zoom out to see multiple branches, zoom in to see one.
- **Selectable branches** — Clicking a branch navigates to that timeline.
- **Branches merge** — When two branches converge, they merge back into a single timeline.

### Depth in the Timeline

Apple says: "SwiftUI automatically adds visual effects to views in a 2D window, making them appear to have depth. For content requiring additional depth, RealityKit can be used to create 3D objects, which can be displayed anywhere or within a volume."

For Chicken Soup:

- **2D with depth (default)** — Nodes have shadow, blur, and scale effects that respond to interaction (closer = larger, more prominent). This is "2D with depth" — not a full 3D scene, but depth feels real.
- **Full 3D on demand** — When the user wants to explore a specific relationship or timeline branch, the view transitions to a RealityKit volume (not a window — a volume has no visible frame).
- **Depth is used selectively** — Apple says "incorporating small amounts of depth throughout an interface, even in standard windows, can help it look more natural."

## Query as Floating Overlay

The query interface is a **floating overlay** — not a fixed bar, not a separate view.

### Three States

1. **Collapsed (search bar)** — A small search bar at the top of the screen (like Spotlight).
2. **Expanded (overlay)** — The query interface expands to a full overlay (using `sheet` or `.overlay`).
3. **Persistent (mini-input)** — A persistent query bar at the bottom of the screen (like a mini-input).

### Liquid Glass

The query interface uses **Liquid Glass** (the new Apple material for controls and navigation). It floats above the timeline without obscuring it. The timeline scrolls behind it.

### Search Suggestions

When typing, the query interface shows **search suggestions** (like Apple's search suggestions API). The suggestions are powered by the AI Navigator (predictive suggestions based on the knowledge graph).

## AI Navigator — Integrated, Not Separate

The AI Navigator is **not a separate view** — it's integrated into the main interface.

### AI Inference as Overlays

- **Predictions** appear as overlays on the timeline (e.g., "Predicting this event will occur..." with a confidence score).
- **Suggestions** appear in the query interface (like search suggestions).
- **AI "thinking"** appears as a subtle animation on the timeline (field lines, quantum particles).
- **AI "thoughts"** appear as a side panel (like a chat panel) that can be pinned.

### The AI is Always There

The AI Navigator is the "brain" of the app. It's not a separate view — it's the **layer that sits on top of everything**, making recommendations, predictions, and suggestions. The user always sees the AI's thinking.

## Core Interfaces

### 1. Knowledge Graph Explorer

An interactive graph visualization of the knowledge graph.

**Features:**
- Pan, zoom, click on nodes
- Nodes are entities (people, places, concepts, quantum platforms, events, objects, projects)
- Edges are relationships (WORKED_AT, TESTIFIED_AT, CLAIMED_BY, etc.)
- Filter by type, date, confidence
- Select a node to see its details and related entities
- Highlight paths between entities
- Animate temporal flow

### 2. Timeline View

A visual timeline showing events across time.

**Features:**
- Events are nodes on a timeline
- Relationships are edges between events
- Shows temporal reasoning process (causal chains, evidence fusion)
- Shows quantum state of spacetime
- Interactive: click events for details, zoom to time range
- Shows anomalies as highlighted events
- **Branching timeline** — Many-worlds interpretation visualized as parallel streams
- **Depth** — Events have depth (shadow, blur, scale)

### 3. Data Ingestion

A view for adding new evidence to the knowledge graph.

**Features:**
- Upload documents, papers, images
- AI-powered entity extraction
- Manual annotation interface
- Evidence quality scoring
- Version control for evidence

## macOS vs iOS — 50/50 Parity

Both platforms get equal investment. iOS is not a scaled-down macOS, and macOS is not just an iPad with a keyboard.

### macOS
- **NavigationSplitView** — persistent multi-column sidebar
- **Windowed layout** — menu bars, keyboard shortcuts, window controls
- **Larger panels** — more space for complex knowledge graph and timeline views
- **Custom menu bar commands** — keyboard-first power features
- **Hover states** — progressive disclosure on mouse hover

### iOS
- **Full-screen gesture-driven** — swipe gestures, pull-to-refresh, haptic feedback
- **TabView + NavigationStack** for iPhone, NavigationSplitView for iPad (via horizontalSizeClass)
- **Compact layout** — optimized for smaller screens without losing functionality
- **Bottom toolbar** — key actions at thumb reach

### Shared
- **Single SwiftUI codebase** — platform-adaptive views via conditional compilation
- **Shared SwiftData models and services** — same business logic on both platforms
- **Swift Testing** — shared test suite
- **Shared assets** — images, icons, colors
- **Context menus** — right-click on macOS, long-press on iOS

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

### 50/50 macOS + iOS
- **Decision:** Equal investment in both platforms from a single codebase
- **Why:** The product serves both desktop power users and mobile-first users
- **How:** Structural platform overrides (NavigationSplitView vs TabView), shared models/services
- **Trade-off:** More conditional code, but reaches both audiences natively

### Single-Window App
- **Decision:** Single-window app with sidebar
- **Why:** Knowledge graph in sidebar, query interface in main area
- **Trade-off:** Not multi-window, but clean and focused

### Custom Layout (Not Generic)
- **Decision:** Custom layout with timeline as primary view
- **Why:** The timeline is the core metaphor — it should be the primary interface
- **Trade-off:** More custom code, but more distinctive and memorable

### Floating Query Overlay
- **Decision:** Query interface floats over the timeline using Liquid Glass
- **Why:** The timeline should be visible while typing; the query should feel like a control layer
- **Trade-off:** Slightly more complex than a fixed query bar

### Integrated AI Navigator
- **Decision:** AI Navigator is integrated into the main interface (not a separate view)
- **Why:** The AI's thinking should always be visible; it's the "brain" of the app
- **Trade-off:** The interface is busier, but the AI feels more present

### 2D with Depth (Default), Full 3D on Demand
- **Decision:** Default to 2D with depth; use full 3D volumes for specific features
- **Why:** Apple's guidance: "incorporating small amounts of depth throughout an interface, even in standard windows, can help it look more natural"
- **Trade-off:** Full 3D is more complex, but adds depth when needed

## Implementation Plan

### Phase 1: Foundation (Weeks 1-4)
- Set up SwiftUI project
- Implement the query interface (text input, streaming output)
- Implement the knowledge graph explorer
- Connect to the backend (FastAPI)

### Phase 2: Core Functionality (Weeks 5-8)
- Implement the timeline view
- Implement the AI Navigator (integrated)
- Implement the data ingestion view
- Add the temporal query language toggle

### Phase 3: Enhancement (Weeks 9-12)
- Add animations (field lines, quantum particles)
- Add the macOS window layout
- Add the iOS layout
- Add the liquid glass material
- Implement branching timeline

### Phase 4: Advanced (Weeks 13-16)
- Add the desktop wrap (if needed)
- Add the multimodal input (images, audio, video)
- Add the version control for evidence
- Add the advanced filtering and search
- Add full 3D views (RealityKit)

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
- [[key-decisions]]

