import SwiftUI

struct BriefsHistorySection: View {
    let history: [APIAlmanacHistoryEntry]
    let onBriefSelected: (String) -> Void
    @State private var showAllBriefs = false

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("DAILY ALMANAC BRIEFS")
                .font(.caption)
                .bold()
                .foregroundStyle(DesignConstants.systemOrangeText)
            
            VStack(spacing: 10) {
                if history.isEmpty {
                    Text("No daily briefs compiled yet.")
                        .font(.caption2)
                        .foregroundStyle(DesignConstants.secondaryText)
                        .padding(.vertical, 20)
                } else {
                    // Show only first 5 on dashboard
                    ForEach(history.prefix(5), id: \.filename) { brief in
                        briefRow(for: brief)
                    }
                    
                    if history.count > 5 {
                        Button(action: {
                            showAllBriefs = true
                        }) {
                            Text("Show All Historical Briefs (\(history.count))")
                                .font(.caption)
                                .bold()
                                .foregroundStyle(DesignConstants.systemOrangeText)
                                .frame(maxWidth: .infinity, alignment: .center)
                                .padding(.top, 8)
                        }
                        .buttonStyle(.plain)
                    }
                }
            }
            .padding()
            .background(DesignConstants.cardBackground)
            .clipShape(RoundedRectangle(cornerRadius: DesignConstants.cardCornerRadius))
            .overlay(RoundedRectangle(cornerRadius: DesignConstants.cardCornerRadius).stroke(DesignConstants.glassBorderColor, lineWidth: 1))
        }
        .sheet(isPresented: $showAllBriefs) {
            NavigationStack {
                List {
                    ForEach(history, id: \.filename) { brief in
                        briefRow(for: brief)
                    }
                }
                .navigationTitle("Almanac Briefs History")
                .toolbar {
                    ToolbarItem(placement: .cancellationAction) {
                        Button("Close") {
                            showAllBriefs = false
                        }
                    }
                }
            }
            #if os(macOS)
            .frame(minWidth: 400, minHeight: 500)
            #endif
        }
    }

    @ViewBuilder
    private func briefRow(for brief: APIAlmanacHistoryEntry) -> some View {
        Button(action: {
            onBriefSelected(brief.date)
            showAllBriefs = false
        }) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(brief.date)
                        .font(.subheadline)
                        .bold()
                        .foregroundStyle(DesignConstants.primaryText)
                    
                    Text("\(brief.sizeKb) KB • Compiled on server")
                        .font(.caption2)
                        .foregroundStyle(DesignConstants.secondaryText)
                }
                Spacer()
                Image(systemName: "chevron.right")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            .padding(10)
            .background(DesignConstants.controlBackground, in: RoundedRectangle(cornerRadius: 8))
            .overlay(RoundedRectangle(cornerRadius: 8).stroke(DesignConstants.dividerColor, lineWidth: 1))
        }
        .buttonStyle(.plain)
        .accessibilityLabel("Open daily brief for \(brief.date)")
    }
}
