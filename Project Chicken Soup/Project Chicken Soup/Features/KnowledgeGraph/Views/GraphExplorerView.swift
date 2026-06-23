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
    @Query private var allEntities: [LoreEntity]
    
    @StateObject private var backendService = BackendService.shared
    @State private var nodePositions: [UUID: CGPoint] = [:]
    
    @State private var dragOffset = CGSize.zero
    @State private var accumulatedOffset = CGSize.zero
    
    var body: some View {
        GeometryReader { geometry in
            ZStack(alignment: .top) {
                // 1. Grid Background
                GridBackgroundView()
                    .background(DesignConstants.cardBackground)
                
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
                            .font(.caption)
                            .foregroundStyle(DesignConstants.secondaryText)
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if let graph = backendService.neighborhood {
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
                        return 75.0 + CGFloat(ring) * 65.0
                    }()
                    
                    let topOffset: CGFloat = 40
                    let bottomOffset: CGFloat = backendService.showChatHistory ? 280 : 100
                    let visibleWidth = geometry.size.width - (backendService.showNavigator ? 320 : 0)
                    let centerY = topOffset + (geometry.size.height - topOffset - bottomOffset) / 2
                    let center = CGPoint(x: visibleWidth / 2 + dragOffset.width + accumulatedOffset.width,
                                         y: centerY + dragOffset.height + accumulatedOffset.height)
                    
                    // Determine viewport scaling factor to fit all nodes cleanly inside the canvas
                    let availableHeight = geometry.size.height - topOffset - bottomOffset
                    let availableWidth = visibleWidth
                    let minDimension = min(availableWidth, availableHeight)
                    let maxAllowedRadius = max(50.0, minDimension / 2.0 - 54.0)
                    let scaleFactor = maxRadius > 0 ? min(1.0, maxAllowedRadius / maxRadius) : 1.0
                    
                    
                    let currentPositions = nodePositions.isEmpty ? computeNodePositions(connections: graph.connections) : nodePositions
                    
                    Canvas { gc, size in
                        // 1. Draw connection lines
                        for (index, conn) in graph.connections.enumerated() {
                            guard let neighborPos = currentPositions[conn.neighbor.id] else { continue }
                            let scaledNeighbor = CGPoint(x: neighborPos.x * scaleFactor, y: neighborPos.y * scaleFactor)
                            let start = center
                            let end = CGPoint(x: scaledNeighbor.x + center.x, y: scaledNeighbor.y + center.y)
                            
                            let nodeColor: Color = {
                                switch conn.neighbor.type.lowercased() {
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
                            gc.stroke(path, with: .color(nodeColor.opacity(0.3)), lineWidth: 1.2)
                            
                            // Draw label text on the line
                            let staggerFactor = 0.35 + 0.35 * Double(index % 3) / 2.0
                            let mid = CGPoint(
                                x: start.x + (end.x - start.x) * CGFloat(staggerFactor),
                                y: start.y + (end.y - start.y) * CGFloat(staggerFactor)
                            )
                            
                            let labelString = conn.relationshipType.replacingOccurrences(of: "_", with: " ")
                            let text = Text(labelString)
                                .font(.system(size: 6.5, weight: .bold))
                                .foregroundStyle(nodeColor.opacity(0.95))
                            
                            let width = CGFloat(labelString.count) * 4.2 + 8
                            let height: CGFloat = 11
                            let pillRect = CGRect(
                                x: mid.x - width/2,
                                y: mid.y - height/2,
                                width: width,
                                height: height
                            )
                            gc.fill(
                                Path(roundedRect: pillRect, cornerRadius: 3.5),
                                with: .color(DesignConstants.cardBackground.opacity(0.95))
                            )
                            gc.stroke(
                                Path(roundedRect: pillRect, cornerRadius: 3.5),
                                with: .color(nodeColor.opacity(0.3)),
                                lineWidth: 0.7
                            )
                            
                            gc.draw(text, at: mid, anchor: .center)
                        }
                        
                        // 2. Draw neighbor nodes
                        for conn in graph.connections {
                            let entity = conn.neighbor
                            guard let relativePos = currentPositions[entity.id] else { continue }
                            let scaledPos = CGPoint(x: relativePos.x * scaleFactor, y: relativePos.y * scaleFactor)
                            let pos = CGPoint(x: scaledPos.x + center.x, y: scaledPos.y + center.y)
                            drawNode(gc: gc, at: pos, name: entity.name, type: entity.type, isFocused: false, scaleFactor: scaleFactor)
                        }
                        
                        // 3. Draw center focused node
                        drawNode(gc: gc, at: center, name: graph.entity.name, type: graph.entity.type, isFocused: true, scaleFactor: scaleFactor)
                    }
                    .clipped()
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
                    .onTapGesture(coordinateSpace: .local) { location in
                        let visibleWidth = geometry.size.width - (backendService.showNavigator ? 320 : 0)
                        let availableHeight = geometry.size.height - topOffset - bottomOffset
                        let availableWidth = visibleWidth
                        let minDimension = min(availableWidth, availableHeight)
                        let maxAllowedRadius = max(50.0, minDimension / 2.0 - 54.0)
                        let scaleFactor = maxRadius > 0 ? min(1.0, maxAllowedRadius / maxRadius) : 1.0
                        
                        let centerY = topOffset + availableHeight / 2
                        let centerPos = CGPoint(x: visibleWidth / 2 + accumulatedOffset.width,
                                                y: centerY + accumulatedOffset.height)
                        
                        // Click center?
                        let distToCenter = sqrt(pow(location.x - centerPos.x, 2) + pow(location.y - centerPos.y, 2))
                        if distToCenter < 28 {
                            return
                        }
                        
                        // Click neighbor?
                        for conn in graph.connections {
                            guard let relativePos = currentPositions[conn.neighbor.id] else { continue }
                            let scaledPos = CGPoint(x: relativePos.x * scaleFactor, y: relativePos.y * scaleFactor)
                            let pos = CGPoint(x: scaledPos.x + centerPos.x, y: scaledPos.y + centerPos.y)
                            let dist = sqrt(pow(location.x - pos.x, 2) + pow(location.y - pos.y, 2))
                            if dist < 22 {
                                selectEntity(name: conn.neighbor.name)
                                break
                            }
                        }
                    }
                } else {
                    VStack {
                        ProgressView("Mapping Lore Graph...")
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                }
            }
        }
        .onAppear {
            if backendService.focusedEntityName.isEmpty {
                if let first = allEntities.first {
                    selectEntity(name: first.name)
                }
            } else {
                if let graph = backendService.neighborhood {
                    nodePositions = computeNodePositions(connections: graph.connections)
                }
                selectEntity(name: backendService.focusedEntityName)
            }
        }
        .onChange(of: allEntities.count) { _, _ in
            if backendService.focusedEntityName.isEmpty, let first = allEntities.first {
                selectEntity(name: first.name)
            }
        }
        .onChange(of: backendService.neighborhood?.entity.id) { _, _ in
            if let graph = backendService.neighborhood {
                withAnimation(.spring(response: 0.65, dampingFraction: 0.75)) {
                    nodePositions = computeNodePositions(connections: graph.connections)
                    dragOffset = .zero
                    accumulatedOffset = .zero
                }
            }
        }
    }
    
    private func selectEntity(name: String) {
        backendService.selectEntity(name, context: modelContext)
    }
    
    private func wrappedText(_ name: String) -> String {
        let words = name.replacingOccurrences(of: "-", with: " ").split(separator: " ")
        var lines: [String] = []
        var currentLine = ""
        for word in words {
            if currentLine.isEmpty {
                currentLine = String(word)
            } else if currentLine.count + word.count + 1 > 12 {
                lines.append(currentLine)
                currentLine = String(word)
            } else {
                currentLine += " " + word
            }
        }
        if !currentLine.isEmpty {
            lines.append(currentLine)
        }
        return lines.joined(separator: "\n")
    }
    
    private func drawNode(gc: GraphicsContext, at pos: CGPoint, name: String, type: String, isFocused: Bool, scaleFactor: CGFloat) {
        let radius: CGFloat = (isFocused ? 24 : 16) * max(0.8, scaleFactor)
        let rect = CGRect(x: pos.x - radius, y: pos.y - radius, width: radius * 2, height: radius * 2)
        
        let nodeColor: Color = {
            switch type.lowercased() {
            case "person": return DesignConstants.systemOrange
            case "place": return DesignConstants.systemGreen
            case "concept": return DesignConstants.systemPurple
            case "project": return Color.pink
            case "object": return DesignConstants.systemBlue
            case "event": return DesignConstants.systemRed
            default: return DesignConstants.secondaryText
            }
        }()
        
        if isFocused {
            gc.fill(
                Path(ellipseIn: rect.insetBy(dx: -8 * max(0.8, scaleFactor), dy: -8 * max(0.8, scaleFactor))),
                with: .radialGradient(
                    Gradient(colors: [nodeColor.opacity(0.35), nodeColor.opacity(0.0)]),
                    center: pos,
                    startRadius: radius - 2,
                    endRadius: radius + 12 * max(0.8, scaleFactor)
                )
            )
            
            gc.stroke(
                Path(ellipseIn: rect.insetBy(dx: -2, dy: -2)),
                with: .color(nodeColor.opacity(0.4)),
                lineWidth: 1.0
            )
        } else {
            gc.fill(
                Path(ellipseIn: rect.insetBy(dx: -4 * max(0.8, scaleFactor), dy: -4 * max(0.8, scaleFactor))),
                with: .radialGradient(
                    Gradient(colors: [nodeColor.opacity(0.12), nodeColor.opacity(0.0)]),
                    center: pos,
                    startRadius: radius - 2,
                    endRadius: radius + 6 * max(0.8, scaleFactor)
                )
            )
        }
        
        let shading = GraphicsContext.Shading.radialGradient(
            Gradient(colors: [nodeColor.opacity(0.35), nodeColor]),
            center: pos,
            startRadius: 0,
            endRadius: radius
        )
        gc.fill(Path(ellipseIn: rect), with: shading)
        
        gc.stroke(
            Path(ellipseIn: rect),
            with: .color(isFocused ? .white : nodeColor.opacity(0.7)),
            lineWidth: isFocused ? 2.0 : 1.0
        )
        
        let formattedName = wrappedText(name).capitalized
        let fontSize = (isFocused ? 9.5 : 8.0) * max(0.75, min(1.0, scaleFactor))
        let labelText = Text(formattedName)
            .font(.system(size: fontSize, weight: isFocused ? .bold : .medium, design: .default))
            .foregroundStyle(DesignConstants.primaryText)
        
        gc.draw(labelText, at: CGPoint(x: pos.x, y: pos.y + radius + 4), anchor: .top)
    }
    
    private func computeNodePositions(connections: [NeighborhoodConnection]) -> [UUID: CGPoint] {
        var newPositions: [UUID: CGPoint] = [:]
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
            return 75.0 + CGFloat(ring) * 65.0
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

extension View {
    func zPriority(_ index: Double) -> some View {
        self.zIndex(index)
    }
}

