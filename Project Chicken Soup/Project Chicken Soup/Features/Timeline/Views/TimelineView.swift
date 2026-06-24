//
//  TimelineView.swift
//  Project Chicken Soup
//
//  Created by mck on 6/22/26.
//

import SwiftUI
import SwiftData

struct TemporalTimelineView: View {
    let events: [TemporalEvent]
    @Binding var selectedEvent: TemporalEvent?
    
    @Environment(\.modelContext) private var modelContext
    @ObservedObject var backendService = BackendService.shared
    
    @State private var minConfidence: Double = 0.0
    @State private var selectedTypes: Set<String> = ["crash", "testimony", "anomaly", "theory"]
    @State private var activeBranchId: UUID? = nil
    @State private var showFilters = false
    
    private var filteredEvents: [TemporalEvent] {
        events.filter { event in
            event.confidence >= minConfidence &&
            selectedTypes.contains(event.type) &&
            (activeBranchId == nil || event.branch?.id == activeBranchId)
        }
    }
    
    // Compute date boundary for layout
    private var dateRange: (start: Date, end: Date) {
        let sorted = filteredEvents.sorted(by: { $0.timestamp < $1.timestamp })
        guard let first = sorted.first, let last = sorted.last else {
            let now = Date()
            return (now, now.addingTimeInterval(3600))
        }
        // Add padding of 1 month before and after for visual breathing room
        let padding: TimeInterval = 30 * 24 * 3600
        return (first.timestamp.addingTimeInterval(-padding), last.timestamp.addingTimeInterval(padding))
    }
    
    var body: some View {
        ZStack(alignment: .topLeading) {
            VStack(spacing: 0) {
                if backendService.isFetchingEvents && events.isEmpty {
                    VStack(spacing: 12) {
                        ProgressView()
                            .tint(DesignConstants.systemOrange)
                        Text("Aligning Spacetime Field...")
                            .font(.headline)
                            .foregroundStyle(DesignConstants.primaryText)
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if filteredEvents.isEmpty {
                    VStack(spacing: 12) {
                        Image(systemName: "clock.arrow.circlepath")
                            .font(.system(size: 40))
                            .foregroundStyle(.secondary)
                        Text("No Timeline Events Match Filters")
                            .font(.headline)
                            .foregroundStyle(DesignConstants.primaryText)
                        Text("Adjust your advanced filters or perform a new query.")
                            .font(.caption)
                            .foregroundStyle(DesignConstants.secondaryText)
                        
                        Button("Reset Filters") {
                            withAnimation {
                                minConfidence = 0.0
                                selectedTypes = ["crash", "testimony", "anomaly", "theory"]
                                activeBranchId = nil
                            }
                        }
                        .buttonStyle(.borderedProminent)
                        .tint(DesignConstants.systemOrange)
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else {
                    ScrollView(.horizontal, showsIndicators: false) {
                        // Timeline layout containing the interactive nodes
                        TimelineLayout(startDate: dateRange.start, endDate: dateRange.end) {
                            ForEach(filteredEvents) { event in
                                Button {
                                    withAnimation(DesignConstants.hoverAnimation) {
                                        selectedEvent = event
                                    }
                                } label: {
                                    TimelineNodeView(event: event, isSelected: selectedEvent?.id == event.id)
                                }
                                .buttonStyle(.plain)
                                .eventDate(event.timestamp)
                                .eventBranch(event.branch?.name ?? "Universe Prime")
                            }
                        }
                        .padding(.leading, 240)
                        .padding(.trailing, 120)
                        .frame(height: 260)
                    }
                    .background(
                        CanvasView(events: filteredEvents, startDate: dateRange.start, endDate: dateRange.end)
                            .drawingGroup()
                    )
                    #if !os(macOS)
                    .refreshable {
                        await backendService.fetchTemporalEvents(context: modelContext)
                    }
                    #endif
                }
            }
            
            // Collapsible floating advanced filter controls
            VStack(alignment: .leading, spacing: 8) {
                Button {
                    withAnimation(.spring(duration: 0.3)) {
                        showFilters.toggle()
                    }
                } label: {
                    Label("Timeline Filters", systemImage: "line.3.horizontal.decrease.circle.fill")
                        .font(.subheadline)
                        .bold()
                        .padding(.horizontal, 12)
                        .padding(.vertical, 8)
                        .background(DesignConstants.cardBackground.opacity(0.9), in: Capsule())
                        .foregroundStyle(DesignConstants.systemOrangeText)
                        .shadow(color: DesignConstants.glassShadowColor, radius: 4, x: 0, y: 2)
                }
                .buttonStyle(.plain)
                
                if showFilters {
                    AdvancedTimelineFilterView(
                        minConfidence: $minConfidence,
                        selectedTypes: $selectedTypes,
                        activeBranchId: $activeBranchId
                    )
                    .frame(width: 300)
                    .shadow(color: .black.opacity(0.12), radius: 8, x: 0, y: 4)
                    .transition(.asymmetric(
                        insertion: .opacity.combined(with: .move(edge: .top)),
                        removal: .opacity.combined(with: .move(edge: .top))
                    ))
                }
            }
            .padding(.leading, 20)
            .padding(.top, 20)
            .zIndex(10)
        }
        .background(
            DesignConstants.warmBackground
                .ignoresSafeArea()
        )
    }
}

// Separate view for the Animated Canvas to follow the separate View struct rule
struct CanvasView: View {
    let events: [TemporalEvent]
    let startDate: Date
    let endDate: Date
    
    var body: some View {
        SwiftUI.TimelineView(.animation(minimumInterval: 1/60, paused: false)) { context in
            let time = context.date.timeIntervalSinceReferenceDate
            
            Canvas { gc, size in
                let totalDuration = endDate.timeIntervalSince(startDate)
                guard totalDuration > 0 else { return }
                
                // Get unique branches
                var branches: [String] = []
                for event in events {
                    let b = event.branch?.name ?? "Universe Prime"
                    if !branches.contains(b) {
                        branches.append(b)
                    }
                }
                branches.sort { b1, b2 in
                    if b1 == "Universe Prime" { return true }
                    if b2 == "Universe Prime" { return false }
                    return b1 < b2
                }
                
                let trackCount = max(branches.count, 1)
                let trackHeight = size.height / CGFloat(trackCount)
                
                // Draw Spacetime Grid lines
                var gridPath = Path()
                let gridSpacing: CGFloat = 80
                let offset = CGFloat(time.truncatingRemainder(dividingBy: Double(gridSpacing)))
                for x in stride(from: -offset, to: size.width, by: gridSpacing) {
                    gridPath.move(to: CGPoint(x: x, y: 0))
                    gridPath.addLine(to: CGPoint(x: x, y: size.height))
                }
                for y in stride(from: 0, to: size.height, by: gridSpacing) {
                    gridPath.move(to: CGPoint(x: 0, y: y))
                    gridPath.addLine(to: CGPoint(x: size.width, y: y))
                }
                gc.stroke(gridPath, with: .color(DesignConstants.primaryText.opacity(0.02)), lineWidth: 1)
                
                // Draw parallel track lines
                for (index, branch) in branches.enumerated() {
                    let trackCenterY = CGFloat(index) * trackHeight + (trackHeight / 2)
                    var trackPath = Path()
                    trackPath.move(to: CGPoint(x: 0, y: trackCenterY))
                    
                    // Wave representing spacetime warp/energy on this branch
                    for x in stride(from: 0, to: size.width, by: 10) {
                        let wave = sin(x * 0.005 + CGFloat(time) + CGFloat(index * 2)) * 6
                        trackPath.addLine(to: CGPoint(x: x, y: trackCenterY + wave))
                    }
                    
                    let tintColor = index == 0 ? DesignConstants.systemOrange : DesignConstants.systemBlue
                    gc.stroke(trackPath, with: .color(tintColor.opacity(0.18)), lineWidth: 2)
                    
                    // Draw branch labels on the left side
                    let font = Font.system(size: 9, weight: .bold, design: .monospaced)
                    let text = gc.resolve(Text(branch.uppercased()).font(font).foregroundStyle(tintColor.opacity(0.35)))
                    gc.draw(text, at: CGPoint(x: 10, y: trackCenterY - 14), anchor: .leading)
                }
                
                // Draw branching curves
                for (index, branch) in branches.enumerated() {
                    if index == 0 { continue }
                    
                    let branchEvents = events.filter { ($0.branch?.name ?? "Universe Prime") == branch }
                        .sorted(by: { $0.timestamp < $1.timestamp })
                    guard let firstEvent = branchEvents.first else { continue }
                    
                    let firstEventOffset = firstEvent.timestamp.timeIntervalSince(startDate)
                    let targetX = (CGFloat(firstEventOffset / totalDuration) * size.width)
                    let targetY = CGFloat(index) * trackHeight + (trackHeight / 2)
                    
                    // Find a preceding event in "Universe Prime" to branch from
                    let primeEvents = events.filter { ($0.branch?.name ?? "Universe Prime") == "Universe Prime" }
                        .sorted(by: { $0.timestamp < $1.timestamp })
                    
                    let precedingEvent = primeEvents.last(where: { $0.timestamp <= firstEvent.timestamp }) ?? primeEvents.first
                    
                    if let sourceEvent = precedingEvent {
                        let sourceOffset = sourceEvent.timestamp.timeIntervalSince(startDate)
                        let sourceX = (CGFloat(sourceOffset / totalDuration) * size.width)
                        let sourceY = trackHeight / 2 // "Universe Prime" center Y
                        
                        var splitPath = Path()
                        splitPath.move(to: CGPoint(x: sourceX, y: sourceY))
                        
                        // Draw smooth Bezier curve from source to target
                        let control1 = CGPoint(x: sourceX + (targetX - sourceX) * 0.5, y: sourceY)
                        let control2 = CGPoint(x: sourceX + (targetX - sourceX) * 0.5, y: targetY)
                        splitPath.addCurve(to: CGPoint(x: targetX, y: targetY), control1: control1, control2: control2)
                        
                        let gradient = Gradient(colors: [DesignConstants.systemOrange.opacity(0.5), DesignConstants.systemBlue.opacity(0.5)])
                        gc.stroke(
                            splitPath,
                            with: .linearGradient(
                                gradient,
                                startPoint: CGPoint(x: sourceX, y: sourceY),
                                endPoint: CGPoint(x: targetX, y: targetY)
                            ),
                            style: StrokeStyle(lineWidth: 1.5, dash: [4, 3])
                        )
                    }
                }
                
                // Particle flow streams along the active tracks
                if !events.isEmpty {
                    for i in 0..<8 {
                        let trackIndex = i % trackCount
                        let trackCenterY = CGFloat(trackIndex) * trackHeight + (trackHeight / 2)
                        let speed = Double((i % 3) + 1) * 0.2
                        let pX = CGFloat((time * 80 * speed).truncatingRemainder(dividingBy: Double(size.width)))
                        let wave = sin(pX * 0.005 + CGFloat(time)) * 6
                        
                        gc.fill(
                            Path(ellipseIn: CGRect(x: pX - 2, y: trackCenterY + wave - 2, width: 4, height: 4)),
                            with: .color((trackIndex == 0 ? DesignConstants.systemOrange : DesignConstants.systemBlue).opacity(0.35))
                        )
                    }
                }
            }
        }
        .frame(height: 260)
    }
}

struct TemporalTimelineView_PreviewHelper: View {
    @State var selected: TemporalEvent? = nil
    let container: ModelContainer
    let events: [TemporalEvent]
    
    init() {
        let schema = Schema([
            TemporalEvent.self,
            TimelineBranch.self,
            LoreEntity.self
        ])
        let container = try! ModelContainer(for: schema, configurations: [ModelConfiguration(isStoredInMemoryOnly: true)])
        let context = container.mainContext
        
        let mainBranch = TimelineBranch(name: "Universe Prime", isActive: true)
        context.insert(mainBranch)
        
        let e1 = TemporalEvent(
            title: "Vatican UFO Crash",
            eventDescription: "Crash recovery of a highly advanced disc-shaped object in Magenta, Italy.",
            timestamp: Date().addingTimeInterval(-1000000),
            confidence: 0.94,
            source: "Vatican Secrets",
            type: "crash"
        )
        e1.branch = mainBranch
        
        let e2 = TemporalEvent(
            title: "David Grusch Testimony",
            eventDescription: "Under-oath disclosure of non-human recovery programs to the US Congress.",
            timestamp: Date(),
            confidence: 0.98,
            source: "US Congress",
            type: "testimony"
        )
        e2.branch = mainBranch
        
        context.insert(e1)
        context.insert(e2)
        
        self.container = container
        self.events = [e1, e2]
    }
    
    var body: some View {
        TemporalTimelineView(
            events: events,
            selectedEvent: $selected
        )
        .modelContainer(container)
    }
}

#Preview {
    TemporalTimelineView_PreviewHelper()
}
