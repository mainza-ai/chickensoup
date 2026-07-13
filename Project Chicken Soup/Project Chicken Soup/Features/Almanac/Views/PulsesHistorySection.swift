import SwiftUI

struct PulsesHistorySection: View {
    let history: [APIPulseHistoryEntry]
    let onPulseSelected: (APIPulseHistoryEntry) -> Void
    let onPulseRerun: (String) -> Void

    @State private var showAllSnapshots = false
    @State private var selectedFilter: IngestionFilter = .all
    @State private var isPurging = false
    @State private var expandedGroups: Set<String> = []

    @Environment(AlmanacService.self) private var almanacService

    enum IngestionFilter: String, CaseIterable, Identifiable {
        case all = "[ All ]"
        case sourced = "[ Sourced ]"
        case empty = "[ Empty ]"

        var id: String { rawValue }
    }

    struct PulseGroup: Identifiable {
        let entityName: String
        var entries: [APIPulseHistoryEntry]
        var id: String { entityName }
    }

    var groupedPulses: [PulseGroup] {
        let filtered = filteredPulses
        var groups: [String: [APIPulseHistoryEntry]] = [:]
        for entry in filtered {
            groups[entry.entityName, default: []].append(entry)
        }
        return groups.map { key, entries in
            PulseGroup(entityName: key, entries: entries)
        }.sorted { a, b in
            let aLatest = a.entries.first?.timestamp ?? ""
            let bLatest = b.entries.first?.timestamp ?? ""
            return aLatest > bLatest
        }
    }

    var displayedGroups: [PulseGroup] {
        Array(groupedPulses.prefix(5))
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
                if displayedGroups.isEmpty {
                    Text("No snapshots match this filter.")
                        .font(.caption2)
                        .foregroundStyle(DesignConstants.secondaryText)
                        .padding(.vertical, 20)
                } else {
                    ForEach(displayedGroups) { group in
                        groupRow(for: group)
                    }

                    if groupedPulses.count > 5 {
                        Button(action: {
                            showAllSnapshots = true
                        }) {
                            Text("Show All Ingest Snapshots (\(groupedPulses.count))")
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
                    ForEach(groupedPulses) { group in
                        groupRow(for: group, isExpanded: .constant(true))
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
    private func groupRow(for group: PulseGroup, isExpandedBinding: Binding<Bool>? = nil) -> some View {
        let latest = group.entries.first!
        let binding: Binding<Bool> = isExpandedBinding ?? Binding(
            get: { expandedGroups.contains(group.entityName) },
            set: { isOn in
                if isOn {
                    expandedGroups.insert(group.entityName)
                } else {
                    expandedGroups.remove(group.entityName)
                }
            }
        )

        VStack(alignment: .leading, spacing: 0) {
            HStack(spacing: 12) {
                Button(action: {
                    onPulseSelected(latest)
                    showAllSnapshots = false
                }) {
                    HStack {
                        VStack(alignment: .leading, spacing: 4) {
                            Text(latest.entityName)
                                .font(.subheadline)
                                .bold()
                                .foregroundStyle(DesignConstants.primaryText)
                            Text("Pulsed: \(latest.date)")
                                .font(.caption2)
                                .foregroundStyle(DesignConstants.secondaryText)
                        }

                        Spacer()

                        Text("\(latest.evidenceCount) claims")
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
                .accessibilityLabel("Open pulse details for \(latest.entityName)")

                if group.entries.count > 1 {
                    Button(action: {
                        binding.wrappedValue.toggle()
                    }) {
                        Image(systemName: binding.wrappedValue ? "chevron.up" : "chevron.down")
                            .font(.caption.bold())
                            .foregroundStyle(DesignConstants.secondaryText)
                    }
                    .buttonStyle(.plain)
                    .accessibilityLabel(binding.wrappedValue ? "Collapse history for \(group.entityName)" : "Expand history for \(group.entityName)")
                }

                Button(action: {
                    onPulseRerun(latest.entityName)
                    showAllSnapshots = false
                }) {
                    Image(systemName: "arrow.clockwise.circle.fill")
                        .font(.title3)
                        .foregroundStyle(DesignConstants.systemOrange)
                }
                .buttonStyle(.plain)
                .accessibilityLabel("Re-run ingestion pulse for \(group.entityName)")
            }
            .padding(10)
            .background(DesignConstants.controlBackground, in: RoundedRectangle(cornerRadius: 8))
            .overlay(RoundedRectangle(cornerRadius: 8).stroke(DesignConstants.dividerColor, lineWidth: 1))

            if binding.wrappedValue, group.entries.count > 1 {
                VStack(alignment: .leading, spacing: 0) {
                    ForEach(group.entries.dropFirst()) { prior in
                        HStack(spacing: 12) {
                            Button(action: {
                                onPulseSelected(prior)
                                showAllSnapshots = false
                            }) {
                                HStack {
                                    VStack(alignment: .leading, spacing: 2) {
                                        Text(prior.entityName)
                                            .font(.caption)
                                            .foregroundStyle(DesignConstants.secondaryText)
                                        Text("Pulsed: \(prior.date)")
                                            .font(.caption2)
                                            .foregroundStyle(DesignConstants.secondaryText.opacity(0.7))
                                    }
                                    Spacer()
                                    Text("\(prior.evidenceCount) claims")
                                        .font(.system(.caption2, design: .monospaced))
                                        .foregroundStyle(DesignConstants.secondaryText)
                                }
                            }
                            .buttonStyle(.plain)

                            Spacer()
                        }
                        .padding(.horizontal, 10)
                        .padding(.vertical, 6)
                        .background(DesignConstants.controlBackground.opacity(0.5))
                    }
                }
                .background(DesignConstants.controlBackground.opacity(0.3))
                .clipShape(RoundedRectangle(cornerRadius: 8))
                .padding(.bottom, 4)
            }
        }
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
