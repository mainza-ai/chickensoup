//
//  GraphExplorerView.swift
//  Project Chicken Soup
//
//  Created by mck on 6/22/26.
//

import SwiftUI
import SwiftData

struct GraphExplorerView: View {
    @Environment(\.modelContext) private var modelContext
    @Query(sort: \LoreEntity.name) private var allEntities: [LoreEntity]
    
    var backendService = BackendService.shared
    
    @State private var dragOffset = CGSize.zero
    @State private var accumulatedOffset = CGSize.zero
    @State private var zoomScale: CGFloat = 1.0
    @State private var initialZoomScale: CGFloat = 1.0
    private struct EntitySheetItem: Identifiable {
        var id: String { name }
        let name: String
    }
    @State private var selectedEntityItem: EntitySheetItem?

    @Environment(\.horizontalSizeClass) private var horizontalSizeClass
    
    private var isCompact: Bool { horizontalSizeClass == .compact }
    
    var body: some View {
        GeometryReader { geometry in
            let _ = geometry.size // force re-read on layout changes
            ZStack(alignment: .top) {
                // 1. Grid Background
                GridBackgroundView()
                    .background(DesignConstants.cardBackground)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                    .drawingGroup()
                
                // 2. Main Content Canvas
                if allEntities.isEmpty {
                    VStack(spacing: 12) {
                        Image(systemName: "circle.grid.hex")
                            .font(.system(size: 40))
                            .foregroundStyle(.secondary)
                        Text("No Lore Ingested")
                            .font(.headline)
                            .foregroundStyle(DesignConstants.primaryText)
                        Text("Ingest markdown documents using the sidebar panel first.")
                            .font(.subheadline)
                            .foregroundStyle(DesignConstants.secondaryText)
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if let graph = backendService.graph.neighborhood {
                    if geometry.size.width > 50 && geometry.size.height > 50 {
                        // Compute max radius of concentric rings to calculate scaling factor
                        let maxRadius: CGFloat = {
                            let numConnections = graph.connections.count
                            if numConnections == 0 { return 0 }
                            
                            func getRingCapacity(ring: Int) -> Int {
                                switch ring {
                                case 0: return 6
                                case 1: return 12
                                case 2: return 18
                                case 3: return 24
                                default: return 32
                                }
                            }
                            
                            var tempCount = numConnections
                            var ring = 0
                            while tempCount > 0 {
                                tempCount -= getRingCapacity(ring: ring)
                                if tempCount > 0 {
                                    ring += 1
                                }
                            }
                            return 150.0 + CGFloat(ring) * 125.0
                        }()
                        
                        let topOffset: CGFloat = 40
                        let bottomOffset: CGFloat = backendService.graph.showChatHistory ? 220 : 90
                        let visibleWidth = geometry.size.width - (!isCompact && backendService.graph.showNavigator ? 320 : 0)
                        let centerY = max(100.0, topOffset + (geometry.size.height - topOffset - bottomOffset) / 2)
                        let center = CGPoint(x: visibleWidth / 2 + dragOffset.width + accumulatedOffset.width,
                                             y: centerY + dragOffset.height + accumulatedOffset.height)
                        
                        // Determine viewport scaling factor to fit all nodes cleanly inside the canvas
                        let availableHeight = geometry.size.height - topOffset - bottomOffset
                        let availableWidth = visibleWidth
                        let minDimension = min(availableWidth, availableHeight)
                        let maxAllowedRadius = max(50.0, minDimension / 2.0 - 54.0)
                        let baseScale = maxRadius > 0 ? min(1.0, max(0.45, maxAllowedRadius / maxRadius)) : 1.0
                        let scaleFactor = baseScale * zoomScale
                        
                        let currentPositions = computeNodePositions(connections: graph.connections)
                        
                        ZStack {
                            // Tap background to reset zoom/pan
                            Color.clear
                                .contentShape(Rectangle())
                                .onTapGesture(count: 2) {
                                    withAnimation(.spring(response: 0.5, dampingFraction: 0.75)) {
                                        zoomScale = 1.0
                                        initialZoomScale = 1.0
                                        dragOffset = .zero
                                        accumulatedOffset = .zero
                                    }
                                }
                            
                            // Connection Lines (Canvas)
                            Canvas { context, size in
                                for conn in graph.connections {
                                    if let neighborPos = currentPositions[conn.neighbor.id] {
                                        let scaledNeighbor = CGPoint(x: neighborPos.x * scaleFactor, y: neighborPos.y * scaleFactor)
                                        let start = center
                                        let end = CGPoint(x: scaledNeighbor.x + center.x, y: scaledNeighbor.y + center.y)
                                        
                                        let guessedType = guessEntityType(name: conn.neighbor.name, currentType: conn.neighbor.type)
                                        let nodeColor: Color = {
                                            switch guessedType.lowercased() {
                                            case "person": return DesignConstants.systemOrange
                                            case "place": return DesignConstants.systemGreen
                                            case "concept": return DesignConstants.systemPurple
                                            case "project": return Color.pink
                                            case "object": return DesignConstants.systemBlue
                                            case "event": return DesignConstants.systemRed
                                            default: return DesignConstants.secondaryText
                                            }
                                        }()
                                        
                                        var path = Path()
                                        path.move(to: start)
                                        path.addLine(to: end)
                                        context.stroke(path, with: .color(nodeColor.opacity(0.35)), lineWidth: 1.5)
                                    }
                                }
                            }
                            .frame(maxWidth: .infinity, maxHeight: .infinity)
                            
                            // Relationship Labels
                            ForEach(Array(graph.connections.enumerated()), id: \.element.id) { index, conn in
                                if let neighborPos = currentPositions[conn.neighbor.id] {
                                    let scaledNeighbor = CGPoint(x: neighborPos.x * scaleFactor, y: neighborPos.y * scaleFactor)
                                    let start = center
                                    let end = CGPoint(x: scaledNeighbor.x + center.x, y: scaledNeighbor.y + center.y)
                                    
                                    let staggerFactor = 0.42 + 0.16 * Double(index % 2)
                                    let mid = CGPoint(
                                        x: start.x + (end.x - start.x) * CGFloat(staggerFactor),
                                        y: start.y + (end.y - start.y) * CGFloat(staggerFactor)
                                    )
                                    
                                    let guessedType = guessEntityType(name: conn.neighbor.name, currentType: conn.neighbor.type)
                                    let nodeColor: Color = {
                                        switch guessedType.lowercased() {
                                        case "person": return DesignConstants.systemOrange
                                        case "place": return DesignConstants.systemGreen
                                        case "concept": return DesignConstants.systemPurple
                                        case "project": return Color.pink
                                        case "object": return DesignConstants.systemBlue
                                        case "event": return DesignConstants.systemRed
                                        default: return DesignConstants.secondaryText
                                        }
                                    }()
                                    
                                    let labelString = conn.relationshipType.replacingOccurrences(of: "_", with: " ").lowercased()
                                    Text(labelString)
                                        .font(.system(.caption, design: .monospaced).bold())
                                        .foregroundStyle(nodeColor.opacity(0.85))
                                        .padding(.horizontal, 5)
                                        .padding(.vertical, 2.5)
                                        .background(DesignConstants.cardBackground.opacity(0.75))
                                        .clipShape(RoundedRectangle(cornerRadius: 4))
                                        .position(mid)
                                }
                            }
                            
                            // Neighbor Nodes
                            ForEach(graph.connections) { conn in
                                let entity = conn.neighbor
                                if let relativePos = currentPositions[entity.id] {
                                    let scaledPos = CGPoint(x: relativePos.x * scaleFactor, y: relativePos.y * scaleFactor)
                                    let pos = CGPoint(x: scaledPos.x + center.x, y: scaledPos.y + center.y)
                                    
                                    NodeView(name: entity.name, type: entity.type, isFocused: false, scaleFactor: scaleFactor) {
                                        selectEntity(name: entity.name)
                                        #if !os(macOS)
                                        if horizontalSizeClass == .compact {
                                            selectedEntityItem = EntitySheetItem(name: entity.name)
                                        }
                                        #endif
                                    }
                                    .position(pos)
                                }
                            }
                            
                            // Center Focused Node view
                            NodeView(name: graph.entity.name, type: graph.entity.type, isFocused: true, scaleFactor: scaleFactor) {
                                #if !os(macOS)
                                if horizontalSizeClass == .compact {
                                    selectedEntityItem = EntitySheetItem(name: graph.entity.name)
                                }
                                #endif
                            }
                            .position(center)
                        }
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                        .animation(.spring(response: 0.65, dampingFraction: 0.75), value: backendService.graph.neighborhood?.entity.id)
                        .gesture(
                            DragGesture()
                                .onChanged { gesture in
                                    dragOffset = gesture.translation
                                }
                                .onEnded { gesture in
                                    accumulatedOffset.width += gesture.translation.width
                                    accumulatedOffset.height += gesture.translation.height
                                    dragOffset = .zero
                                }
                        )
                        .simultaneousGesture(
                            MagnifyGesture()
                                .onChanged { value in
                                    zoomScale = max(0.4, min(2.0, initialZoomScale * value.magnification))
                                }
                                .onEnded { _ in
                                    initialZoomScale = zoomScale
                                }
                        )
                        
                        // Floating Zoom Controls
                        VStack {
                            Spacer()
                            HStack {
                                Spacer()
                                
                                HStack(spacing: 8) {
                                    Button("Zoom Out", systemImage: "minus.magnifyingglass") {
                                        withAnimation(.spring(response: 0.25, dampingFraction: 0.75)) {
                                            zoomScale = max(0.4, zoomScale - 0.15)
                                            initialZoomScale = zoomScale
                                        }
                                    }
                                    .buttonStyle(.plain)
                                    .labelStyle(.iconOnly)
                                    .frame(width: 26, height: 26)
                                    .background(DesignConstants.controlBackground, in: Circle())
                                    
                                    Text("\(Int(zoomScale * 100))%")
                                        .font(.system(.caption, design: .monospaced).bold())
                                        .foregroundStyle(DesignConstants.primaryText)
                                        .frame(width: 40)
                                    
                                    Button("Zoom In", systemImage: "plus.magnifyingglass") {
                                        withAnimation(.spring(response: 0.25, dampingFraction: 0.75)) {
                                            zoomScale = min(2.0, zoomScale + 0.15)
                                            initialZoomScale = zoomScale
                                        }
                                    }
                                    .buttonStyle(.plain)
                                    .labelStyle(.iconOnly)
                                    .frame(width: 26, height: 26)
                                    .background(DesignConstants.controlBackground, in: Circle())
                                    
                                    Button("Reset Zoom", systemImage: "arrow.counterclockwise") {
                                        withAnimation(.spring(response: 0.5, dampingFraction: 0.75)) {
                                            zoomScale = 1.0
                                            initialZoomScale = 1.0
                                            dragOffset = .zero
                                            accumulatedOffset = .zero
                                        }
                                    }
                                    .buttonStyle(.plain)
                                    .labelStyle(.iconOnly)
                                    .frame(width: 26, height: 26)
                                    .background(DesignConstants.controlBackground, in: Circle())
                                }
                                .padding(.horizontal, 8)
                                .padding(.vertical, 5)
                                .background(DesignConstants.cardBackground.opacity(0.85))
                                .liquidGlass()
                                .padding(.trailing, DesignConstants.standardPadding)
                                .padding(.bottom, backendService.graph.showChatHistory ? 20 : 16)
                            }
                        }
                    } else {
                        Color.clear
                    }
                } else {
                    VStack {
                        ProgressView("Mapping Lore Graph...")
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                }
            }
        }
        .ignoresSafeArea()
        .onAppear {
            dragOffset = .zero
            accumulatedOffset = .zero
        }
        .onChange(of: backendService.graph.neighborhood?.entity.id) { _, _ in
            dragOffset = .zero
            accumulatedOffset = .zero
        }
        #if !os(macOS)
        .sheet(item: $selectedEntityItem) { item in
            NavigationStack {
                EntityDetailView(entityName: item.name, entity: backendService.graph.focusedEntityName == item.name ? backendService.graph.neighborhood?.entity : nil)
                    .toolbar {
                        ToolbarItem(placement: .cancellationAction) {
                            Button("Close") { selectedEntityItem = nil }
                        }
                    }
            }
        }
        #endif
    }
    
    private func selectEntity(name: String) {
        backendService.selectEntity(name, context: modelContext)
    }
    
    private func computeNodePositions(connections: [NeighborhoodConnection]) -> [String: CGPoint] {
        var newPositions: [String: CGPoint] = [:]
        let count = connections.count
        if count == 0 { return [:] }
        
        func getRingCapacity(ring: Int) -> Int {
            switch ring {
            case 0: return 6
            case 1: return 12
            case 2: return 18
            case 3: return 24
            default: return 32
            }
        }
        
        func getRingRadius(ring: Int) -> CGFloat {
            return 150.0 + CGFloat(ring) * 125.0
        }
        
        var rings: [[NeighborhoodConnection]] = [[]]
        var currentRing = 0
        for conn in connections {
            if rings[currentRing].count >= getRingCapacity(ring: currentRing) {
                currentRing += 1
                rings.append([])
            }
            rings[currentRing].append(conn)
        }
        
        for (rIdx, ringConns) in rings.enumerated() {
            let rCount = ringConns.count
            let rRadius = getRingRadius(ring: rIdx)
            let phaseOffset = CGFloat(rIdx) * 0.45
            
            for (idx, conn) in ringConns.enumerated() {
                let angle = (CGFloat(idx) * (2.0 * .pi) / CGFloat(max(1, rCount))) + phaseOffset
                let x = cos(angle) * rRadius
                let y = sin(angle) * rRadius
                newPositions[conn.neighbor.id] = CGPoint(x: x, y: y)
            }
        }
        
        return newPositions
    }
}

struct GridBackgroundView: View {
    var body: some View {
        GeometryReader { geo in
            Path { path in
                let step: CGFloat = 30
                for x in stride(from: 0, to: geo.size.width, by: step) {
                    path.move(to: CGPoint(x: x, y: 0))
                    path.addLine(to: CGPoint(x: x, y: geo.size.height))
                }
                for y in stride(from: 0, to: geo.size.height, by: step) {
                    path.move(to: CGPoint(x: 0, y: y))
                    path.addLine(to: CGPoint(x: geo.size.width, y: y))
                }
            }
            .stroke(Color.primary.opacity(0.035), lineWidth: 0.8)
        }
    }
}

// MARK: - Shared type guessing utility (file scope, accessible from both GraphExplorerView and NodeView)

func guessEntityType(name: String, currentType: String) -> String {
    let cleanType = currentType.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
    if ["person", "place", "concept", "project", "object", "event"].contains(cleanType) {
        return currentType
    }

    let lower = name.lowercased()
    if lower.contains("bob") || lower.contains("tesla") || lower.contains("grusch") || lower.contains("rebelo") || lower.contains("buchanan") || lower.contains("mussolini") || lower.contains("freedman") || lower.contains("brown") || lower.contains("fravor") {
        return "Person"
    }
    if lower.contains("roswell") || lower.contains("varginha") || lower.contains("area") || lower.contains("school") || lower.contains("mount") || lower.contains("brazil") || lower.contains("italy") || lower.contains("zimbabwe") || lower.contains("vatican") || lower.contains("capistrano") {
        return "Place"
    }
    if lower.contains("crash") || lower.contains("incident") || lower.contains("hearings") || lower.contains("disclosure") || lower.contains("encounter") || lower.contains("recovery") || lower.contains("assassination") {
        return "Event"
    }
    if lower.contains("project") || lower.contains("program") || lower.contains("serpo") {
        return "Project"
    }
    if lower.contains("element") || lower.contains("device") || lower.contains("energy") || lower.contains("ray") || lower.contains("craft") || lower.contains("thing") || lower.contains("wireless") {
        return "Object"
    }
    return "Concept"
}

struct NodeView: View {
    let name: String
    let type: String
    let isFocused: Bool
    let scaleFactor: CGFloat
    let action: () -> Void
    
    @State private var isHovered = false
    
    var body: some View {
        let guessedType = guessEntityType(name: name, currentType: type)
        let size = (isFocused ? 48.0 : 36.0) * max(0.5, min(1.2, scaleFactor))
        let buttonSize = max(44.0, size + 16)
        
        let nodeColor: Color = {
            switch guessedType.lowercased() {
            case "person": return DesignConstants.systemOrange
            case "place": return DesignConstants.systemGreen
            case "concept": return DesignConstants.systemPurple
            case "project": return Color.pink
            case "object": return DesignConstants.systemBlue
            case "event": return DesignConstants.systemRed
            default: return DesignConstants.secondaryText
            }
        }()
        
        let symbol: String = {
            switch guessedType.lowercased() {
            case "person": return "person.fill"
            case "place": return "mappin.and.ellipse"
            case "concept": return "lightbulb.fill"
            case "project": return "gearshape.2.fill"
            case "object": return "cube.fill"
            case "event": return "sparkles"
            default: return "doc.text.fill"
            }
        }()
        
        Button(action: action) {
            ZStack {
                // Outer glow
                Circle()
                    .fill(nodeColor.opacity(isFocused ? 0.3 : 0.15))
                    .frame(width: size + 16, height: size + 16)
                    .blur(radius: 6)
                    .scaleEffect(isHovered ? 1.15 : 1.0)
                
                // Glassmorphic border
                Circle()
                    .strokeBorder(
                        LinearGradient(
                            colors: [.white.opacity(0.4), nodeColor.opacity(0.8), .clear],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        ),
                        lineWidth: isFocused ? 2.5 : 1.5
                    )
                    .frame(width: size + 4, height: size + 4)
                
                // Central type-gradient fill
                Circle()
                    .fill(
                        LinearGradient(
                            colors: [nodeColor, nodeColor.opacity(0.6)],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .frame(width: size, height: size)
                    .shadow(color: nodeColor.opacity(0.35), radius: 6, x: 0, y: 3)
                
                // SF Symbol Icon
                Image(systemName: symbol)
                    .font(.system(size: (isFocused ? 18 : 13) * max(0.5, min(1.2, scaleFactor)), weight: .bold))
                    .foregroundStyle(.white)
            }
        }
        .buttonStyle(.plain)
        .frame(width: buttonSize, height: buttonSize)
        .contentShape(Rectangle())
        .scaleEffect(isHovered ? 1.08 : 1.0)
        .animation(.spring(response: 0.25, dampingFraction: 0.7), value: isHovered)
        .onHover { hovering in
            isHovered = hovering
        }
        .overlay(alignment: .top) {
            let formattedName = name.replacingOccurrences(of: "-", with: " ").capitalized
            Text(formattedName)
                .font(.system(.caption, design: .rounded).weight(isFocused ? .bold : .semibold))
                .foregroundStyle(DesignConstants.primaryText)
                .multilineTextAlignment(.center)
                .lineLimit(3)
                .fixedSize(horizontal: false, vertical: true)
                .frame(width: 85 * max(0.6, min(1.2, scaleFactor)))
                .offset(y: buttonSize + 4)
        }
    }
}

