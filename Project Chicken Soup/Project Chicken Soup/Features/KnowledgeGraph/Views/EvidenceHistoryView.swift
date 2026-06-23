//
//  EvidenceHistoryView.swift
//  Project Chicken Soup
//
//  Created by mck on 6/23/26.
//

import SwiftUI

// Structure representing an archived version of evidence/notes for comparison
struct EvidenceVersion: Identifiable, Equatable {
    let id = UUID()
    let timestamp: Date
    let editor: String
    let confidence: Double
    let summary: String
    let source: String
    let changeReason: String
}

struct EvidenceHistoryView: View {
    let entityName: String
    let currentConfidence: Double
    let currentSummary: String
    let currentSource: String
    
    @State private var historicalVersions: [EvidenceVersion] = []
    @State private var selectedOldVersion: EvidenceVersion?
    
    var body: some View {
        VStack(alignment: .leading, spacing: DesignConstants.standardPadding) {
            Text("Evidence & Confidence History")
                .font(.headline)
                .bold()
                .foregroundStyle(DesignConstants.primaryText)
            
            // 1. Confidence Timeline Visualization
            VStack(alignment: .leading, spacing: 8) {
                Text("Confidence Trajectory")
                    .font(.caption)
                    .bold()
                    .foregroundStyle(.secondary)
                
                HStack(alignment: .bottom, spacing: 16) {
                    ForEach(historicalVersions) { version in
                        VStack(spacing: 4) {
                            Text(String(format: "%.0f%%", version.confidence * 100))
                                .font(.system(size: 10, design: .monospaced))
                                .bold()
                                .foregroundStyle(DesignConstants.systemOrangeText)
                            
                            // Visual bar
                            RoundedRectangle(cornerRadius: 3)
                                .fill(DesignConstants.systemOrange.opacity(0.3 + version.confidence * 0.7))
                                .frame(width: 28, height: CGFloat(version.confidence * 60))
                            
                            Text(formatShortDate(version.timestamp))
                                .font(.system(size: 8))
                                .foregroundStyle(.secondary)
                        }
                    }
                    
                    // Current/Latest version column
                    VStack(spacing: 4) {
                        Text(String(format: "%.0f%%", currentConfidence * 100))
                            .font(.system(size: 10, design: .monospaced))
                            .bold()
                            .foregroundStyle(DesignConstants.systemOrangeText)
                        
                        RoundedRectangle(cornerRadius: 3)
                            .fill(DesignConstants.systemOrange)
                            .frame(width: 28, height: CGFloat(currentConfidence * 60))
                        
                        Text("Current")
                            .font(.system(size: 8))
                            .bold()
                            .foregroundStyle(DesignConstants.systemOrangeText)
                    }
                }
                .padding(.vertical, 8)
                .padding(.horizontal, 12)
                .background(Color.black.opacity(0.02), in: RoundedRectangle(cornerRadius: 8))
            }
            
            Divider()
            
            // 2. Comparison Matrix Selector
            VStack(alignment: .leading, spacing: 8) {
                Text("Select Version to Compare")
                    .font(.caption)
                    .bold()
                    .foregroundStyle(.secondary)
                
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 8) {
                        ForEach(historicalVersions) { version in
                            let isSelected = selectedOldVersion?.id == version.id
                            Button {
                                withAnimation {
                                    selectedOldVersion = version
                                }
                            } label: {
                                VStack(alignment: .leading, spacing: 4) {
                                    HStack {
                                        Text(version.editor)
                                            .font(.caption)
                                            .bold()
                                        Spacer()
                                        Text(String(format: "%.0f%%", version.confidence * 100))
                                            .font(.caption2)
                                            .bold()
                                    }
                                    Text(version.changeReason)
                                        .font(.system(size: 9))
                                        .foregroundStyle(.secondary)
                                        .lineLimit(1)
                                }
                                .padding(8)
                                .frame(width: 130, alignment: .leading)
                                .background(
                                    isSelected ? DesignConstants.systemOrange.opacity(0.12) : Color.black.opacity(0.04),
                                    in: RoundedRectangle(cornerRadius: 8)
                                )
                                .overlay(
                                    RoundedRectangle(cornerRadius: 8)
                                        .stroke(isSelected ? DesignConstants.systemOrange : Color.clear, lineWidth: 1)
                                )
                            }
                            .buttonStyle(.plain)
                        }
                    }
                }
            }
            
            // 3. Side-by-side Comparator Cards
            if let old = selectedOldVersion {
                HStack(alignment: .top, spacing: 12) {
                    // Left Card: Old Version
                    VStack(alignment: .leading, spacing: 6) {
                        HStack {
                            Text("Archived Version")
                                .font(.caption)
                                .bold()
                                .foregroundStyle(.secondary)
                            Spacer()
                            Text(String(format: "%.0f%%", old.confidence * 100))
                                .font(.caption)
                                .bold()
                                .foregroundStyle(DesignConstants.systemOrangeText)
                        }
                        
                        Text(old.summary)
                            .font(.caption2)
                            .foregroundStyle(DesignConstants.primaryText)
                            .lineLimit(4)
                        
                        Spacer()
                        
                        Text("Source: \(old.source)")
                            .font(.system(size: 8))
                            .foregroundStyle(.secondary)
                    }
                    .padding(10)
                    .frame(maxWidth: .infinity, minHeight: 110, maxHeight: 130)
                    .background(Color.black.opacity(0.03), in: RoundedRectangle(cornerRadius: 8))
                    
                    // Center indicator
                    Image(systemName: "arrow.right")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .padding(.top, 45)
                    
                    // Right Card: Current Active Version
                    VStack(alignment: .leading, spacing: 6) {
                        HStack {
                            Text("Active Version")
                                .font(.caption)
                                .bold()
                                .foregroundStyle(DesignConstants.systemOrangeText)
                            Spacer()
                            Text(String(format: "%.0f%%", currentConfidence * 100))
                                .font(.caption)
                                .bold()
                                .foregroundStyle(DesignConstants.systemOrangeText)
                        }
                        
                        Text(currentSummary)
                            .font(.caption2)
                            .foregroundStyle(DesignConstants.primaryText)
                            .lineLimit(4)
                        
                        Spacer()
                        
                        Text("Source: \(currentSource)")
                            .font(.system(size: 8))
                            .foregroundStyle(.secondary)
                    }
                    .padding(10)
                    .frame(maxWidth: .infinity, minHeight: 110, maxHeight: 130)
                    .background(DesignConstants.systemOrange.opacity(0.04), in: RoundedRectangle(cornerRadius: 8))
                    .overlay(RoundedRectangle(cornerRadius: 8).stroke(DesignConstants.systemOrange.opacity(0.15), lineWidth: 1))
                }
            } else {
                Text("Select a version above to compare side-by-side.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 24)
                    .background(DesignConstants.controlBackground, in: RoundedRectangle(cornerRadius: 8))
            }
        }
        .padding(DesignConstants.standardPadding)
        .background(DesignConstants.panelBackground)
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .overlay(RoundedRectangle(cornerRadius: 12).stroke(DesignConstants.dividerColor, lineWidth: 1))
        .onAppear {
            generateMockHistory()
        }
    }
    
    private func generateMockHistory() {
        let calendar = Calendar.current
        let now = Date()
        
        historicalVersions = [
            EvidenceVersion(
                timestamp: calendar.date(byAdding: .year, value: -3, to: now) ?? now,
                editor: "Analyst Prime",
                confidence: max(0.1, currentConfidence - 0.45),
                summary: "Initial fragmented signal logs of \(entityName) collected via automated quantum intelligence sweeps.",
                source: "Quantum Signals",
                changeReason: "Initial Signal Ingestion"
            ),
            EvidenceVersion(
                timestamp: calendar.date(byAdding: .year, value: -1, to: now) ?? now,
                editor: "Director Smith",
                confidence: max(0.3, currentConfidence - 0.15),
                summary: "Corroborated intelligence reports for \(entityName) suggesting timeline deviation risks.",
                source: "Intelligence Feed 8",
                changeReason: "Cross-Reference Cleared"
            )
        ]
        
        // Select the first version by default
        selectedOldVersion = historicalVersions.first
    }
    
    private func formatShortDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "MM/yy"
        return formatter.string(from: date)
    }
}

#Preview {
    EvidenceHistoryView(
        entityName: "Bob Lazar",
        currentConfidence: 0.92,
        currentSummary: "S-4 back-engineering engineer who exposed Area 51 flying disk propulsion systems.",
        currentSource: "Bob Lazar Testimony"
    )
    .padding()
}
