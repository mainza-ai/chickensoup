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
    @StateObject private var backendService = BackendService.shared
    
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
                            }
                        }
                        .padding(.leading, 240)
                        .padding(.trailing, 120)
                        .frame(height: 220)
                    }
                    .background(
                        CanvasView(eventsCount: filteredEvents.count)
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
    let eventsCount: Int
    
    var body: some View {
        SwiftUI.TimelineView(.animation(minimumInterval: 1/60, paused: false)) { context in
            let time = context.date.timeIntervalSinceReferenceDate
            
            Canvas { gc, size in
                let midY = size.height / 2
                
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
                gc.stroke(gridPath, with: .color(DesignConstants.primaryText.opacity(0.04)), lineWidth: 1)
                
                // Draw core Timeline Field line
                var timelinePath = Path()
                timelinePath.move(to: CGPoint(x: 0, y: midY))
                
                // Draw wave representing timeline energy state
                for x in stride(from: 0, to: size.width, by: 10) {
                    let wave = sin(x * 0.005 + CGFloat(time)) * 8
                    timelinePath.addLine(to: CGPoint(x: x, y: midY + wave))
                }
                
                let gradient = Gradient(colors: [DesignConstants.systemOrange.opacity(0.15), DesignConstants.systemOrange.opacity(0.5), DesignConstants.systemPurple.opacity(0.4), DesignConstants.systemOrange.opacity(0.15)])
                gc.stroke(timelinePath, with: .linearGradient(gradient, startPoint: CGPoint(x: 0, y: midY), endPoint: CGPoint(x: size.width, y: midY)), lineWidth: 3)
                
                // Draw quantum particle streams flowing along the timeline
                if eventsCount > 0 {
                    for i in 0..<12 {
                        let speed = Double(i + 1) * 0.15
                        let particleX = CGFloat((time * 100 * speed).truncatingRemainder(dividingBy: Double(size.width)))
                        let wave = sin(particleX * 0.005 + CGFloat(time * 2)) * 8
                        let particleY = midY + wave
                        
                        gc.fill(
                            Path(ellipseIn: CGRect(x: particleX - 3, y: particleY - 3, width: 6, height: 6)),
                            with: .color(i % 2 == 0 ? DesignConstants.systemOrange : DesignConstants.systemBlue)
                        )
                    }
                }
            }
        }
        .frame(height: 220)
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
