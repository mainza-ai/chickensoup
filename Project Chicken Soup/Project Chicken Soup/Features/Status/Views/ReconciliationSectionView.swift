import SwiftUI

struct ReconciliationSectionView: View {
    let section: APIStatusProgressSection?

    var statusIcon: String {
        switch section?.status {
        case "running": "arrow.triangle.2.circlepath"
        case "complete": "checkmark.circle.fill"
        case "stopped": "stop.circle"
        case "error": "exclamationmark.circle.fill"
        default: "circle.dashed"
        }
    }

    var statusColor: Color {
        switch section?.status {
        case "running": .blue
        case "complete": .green
        case "stopped": .orange
        case "error": .red
        default: .secondary
        }
    }

    var body: some View {
        Section {
            if let section {
                LabeledContent("Status", value: section.status ?? "idle")
                    .foregroundStyle(statusColor)

                if let current = section.current, let total = section.total {
                    ProgressView(
                        "\(current) / \(total) pages",
                        value: Double(current) ?? 0,
                        total: Double(total) ?? 100
                    )
                    .tint(statusColor)
                }

                if let slug = section.currentSlug, !slug.isEmpty {
                    LabeledContent("Current", value: slug)
                        .font(.caption)
                }

                if let processed = section.pagesProcessed {
                    LabeledContent("Processed", value: processed)
                }

                if let errors = section.errors, errors != "0" {
                    LabeledContent("Errors", value: errors)
                        .foregroundStyle(.red)
                }

                if let elapsed = section.startedAt {
                    LabeledContent("Started", value: StatusDateFormatter.format(elapsed))
                        .font(.caption2)
                }

                if let completed = section.completedAt {
                    LabeledContent("Completed", value: StatusDateFormatter.format(completed))
                        .font(.caption2)
                }
            } else {
                LabeledContent("Status", value: "idle")
                    .foregroundStyle(.secondary)
            }
        } header: {
            HStack {
                Image(systemName: statusIcon)
                    .foregroundStyle(statusColor)
                Text("Reconciliation")
            }
        }
    }
}

#Preview {
    List {
        ReconciliationSectionView(section: APIStatusProgressSection(
            status: "running", current: "45", total: "495",
            currentSlug: "bob-lazar", pagesProcessed: "45", errors: "0",
            startedAt: ISO8601DateFormatter().string(from: .now)
        ))
    }
}
