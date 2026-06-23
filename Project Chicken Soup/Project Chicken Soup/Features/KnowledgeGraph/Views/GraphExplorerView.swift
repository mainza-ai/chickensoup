//
//  GraphExplorerView.swift
//  Project Chicken Soup
//
//  Created by mck on 6/22/26.
//

import SwiftUI
import SwiftData

struct NeighborhoodEntity: Codable, Identifiable, Hashable {
    var id: UUID
    var name: String
    var type: String // "Person", "Place", "Concept", "Object", "Project", "Event"
    var summary: String
    var confidence: Double
    var source: String
    var sources: [String]
    
    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }
    
    static func == (lhs: NeighborhoodEntity, rhs: NeighborhoodEntity) -> Bool {
        lhs.id == rhs.id
    }
}

struct NeighborhoodConnection: Codable, Identifiable {
    var id: UUID { UUID() }
    var relationshipType: String
    var neighbor: NeighborhoodEntity
    
    enum CodingKeys: String, CodingKey {
        case relationshipType = "relationship_type"
        case neighbor
    }
}

struct NeighborhoodResponse: Codable {
    var entity: NeighborhoodEntity
    var connections: [NeighborhoodConnection]
}

struct GraphExplorerView: View {
    @Query private var allEntities: [LoreEntity]
    
    @State private var focusedEntityName: String = ""
    @State private var neighborhood: NeighborhoodResponse? = nil
    @State private var isFetchingNeighborhood = false
    @State private var nodePositions: [UUID: CGPoint] = [:]
    
    @State private var searchText = ""
    @State private var showSuggestions = false
    
    @State private var dragOffset = CGSize.zero
    @State private var accumulatedOffset = CGSize.zero
    @State private var isDetailsExpanded = false
    
    var filteredSuggestions: [LoreEntity] {
        if searchText.isEmpty {
            return Array(allEntities.prefix(5))
        } else {
            return allEntities.filter { $0.name.localizedCaseInsensitiveContains(searchText) }
        }
    }
    
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
                } else if let graph = neighborhood {
                    let topOffset: CGFloat = 60
                    let bottomOffset: CGFloat = isDetailsExpanded ? 290 : 120
                    let centerY = topOffset + (geometry.size.height - topOffset - bottomOffset) / 2
                    let center = CGPoint(x: geometry.size.width / 2 + dragOffset.width + accumulatedOffset.width,
                                         y: centerY + dragOffset.height + accumulatedOffset.height)
                    
                    Canvas { gc, size in
                        // 1. Draw connection lines
                        for conn in graph.connections {
                            guard let neighborPos = nodePositions[conn.neighbor.id] else { continue }
                            let start = center
                            let end = CGPoint(x: neighborPos.x + center.x, y: neighborPos.y + center.y)
                            
                            var path = Path()
                            path.move(to: start)
                            path.addLine(to: end)
                            gc.stroke(path, with: .color(DesignConstants.systemOrange.opacity(0.35)), lineWidth: 1.5)
                            
                            // Draw label text on the line
                            let mid = CGPoint(x: (start.x + end.x) / 2, y: (start.y + end.y) / 2 - 8)
                            let text = Text(conn.relationshipType)
                                .font(.system(size: 7.5, weight: .bold))
                                .foregroundStyle(DesignConstants.systemOrangeText.opacity(0.7))
                            gc.draw(text, at: mid, anchor: .center)
                        }
                        
                        // 2. Draw neighbor nodes
                        for conn in graph.connections {
                            let entity = conn.neighbor
                            guard let relativePos = nodePositions[entity.id] else { continue }
                            let pos = CGPoint(x: relativePos.x + center.x, y: relativePos.y + center.y)
                            drawNode(gc: gc, at: pos, name: entity.name, type: entity.type, isFocused: false)
                        }
                        
                        // 3. Draw center focused node
                        drawNode(gc: gc, at: center, name: graph.entity.name, type: graph.entity.type, isFocused: true)
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
                    .onTapGesture(coordinateSpace: .local) { location in
                        // Detect click on center or neighbors using accurate geometry size and dynamic offsets
                        let topOffset: CGFloat = 60
                        let bottomOffset: CGFloat = isDetailsExpanded ? 290 : 120
                        let centerY = topOffset + (geometry.size.height - topOffset - bottomOffset) / 2
                        let centerPos = CGPoint(x: geometry.size.width / 2 + accumulatedOffset.width,
                                                y: centerY + accumulatedOffset.height)
                        
                        // Click center?
                        let distToCenter = sqrt(pow(location.x - centerPos.x, 2) + pow(location.y - centerPos.y, 2))
                        if distToCenter < 28 {
                            return
                        }
                        
                        // Click neighbor?
                        for conn in graph.connections {
                            guard let relativePos = nodePositions[conn.neighbor.id] else { continue }
                            let pos = CGPoint(x: relativePos.x + centerPos.x, y: relativePos.y + centerPos.y)
                            let dist = sqrt(pow(location.x - pos.x, 2) + pow(location.y - pos.y, 2))
                            if dist < 22 {
                                selectEntity(name: conn.neighbor.name)
                                break
                            }
                        }
                    }
                    
                    // Detail panel overlay at the bottom
                    VStack {
                        Spacer()
                        NeighborhoodNodeCard(entity: graph.entity, isExpanded: $isDetailsExpanded)
                            .padding(DesignConstants.standardPadding)
                            .transition(.move(edge: .bottom).combined(with: .opacity))
                    }
                } else {
                    VStack {
                        ProgressView("Mapping Lore Graph...")
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                }
                
                // 3. Floating Search Bar & Glass Dropdown suggestions overlay
                VStack(spacing: 0) {
                    HStack {
                        Image(systemName: "magnifyingglass")
                            .foregroundStyle(.secondary)
                        
                        TextField("Search Lore Graph...", text: $searchText, onEditingChanged: { isEditing in
                            withAnimation { showSuggestions = isEditing }
                        })
                        .textFieldStyle(.plain)
                        .onSubmit {
                            if let match = allEntities.first(where: { $0.name.localizedCaseInsensitiveContains(searchText) }) {
                                selectEntity(name: match.name)
                                searchText = ""
                                showSuggestions = false
                            }
                        }
                        
                        if !searchText.isEmpty {
                            Button(action: { searchText = "" }) {
                                Image(systemName: "xmark.circle.fill")
                                    .foregroundStyle(.secondary)
                            }
                            .buttonStyle(.plain)
                        }
                        
                        Spacer()
                        
                        if isFetchingNeighborhood {
                            ProgressView()
                                .scaleEffect(0.8)
                        } else {
                            Button(action: {
                                if !focusedEntityName.isEmpty {
                                    Task { await fetchNeighborhood(for: focusedEntityName) }
                                } else if let first = allEntities.first {
                                    selectEntity(name: first.name)
                                }
                            }) {
                                Image(systemName: "arrow.clockwise")
                                    .font(.subheadline)
                                    .foregroundStyle(DesignConstants.systemOrangeText)
                            }
                            .buttonStyle(.plain)
                        }
                    }
                    .padding(DesignConstants.standardPadding)
                    .background(.ultraThinMaterial)
                    .overlay(
                        VStack {
                            Spacer()
                            Divider()
                        }
                    )
                    
                    // Suggestions dropdown floating card
                    if showSuggestions && !filteredSuggestions.isEmpty {
                        VStack(alignment: .leading, spacing: 0) {
                            ForEach(filteredSuggestions) { entity in
                                Button(action: {
                                    selectEntity(name: entity.name)
                                    searchText = ""
                                    showSuggestions = false
                                }) {
                                    HStack {
                                        Text(entity.name.replacingOccurrences(of: "-", with: " ").capitalized)
                                            .font(.subheadline)
                                            .foregroundStyle(DesignConstants.primaryText)
                                        Spacer()
                                        Text(entity.type)
                                            .font(.caption2)
                                            .bold()
                                            .padding(.horizontal, 6)
                                            .padding(.vertical, 2)
                                            .background(DesignConstants.systemOrange.opacity(0.12), in: Capsule())
                                            .foregroundStyle(DesignConstants.systemOrangeText)
                                    }
                                    .padding(.vertical, 8)
                                    .padding(.horizontal, 16)
                                    .contentShape(Rectangle())
                                }
                                .buttonStyle(.plain)
                                Divider()
                            }
                        }
                        .background(DesignConstants.cardBackground.opacity(0.95))
                        .background(.ultraThinMaterial)
                        .clipShape(RoundedRectangle(cornerRadius: 12))
                        .shadow(color: Color.black.opacity(0.12), radius: 10, x: 0, y: 5)
                        .padding(.horizontal, DesignConstants.standardPadding)
                        .padding(.top, 8)
                        .transition(.move(edge: .top).combined(with: .opacity))
                    }
                }
            }
        }
        .onAppear {
            if let first = allEntities.first {
                selectEntity(name: first.name)
            }
        }
        .onChange(of: allEntities.count) { _, _ in
            if focusedEntityName.isEmpty, let first = allEntities.first {
                selectEntity(name: first.name)
            }
        }
    }
    
    private func selectEntity(name: String) {
        focusedEntityName = name
        Task {
            await fetchNeighborhood(for: name)
        }
    }
    
    private func fetchNeighborhood(for name: String) async {
        isFetchingNeighborhood = true
        defer { isFetchingNeighborhood = false }
        
        let encodedName = name.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? name
        guard let url = URL(string: "http://127.0.0.1:8000/graph/\(encodedName)") else { return }
        
        do {
            let (data, response) = try await URLSession.shared.data(for: URLRequest(url: url))
            
            guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
                loadFallbackNeighborhood(for: name)
                return
            }
            
            let decoder = JSONDecoder()
            let responseDecoded = try decoder.decode(NeighborhoodResponse.self, from: data)
            
            // Deduplicate connections by neighbor name to ensure clean radial positioning
            var uniqueConns: [NeighborhoodConnection] = []
            for conn in responseDecoded.connections {
                if !uniqueConns.contains(where: { $0.neighbor.name.lowercased() == conn.neighbor.name.lowercased() }) {
                    uniqueConns.append(conn)
                }
            }
            
            let filteredResponse = NeighborhoodResponse(entity: responseDecoded.entity, connections: uniqueConns)
            
            // Build positions based on unique connections
            var newPositions: [UUID: CGPoint] = [:]
            let count = uniqueConns.count
            let radius: CGFloat = 135
            
            for (index, conn) in uniqueConns.enumerated() {
                let angle = CGFloat(index) * (2.0 * .pi) / CGFloat(max(1, count))
                let x = cos(angle) * radius
                let y = sin(angle) * radius
                newPositions[conn.neighbor.id] = CGPoint(x: x, y: y)
            }
            
            withAnimation(.spring(response: 0.65, dampingFraction: 0.75)) {
                self.neighborhood = filteredResponse
                self.nodePositions = newPositions
            }
        } catch {
            print("Failed to fetch neighborhood: \(error)")
            loadFallbackNeighborhood(for: name)
        }
    }
    
    private func loadFallbackNeighborhood(for name: String) {
        // Find matching SwiftData entity
        let simpleEntity: NeighborhoodEntity
        if let localEntity = allEntities.first(where: { 
            $0.name == name || 
            $0.name.lowercased() == name.lowercased() || 
            $0.name.replacingOccurrences(of: " ", with: "-").lowercased() == name.replacingOccurrences(of: " ", with: "-").lowercased() 
        }) {
            simpleEntity = NeighborhoodEntity(
                id: localEntity.id,
                name: localEntity.name,
                type: localEntity.type,
                summary: localEntity.summary,
                confidence: localEntity.confidence,
                source: localEntity.source,
                sources: [localEntity.source]
            )
        } else {
            simpleEntity = NeighborhoodEntity(
                id: UUID(),
                name: name,
                type: "Entity",
                summary: "Lore graph node for \(name). Select or query to discover more.",
                confidence: 0.5,
                source: "Unknown",
                sources: ["Offline Cache"]
            )
        }
        
        // Find other SwiftData entities to show as mock connections
        let otherEntities = allEntities.filter { $0.name != name }
        var uniqueOthers: [LoreEntity] = []
        for other in otherEntities {
            if !uniqueOthers.contains(where: { $0.name.lowercased() == other.name.lowercased() }) {
                uniqueOthers.append(other)
            }
        }
        
        let connections = uniqueOthers.prefix(5).map { other in
            NeighborhoodConnection(
                relationshipType: "RELATED_TO",
                neighbor: NeighborhoodEntity(
                    id: other.id,
                    name: other.name,
                    type: other.type,
                    summary: other.summary,
                    confidence: other.confidence,
                    source: other.source,
                    sources: [other.source]
                )
            )
        }
        
        let response = NeighborhoodResponse(entity: simpleEntity, connections: Array(connections))
        
        var newPositions: [UUID: CGPoint] = [:]
        let radius: CGFloat = 135
        for (index, conn) in response.connections.enumerated() {
            let angle = CGFloat(index) * (2.0 * .pi) / CGFloat(max(1, response.connections.count))
            let x = cos(angle) * radius
            let y = sin(angle) * radius
            newPositions[conn.neighbor.id] = CGPoint(x: x, y: y)
        }
        
        withAnimation(.spring(response: 0.65, dampingFraction: 0.75)) {
            self.neighborhood = response
            self.nodePositions = newPositions
        }
    }
    
    private func drawNode(gc: GraphicsContext, at pos: CGPoint, name: String, type: String, isFocused: Bool) {
        let radius: CGFloat = isFocused ? 24 : 16
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
            // Pulse outer glow
            gc.fill(
                Path(ellipseIn: rect.insetBy(dx: -8, dy: -8)),
                with: .radialGradient(
                    Gradient(colors: [nodeColor.opacity(0.35), nodeColor.opacity(0.0)]),
                    center: pos,
                    startRadius: radius - 2,
                    endRadius: radius + 12
                )
            )
            
            // Outer ring
            gc.stroke(
                Path(ellipseIn: rect.insetBy(dx: -2, dy: -2)),
                with: .color(nodeColor.opacity(0.4)),
                lineWidth: 1.0
            )
        } else {
            // Light aura for neighbor nodes
            gc.fill(
                Path(ellipseIn: rect.insetBy(dx: -4, dy: -4)),
                with: .radialGradient(
                    Gradient(colors: [nodeColor.opacity(0.12), nodeColor.opacity(0.0)]),
                    center: pos,
                    startRadius: radius - 2,
                    endRadius: radius + 6
                )
            )
        }
        
        // Node circle gradient shading
        let shading = GraphicsContext.Shading.radialGradient(
            Gradient(colors: [nodeColor.opacity(0.35), nodeColor]),
            center: pos,
            startRadius: 0,
            endRadius: radius
        )
        gc.fill(Path(ellipseIn: rect), with: shading)
        
        // Dynamic border stroke
        gc.stroke(
            Path(ellipseIn: rect),
            with: .color(isFocused ? .white : nodeColor.opacity(0.7)),
            lineWidth: isFocused ? 2.0 : 1.0
        )
        
        // Render name tag cleanly below
        let formattedName = name.replacingOccurrences(of: "-", with: " ").capitalized
        let labelText = Text(formattedName)
            .font(.system(size: isFocused ? 9.5 : 8.5, weight: isFocused ? .bold : .medium, design: .default))
            .foregroundStyle(DesignConstants.primaryText)
        
        gc.draw(labelText, at: CGPoint(x: pos.x, y: pos.y + radius + 6), anchor: .top)
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

struct NeighborhoodNodeCard: View {
    let entity: NeighborhoodEntity
    @Binding var isExpanded: Bool
    
    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // Header button to toggle expand state
            Button(action: {
                withAnimation(.spring(response: 0.38, dampingFraction: 0.82)) {
                    isExpanded.toggle()
                }
            }) {
                HStack {
                    Text(entity.name.replacingOccurrences(of: "-", with: " ").capitalized)
                        .font(.headline)
                        .bold()
                        .foregroundStyle(DesignConstants.primaryText)
                        .lineLimit(1)
                    
                    Spacer()
                    
                    Text(entity.type)
                        .font(.caption)
                        .bold()
                        .padding(.horizontal, 8)
                        .padding(.vertical, 2)
                        .background(DesignConstants.systemOrange.opacity(0.12), in: Capsule())
                        .foregroundStyle(DesignConstants.systemOrangeText)
                    
                    Image(systemName: isExpanded ? "chevron.down" : "chevron.up")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .padding(.leading, 4)
                }
                .padding(.horizontal, DesignConstants.standardPadding)
                .padding(.vertical, DesignConstants.compactPadding)
                .contentShape(Rectangle())
            }
            .buttonStyle(.plain)
            
            // Collapsible content section
            if isExpanded {
                ScrollView {
                    VStack(alignment: .leading, spacing: DesignConstants.compactPadding) {
                        Text(entity.summary)
                            .font(.subheadline)
                            .foregroundStyle(DesignConstants.secondaryText)
                        
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
                        
                        Divider()
                            .padding(.vertical, 4)
                        
                        EvidenceHistoryView(
                            entityName: entity.name,
                            currentConfidence: entity.confidence,
                            currentSummary: entity.summary,
                            currentSource: entity.source
                        )
                    }
                    .padding(.horizontal, DesignConstants.standardPadding)
                    .padding(.bottom, DesignConstants.standardPadding)
                }
                .frame(maxHeight: 220)
            } else {
                Text(entity.summary)
                    .font(.caption)
                    .foregroundStyle(DesignConstants.secondaryText)
                    .lineLimit(1)
                    .padding(.horizontal, DesignConstants.standardPadding)
                    .padding(.bottom, DesignConstants.compactPadding)
            }
        }
        .liquidGlass()
    }
}

// Helper modifier to handle z-indexing in layered dropdowns
extension View {
    func zPriority(_ index: Double) -> some View {
        self.zIndex(index)
    }
}
