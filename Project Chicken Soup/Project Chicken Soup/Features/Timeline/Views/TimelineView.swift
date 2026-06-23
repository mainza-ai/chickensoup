//
//  TimelineView.swift
//  Project Chicken Soup
//
//  Created by mck on 6/22/26.
//

import SwiftUI
import SwiftData

struct TimelineView: View {
    let events: [TemporalEvent]
    @Binding var selectedEvent: TemporalEvent?
    
    // Compute date boundary for layout
    private var dateRange: (start: Date, end: Date) {
        let sorted = events.sorted(by: { $0.timestamp < $1.timestamp })
        guard let first = sorted.first, let last = sorted.last else {
            let now = Date()
            return (now, now.addingTimeInterval(3600))
        }
        // Add padding of 1 month before and after for visual breathing room
        let padding: TimeInterval = 30 * 24 * 3600
        return (first.timestamp.addingTimeInterval(-padding), last.timestamp.addingTimeInterval(padding))
    }
    
    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            ZStack(alignment: .leading) {
                // Background Quantum Entanglement Field Canvas
                CanvasView(eventsCount: events.count)
                
                // Timeline layout containing the interactive nodes
                TimelineLayout(startDate: dateRange.start, endDate: dateRange.end) {
                    ForEach(events) { event in
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
                .padding(.horizontal, 100)
            }
            .frame(minHeight: 450)
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
        .frame(minHeight: 450)
    }
}

#Preview {
    @Previewable @State var selected: TemporalEvent? = nil
    TimelineView(
        events: [
            TemporalEvent(
                title: "Vatican UFO Crash",
                eventDescription: "Crash recovery of a highly advanced disc-shaped object in Magenta, Italy.",
                timestamp: Date().addingTimeInterval(-1000000),
                confidence: 0.94,
                source: "Vatican Secrets",
                type: "crash"
            ),
            TemporalEvent(
                title: "David Grusch Testimony",
                eventDescription: "Under-oath disclosure of non-human recovery programs to the US Congress.",
                timestamp: Date(),
                confidence: 0.98,
                source: "US Congress",
                type: "testimony"
            )
        ],
        selectedEvent: $selected
    )
}
