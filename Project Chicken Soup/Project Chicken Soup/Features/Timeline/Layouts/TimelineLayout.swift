//
//  TimelineLayout.swift
//  Project Chicken Soup
//
//  Created by mck on 6/22/26.
//

import SwiftUI

struct EventDateKey: LayoutValueKey {
    static let defaultValue: Date = Date()
}

extension View {
    func eventDate(_ date: Date) -> some View {
        layoutValue(key: EventDateKey.self, value: date)
    }
}

struct TimelineLayout: Layout {
    var startDate: Date
    var endDate: Date
    var minWidth: CGFloat = 1600
    
    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let totalDuration = endDate.timeIntervalSince(startDate)
        // Scale: map the total duration to width. Let's make it at least minWidth.
        let width = max(CGFloat(totalDuration) * 0.00001, minWidth)
        return CGSize(width: width, height: proposal.height ?? 400)
    }
    
    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        let totalDuration = endDate.timeIntervalSince(startDate)
        guard totalDuration > 0 else { return }
        
        for subview in subviews {
            let date = subview[EventDateKey.self]
            let offset = date.timeIntervalSince(startDate)
            let ratio = CGFloat(offset / totalDuration)
            let x = bounds.minX + (ratio * bounds.width)
            
            let size = subview.sizeThatFits(.unspecified)
            // Center the subview vertically in the layout bounds
            let y = bounds.minY + (bounds.height - size.height) / 2
            
            subview.place(at: CGPoint(x: x - size.width / 2, y: y), proposal: ProposedViewSize(size))
        }
    }
}
