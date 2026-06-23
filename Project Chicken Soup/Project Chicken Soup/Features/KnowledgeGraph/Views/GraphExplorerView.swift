//
//  GraphExplorerView.swift
//  Project Chicken Soup
//
//  Created by mck on 6/22/26.
//

import SwiftUI
import SwiftData

struct GraphExplorerView: View {
    @Query private var entities: [LoreEntity]
    
    @State private var selectedEntity: LoreEntity?
    @State private var dragOffset = CGSize.zero
    @State private var accumulatedOffset = CGSize.zero
    @State private var nodePositions: [UUID: CGPoint] = [:]
    
    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                Label("Knowledge Graph Explorer", systemImage: "circle.grid.hex.fill")
                    .font(.headline)
                    .foregroundStyle(DesignConstants.primaryText)
                
                Spacer()
                
                if selectedEntity != nil {
                    Button("Clear Selection") {
                        withAnimation(DesignConstants.hoverAnimation) {
                            selectedEntity = nil
                        }
                    }
                    .buttonStyle(.borderless)
                    .font(.caption)
                    .foregroundStyle(DesignConstants.systemOrange)
                }
            }
            .padding(DesignConstants.standardPadding)
            .background(.thinMaterial)
            
            ZStack {
                // Background Grid & Nodes Drawing
                Canvas { gc, size in
                    let center = CGPoint(x: size.width / 2 + dragOffset.width + accumulatedOffset.width,
                                         y: size.height / 2 + dragOffset.height + accumulatedOffset.height)
                    
                    // Draw relationship lines first
                    var path = Path()
                    let nodes = Array(nodePositions.values)
                    if nodes.count > 1 {
                        for i in 0..<nodes.count {
                            for j in (i + 1)..<nodes.count {
                                // Draw lines connecting nodes to represent relationships
                                let start = CGPoint(x: nodes[i].x + center.x, y: nodes[i].y + center.y)
                                let end = CGPoint(x: nodes[j].x + center.x, y: nodes[j].y + center.y)
                                path.move(to: start)
                                // Add a subtle curve
                                let control = CGPoint(x: (start.x + end.x) / 2, y: (start.y + end.y) / 2 - 30)
                                path.addQuadCurve(to: end, control: control)
                            }
                        }
                    }
                    gc.stroke(path, with: .color(DesignConstants.systemOrange.opacity(0.35)), style: StrokeStyle(lineWidth: 1.5, dash: [4, 4]))
                    
                    // Draw Nodes
                    for entity in entities {
                        guard let relativePos = nodePositions[entity.id] else { continue }
                        let pos = CGPoint(x: relativePos.x + center.x, y: relativePos.y + center.y)
                        
                        let isSelected = selectedEntity?.id == entity.id
                        let nodeRadius: CGFloat = isSelected ? 24 : 18
                        let rect = CGRect(x: pos.x - nodeRadius, y: pos.y - nodeRadius, width: nodeRadius * 2, height: nodeRadius * 2)
                        
                        // Node outline glow
                        if isSelected {
                            gc.fill(Path(ellipseIn: rect.insetBy(dx: -4, dy: -4)), with: .color(DesignConstants.systemOrange.opacity(0.25)))
                        }
                        
                        // Main node circle
                        let typeColor: Color = {
                            switch entity.type.lowercased() {
                            case "person": return DesignConstants.systemBlue
                            case "place": return DesignConstants.systemGreen
                            case "concept": return DesignConstants.systemPurple
                            case "project": return DesignConstants.systemOrange
                            default: return DesignConstants.secondaryText
                            }
                        }()
                        
                        gc.fill(Path(ellipseIn: rect), with: .color(typeColor.opacity(0.85)))
                        gc.stroke(Path(ellipseIn: rect), with: .color(.white), lineWidth: 2)
                        
                        // Label text
                        let text = Text(entity.name)
                            .font(.system(size: 10, weight: isSelected ? .bold : .regular))
                            .foregroundStyle(DesignConstants.primaryText)
                        
                        gc.draw(text, at: CGPoint(x: pos.x, y: pos.y + nodeRadius + 8), anchor: .top)
                    }
                }
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
                // Add click detection on the canvas nodes
                .onTapGesture(coordinateSpace: .local) { location in
                    let center = CGPoint(x: 300 / 2 + accumulatedOffset.width,
                                         y: 400 / 2 + accumulatedOffset.height) // Assumes container layout coordinates
                    
                    var clickedNode: LoreEntity? = nil
                    for entity in entities {
                        guard let relativePos = nodePositions[entity.id] else { continue }
                        let pos = CGPoint(x: relativePos.x + center.x, y: relativePos.y + center.y)
                        let dist = sqrt(pow(location.x - pos.x, 2) + pow(location.y - pos.y, 2))
                        if dist < 30 { // Hitbox area
                            clickedNode = entity
                            break
                        }
                    }
                    
                    withAnimation(DesignConstants.hoverAnimation) {
                        selectedEntity = clickedNode
                    }
                }
                
                // Overlay Detail Card if selected
                if let entity = selectedEntity {
                    VStack {
                        Spacer()
                        GraphNodeCard(entity: entity)
                            .padding(DesignConstants.standardPadding)
                            .transition(.move(edge: .bottom).combined(with: .opacity))
                    }
                }
            }
        }
        .background(Color.white)
        .onAppear {
            layoutNodes()
        }
        .onChange(of: entities.count) { _, _ in
            layoutNodes()
        }
    }
    
    // Distribute nodes in a circle or force-directed layout
    private func layoutNodes() {
        guard !entities.isEmpty else { return }
        var newPositions: [UUID: CGPoint] = [:]
        let radius: CGFloat = 100
        
        for (index, entity) in entities.enumerated() {
            let angle = CGFloat(index) * (2.0 * .pi) / CGFloat(entities.count)
            let x = cos(angle) * radius
            let y = sin(angle) * radius
            newPositions[entity.id] = CGPoint(x: x, y: y)
        }
        
        withAnimation(.easeOut(duration: 0.8)) {
            nodePositions = newPositions
        }
    }
}

// Subview for Node details to follow separate View struct rule
struct GraphNodeCard: View {
    let entity: LoreEntity
    
    var body: some View {
        VStack(alignment: .leading, spacing: DesignConstants.compactPadding) {
            HStack {
                Text(entity.name)
                    .font(.headline)
                    .bold()
                Spacer()
                Text(entity.type)
                    .font(.caption)
                    .bold()
                    .padding(.horizontal, 8)
                    .padding(.vertical, 2)
                    .background(DesignConstants.systemOrange.opacity(0.12), in: Capsule())
                    .foregroundStyle(DesignConstants.systemOrange)
            }
            
            Text(entity.summary)
                .font(.subheadline)
                .foregroundStyle(DesignConstants.secondaryText)
                .lineLimit(3)
            
            HStack {
                Label("Credibility: \(Int(entity.confidence * 100))%", systemImage: "checkmark.shield.fill")
                    .font(.caption)
                    .foregroundStyle(DesignConstants.secondaryText)
                Spacer()
                Text("Source: \(entity.source)")
                    .font(.caption)
                    .foregroundStyle(.tertiary)
            }
            .padding(.top, 4)
        }
        .padding(DesignConstants.standardPadding)
        .liquidGlass()
    }
}

#Preview {
    let container = try! ModelContainer(for: LoreEntity.self, configurations: ModelConfiguration(isStoredInMemoryOnly: true))
    let context = container.mainContext
    
    let mock = LoreEntity(name: "Vatican UFO Recovery", type: "Project", summary: "Recovery program initiated by Vatican intelligence following the 1933 Magenta crash.", confidence: 0.96, source: "Historical Leak")
    context.insert(mock)
    
    return GraphExplorerView()
        .modelContainer(container)
        .frame(width: 300, height: 400)
}
