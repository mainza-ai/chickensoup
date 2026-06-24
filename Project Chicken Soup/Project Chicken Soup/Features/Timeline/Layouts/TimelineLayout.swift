//
//  TimelineLayout.swift
//  Project Chicken Soup
//
//  Created by mck on 6/22/26.
//

import SwiftUI

struct EventDateKey: LayoutValueKey {
    nonisolated static let defaultValue: Date = Date()
}

struct EventBranchKey: LayoutValueKey {
    nonisolated static let defaultValue: String = "Universe Prime"
}

extension View {
    func eventDate(_ date: Date) -> some View {
        layoutValue(key: EventDateKey.self, value: date)
    }
    
    func eventBranch(_ branchName: String) -> some View {
        layoutValue(key: EventBranchKey.self, value: branchName)
    }
}

struct TimelineLayout: Layout {
    var startDate: Date
    var endDate: Date
    var minWidth: CGFloat = 1600
    
    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let totalDuration = endDate.timeIntervalSince(startDate)
        let width = max(CGFloat(totalDuration) * 0.00001, minWidth)
        return CGSize(width: width, height: proposal.height ?? 300)
    }
    
    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        let totalDuration = endDate.timeIntervalSince(startDate)
        guard totalDuration > 0 else { return }
        
        // Find unique branches present
        var branches: [String] = []
        for subview in subviews {
            let branch = subview[EventBranchKey.self]
            if !branches.contains(branch) {
                branches.append(branch)
            }
        }
        
        // Sort with Universe Prime at the top
        branches.sort { b1, b2 in
            if b1 == "Universe Prime" { return true }
            if b2 == "Universe Prime" { return false }
            return b1 < b2
        }
        
        let trackCount = max(branches.count, 1)
        let trackHeight = bounds.height / CGFloat(trackCount)
        
        for subview in subviews {
            let date = subview[EventDateKey.self]
            let branch = subview[EventBranchKey.self]
            
            let offset = date.timeIntervalSince(startDate)
            let ratio = CGFloat(offset / totalDuration)
            let x = bounds.minX + (ratio * bounds.width)
            
            let size = subview.sizeThatFits(.unspecified)
            
            let branchIndex = branches.firstIndex(of: branch) ?? 0
            let y = bounds.minY + (CGFloat(branchIndex) * trackHeight) + (trackHeight - size.height) / 2
            
            subview.place(at: CGPoint(x: x - size.width / 2, y: y), proposal: ProposedViewSize(size))
        }
    }
}
