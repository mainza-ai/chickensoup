import SwiftUI

struct IdleIngestionSectionView: View {
    let section: APIStatusProgressSection?

    var body: some View {
        Section {
            if let section {
                LabeledContent("Status", value: section.status ?? "idle")
                LabeledContent("Successful pulses", value: section.pulsesSuccess ?? "0")
                LabeledContent("Failed pulses", value: section.pulsesError ?? "0")

                if let result = section.lastResult {
                    LabeledContent("Last result", value: result)
                }

                if let run = section.lastRun {
                    LabeledContent("Last run", value: formatTimestamp(run))
                        .font(.caption2)
                }
            } else {
                ContentUnavailableView("No Data", systemImage: "questionmark.circle")
            }
        } header: {
            HStack {
                Image(systemName: "antenna.radiowaves.left.and.right")
                    .foregroundStyle(section?.status == "pulsing" ? .blue : .secondary)
                Text("Idle Ingestion")
            }
        }
    }

    private func formatTimestamp(_ iso: String) -> String {
        guard let date = ISO8601DateFormatter().date(from: iso) else { return iso }
        return date.formatted(date: .omitted, time: .standard)
    }
}

#Preview {
    List {
        IdleIngestionSectionView(section: APIStatusProgressSection(
            status: "idle", pulsesSuccess: "5", pulsesError: "1",
            lastResult: "success", lastRun: ISO8601DateFormatter().string(from: .now)
        ))
    }
}
