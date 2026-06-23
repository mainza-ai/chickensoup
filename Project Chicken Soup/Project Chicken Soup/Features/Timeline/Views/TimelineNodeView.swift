//
//  TimelineNodeView.swift
//  Project Chicken Soup
//
//  Created by mck on 6/22/26.
//

import SwiftUI
import SwiftData

struct TimelineNodeView: View {
    let event: TemporalEvent
    var isSelected: Bool = false
    
    @State private var isHovered = false
    
    private var iconName: String {
        switch event.type.lowercased() {
        case "crash": return "exclamationmark.triangle.fill"
        case "testimony": return "person.2.wave.2.fill"
        case "anomaly": return "sparkles"
        case "theory": return "brain"
        default: return "clock.fill"
        }
    }
    
    private var badgeColor: Color {
        switch event.type.lowercased() {
        case "crash": return DesignConstants.systemRed
        case "testimony": return DesignConstants.systemBlue
        case "anomaly": return DesignConstants.systemPurple
        case "theory": return DesignConstants.systemGreenText
        default: return DesignConstants.systemOrangeText
        }
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: DesignConstants.compactPadding) {
            HStack {
                Label(event.type.capitalized, systemImage: iconName)
                    .font(.footnote)
                    .bold()
                    .foregroundStyle(badgeColor)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(badgeColor.opacity(0.12), in: Capsule())
                
                Spacer()
                
                Text(String(format: "%.0f%% Match", event.confidence * 100))
                    .font(.caption)
                    .bold()
                    .foregroundStyle(DesignConstants.systemOrangeText)
            }
            
            Text(event.title)
                .font(.headline)
                .foregroundStyle(DesignConstants.primaryText)
                .lineLimit(1)
            
            Text(event.eventDescription)
                .font(.subheadline)
                .foregroundStyle(DesignConstants.secondaryText)
                .lineLimit(2)
                .multilineTextAlignment(.leading)
            
            Divider()
                .padding(.vertical, 4)
            
            HStack {
                Text(event.timestamp, format: .dateTime.year().month().day())
                    .font(.caption)
                    .foregroundStyle(.secondary)
                
                Spacer()
                
                Text("Src: \(event.source)")
                    .font(.caption)
                    .foregroundStyle(.tertiary)
                    .lineLimit(1)
            }
        }
        .padding(DesignConstants.standardPadding)
        .frame(width: 260)
        .background(
            RoundedRectangle(cornerRadius: DesignConstants.cardCornerRadius)
                .fill(DesignConstants.cardBackground)
        )
        .overlay(
            RoundedRectangle(cornerRadius: DesignConstants.cardCornerRadius)
                .stroke(
                    isSelected || isHovered ? DesignConstants.systemOrange.opacity(0.8) : DesignConstants.dividerColor,
                    lineWidth: isSelected || isHovered ? 2 : 1
                )
        )
        .shadow(
            color: isSelected || isHovered ? DesignConstants.activeShadowColor : DesignConstants.glassShadowColor,
            radius: isSelected || isHovered ? DesignConstants.activeShadowRadius : DesignConstants.glassShadowRadius,
            x: 0,
            y: isSelected || isHovered ? 8 : 4
        )
        .scaleEffect(isHovered ? 1.05 : 1.0)
        .onHover { hovering in
            withAnimation(DesignConstants.hoverAnimation) {
                isHovered = hovering
            }
        }
        .accessibilityElement(children: .combine)
        .accessibilityLabel("\(event.title), \(event.type) event, \(Int(event.confidence * 100)) percent confidence match. Source: \(event.source). Date: \(event.timestamp.formatted(date: .abbreviated, time: .omitted))")
        .accessibilityHint(isSelected ? "Currently selected event." : "Double tap to select this event on the timeline.")
    }
}

struct TimelineNodeView_PreviewHelper: View {
    let container: ModelContainer
    let mockEvent: TemporalEvent
    
    init() {
        let schema = Schema([
            TemporalEvent.self,
            TimelineBranch.self,
            LoreEntity.self
        ])
        let container = try! ModelContainer(for: schema, configurations: [ModelConfiguration(isStoredInMemoryOnly: true)])
        let context = container.mainContext
        
        let mockEvent = TemporalEvent(
            title: "Magenta UFO Crash Recovery",
            eventDescription: "A circular flying craft crash-landed in northern Italy, recovered by Mussolini's secret cabinet.",
            timestamp: Date(),
            confidence: 0.94,
            source: "Vatican Archives",
            type: "crash"
        )
        context.insert(mockEvent)
        
        self.container = container
        self.mockEvent = mockEvent
    }
    
    var body: some View {
        TimelineNodeView(
            event: mockEvent,
            isSelected: false
        )
        .modelContainer(container)
        .padding()
        .background(Color.gray.opacity(0.2))
    }
}

#Preview {
    TimelineNodeView_PreviewHelper()
}
