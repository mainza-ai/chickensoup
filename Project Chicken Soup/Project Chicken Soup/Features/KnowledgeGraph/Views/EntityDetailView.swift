import SwiftUI

struct EntityDetailView: View {
    let entityName: String
    let entity: NeighborhoodEntity?
    @Environment(AlmanacService.self) private var almanacService
    @State private var isPulsing = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: DesignConstants.standardPadding) {
                if let entity = entity {
                    HStack {
                        Image(systemName: entityTypeIcon(entity.type))
                            .font(.title3)
                            .foregroundStyle(entityColor(entity.type))
                        Text(entity.name)
                            .font(.title2)
                            .bold()
                            .foregroundStyle(DesignConstants.primaryText)
                    }

                    Label(entity.summary, systemImage: "info.circle")
                        .font(.body)
                        .foregroundStyle(DesignConstants.primaryText)
                        .frame(maxWidth: .infinity, alignment: .leading)

                    Divider()

                    VStack(alignment: .leading, spacing: DesignConstants.compactPadding) {
                        confidenceRow(entity.confidence)

                        HStack {
                            Label("Type", systemImage: "tag")
                                .font(.subheadline)
                                .foregroundStyle(.secondary)
                            Spacer()
                            Text(entity.type)
                                .font(.subheadline)
                                .foregroundStyle(DesignConstants.primaryText)
                        }

                        HStack {
                            Label("Source", systemImage: "bookmark")
                                .font(.subheadline)
                                .foregroundStyle(.secondary)
                            Spacer()
                            Text(entity.source)
                                .font(.subheadline)
                                .foregroundStyle(DesignConstants.primaryText)
                        }

                        if !entity.sources.isEmpty {
                            HStack(alignment: .top) {
                                Label("All Sources", systemImage: "books.vertical")
                                    .font(.subheadline)
                                    .foregroundStyle(.secondary)
                                Spacer()
                                VStack(alignment: .trailing, spacing: 4) {
                                    ForEach(entity.sources, id: \.self) { source in
                                        Text(source)
                                            .font(.caption)
                                            .foregroundStyle(DesignConstants.secondaryText)
                                    }
                                }
                            }
                        }
                    }
                    .padding()
                    .background(DesignConstants.controlBackground, in: RoundedRectangle(cornerRadius: DesignConstants.cardCornerRadius))
                } else {
                    VStack(spacing: 12) {
                        Image(systemName: "circle.grid.hex")
                            .font(.system(size: 40))
                            .foregroundStyle(.secondary)
                        Text("Loading entity data...")
                            .font(.headline)
                            .foregroundStyle(DesignConstants.secondaryText)
                        ProgressView()
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 60)
                }
            }
            .padding(DesignConstants.standardPadding)
        }
        .background(DesignConstants.warmBackground)
        .navigationTitle(entityName)
        .toolbar {
            if let entity = entity {
                ToolbarItem(placement: .primaryAction) {
                    if isPulsing {
                        ProgressView("Researching...")
                            .font(.caption)
                            .foregroundStyle(DesignConstants.systemOrange)
                    } else {
                        Button {
                            Task { await pulseCurrentEntity(entity.name) }
                        } label: {
                            Label("Research Now", systemImage: "bolt.fill")
                                .font(.caption)
                                .foregroundStyle(DesignConstants.systemOrange)
                        }
                        .disabled(entity.name.isEmpty)
                    }
                }
            }
        }
        #if os(iOS)
        .navigationBarTitleDisplayMode(.inline)
        #endif
    }

    private func pulseCurrentEntity(_ name: String) async {
        isPulsing = true
        defer { isPulsing = false }
        let result = await almanacService.triggerPulseAsync(entityName: name)
        guard let taskId = result?.taskId else { return }
        _ = await pollPulseStatus(taskId: taskId)
    }

    private func pollPulseStatus(taskId: String) async -> Bool {
        var done = false
        while !done {
            try? await Task.sleep(nanoseconds: 2_000_000_000)
            let status = await almanacService.fetchTaskStatus(taskId: taskId)
            if let s = status {
                if s.status == "completed" || s.status == "failed" || s.status == "success" {
                    done = true
                }
            } else {
                done = true
            }
        }
        return true
    }

    private func confidenceRow(_ confidence: Double) -> some View {
        HStack {
            Label("Confidence", systemImage: "percent")
                .font(.subheadline)
                .foregroundStyle(.secondary)
            Spacer()
            Text(String(format: "%.0f%% Match", confidence * 100))
                .font(.subheadline)
                .bold()
                .foregroundStyle(confidence > 0.9 ? DesignConstants.systemGreenText : DesignConstants.systemOrangeText)
        }
    }

    private func entityTypeIcon(_ type: String) -> String {
        switch type.lowercased() {
        case "person": return "person.fill"
        case "place": return "mappin.and.ellipse"
        case "concept": return "lightbulb.fill"
        case "project": return "gearshape.2.fill"
        case "object": return "cube.fill"
        case "event": return "sparkles"
        default: return "doc.text.fill"
        }
    }

    private func entityColor(_ type: String) -> Color {
        switch type.lowercased() {
        case "person": return DesignConstants.systemOrange
        case "place": return DesignConstants.systemGreen
        case "concept": return DesignConstants.systemPurple
        case "project": return .pink
        case "object": return DesignConstants.systemBlue
        case "event": return DesignConstants.systemRed
        default: return DesignConstants.secondaryText
        }
    }
}
