import SwiftUI

struct PulsesHistorySection: View {
    let history: [APIPulseHistoryEntry]
    let onPulseSelected: (APIPulseHistoryEntry) -> Void
    let onPulseRerun: (String) -> Void
    
    @State private var showAllSnapshots = false
    @State private var selectedFilter: IngestionFilter = .all
    @State private var isPurging = false
    
    @Environment(AlmanacService.self) private var almanacService

    enum IngestionFilter: String, CaseIterable, Identifiable {
        case all = "[ All ]"
        case sourced = "[ Sourced ]"
        case empty = "[ Empty ]"
        
        var id: String { rawValue }
    }

    var filteredPulses: [APIPulseHistoryEntry] {
        switch selectedFilter {
        case .all:
            return history
        case .sourced:
            return history.filter { $0.evidenceCount > 0 }
        case .empty:
            return history.filter { $0.evidenceCount == 0 }
        }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("SNAPSHOT FEED")
                    .font(.caption)
                    .bold()
                    .foregroundStyle(DesignConstants.systemOrangeText)
                
                Spacer()
                
                if isPurging {
                    ProgressView().scaleEffect(0.6)
                } else if history.contains(where: { $0.evidenceCount == 0 }) {
                    Button(action: purgeEmpty) {
                        Label("Purge Empty Logs", systemImage: "trash")
                            .font(.caption2)
                            .bold()
                            .foregroundStyle(.red)
                    }
                    .buttonStyle(.plain)
                    .accessibilityLabel("Purge all empty pulse snapshots")
                }
            }
            
            Picker("Status Filter", selection: $selectedFilter) {
                ForEach(IngestionFilter.allCases) { filter in
                    Text(filter.rawValue).tag(filter)
                }
            }
            .pickerStyle(.segmented)
            .padding(.bottom, 4)
            
            VStack(spacing: 10) {
                let displayed = filteredPulses
                if displayed.isEmpty {
                    Text("No snapshots match this filter.")
                        .font(.caption2)
                        .foregroundStyle(DesignConstants.secondaryText)
                        .padding(.vertical, 20)
                } else {
                    ForEach(displayed.prefix(5), id: \.file) { entry in
                        pulseRow(for: entry)
                    }
                    
                    if displayed.count > 5 {
                        Button(action: {
                            showAllSnapshots = true
                        }) {
                            Text("Show All Ingest Snapshots (\(displayed.count))")
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
        .sheet(isPresented: $showAllSnapshots) {
            NavigationStack {
                List {
                    ForEach(filteredPulses, id: \.file) { entry in
                        pulseRow(for: entry)
                    }
                }
                .navigationTitle("Ingestion Snapshots History")
                .toolbar {
                    ToolbarItem(placement: .cancellationAction) {
                        Button("Close") {
                            showAllSnapshots = false
                        }
                    }
                }
            }
            #if os(macOS)
            .frame(minWidth: 550, minHeight: 500)
            #endif
        }
    }

    @ViewBuilder
    private func pulseRow(for entry: APIPulseHistoryEntry) -> some View {
        HStack(spacing: 12) {
            Button(action: {
                onPulseSelected(entry)
                showAllSnapshots = false
            }) {
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text(entry.entityName)
                            .font(.subheadline)
                            .bold()
                            .foregroundStyle(DesignConstants.primaryText)
                        Text("Pulsed: \(entry.date)")
                            .font(.caption2)
                            .foregroundStyle(DesignConstants.secondaryText)
                    }
                    
                    Spacer()
                    
                    Text("\(entry.evidenceCount) claims")
                        .font(.system(.caption2, design: .monospaced))
                        .bold()
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(DesignConstants.systemOrange.opacity(0.15))
                        .foregroundStyle(DesignConstants.systemOrangeText)
                        .clipShape(Capsule())
                }
            }
            .buttonStyle(.plain)
            .accessibilityLabel("Open pulse details for \(entry.entityName)")
            
            Button(action: {
                onPulseRerun(entry.entityName)
                showAllSnapshots = false
            }) {
                Image(systemName: "arrow.clockwise.circle.fill")
                    .font(.title3)
                    .foregroundStyle(DesignConstants.systemOrange)
            }
            .buttonStyle(.plain)
            .accessibilityLabel("Re-run ingestion pulse for \(entry.entityName)")
        }
        .padding(10)
        .background(DesignConstants.controlBackground, in: RoundedRectangle(cornerRadius: 8))
        .overlay(RoundedRectangle(cornerRadius: 8).stroke(DesignConstants.dividerColor, lineWidth: 1))
    }
    
    private func purgeEmpty() {
        isPurging = true
        Task {
            let success = await almanacService.purgeEmptyPulses()
            if success {
                await almanacService.fetchPulseHistory()
            }
            isPurging = false
        }
    }
}
