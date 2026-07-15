import SwiftUI

struct Neo4jSnapshotSectionView: View {
    let section: APIStatusProgressSection?

    var body: some View {
        Section {
            if let section {
                LabeledContent("Nodes", value: section.nodes ?? "—")
                LabeledContent("Relationships", value: section.relationships ?? "—")

                if let updated = section.lastRun {
                    LabeledContent("Last updated", value: StatusDateFormatter.format(updated))
                        .font(.caption2)
                }
            } else {
                LabeledContent("Status", value: "idle")
                    .foregroundStyle(.secondary)
            }
        } header: {
            HStack {
                Image(systemName: "point.3.connected.trianglepath.dotted")
                    .foregroundStyle(.secondary)
                Text("Knowledge Graph")
            }
        }
    }
}

#Preview {
    List {
        Neo4jSnapshotSectionView(section: APIStatusProgressSection(
            status: "synced", lastRun: ISO8601DateFormatter().string(from: .now),
            nodes: "794", relationships: "6328"
        ))
    }
}
