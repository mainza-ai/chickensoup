import SwiftUI

struct FallbackRetrySectionView: View {
    let section: APIStatusProgressSection?

    var body: some View {
        Section {
            if let section {
                LabeledContent("Status", value: section.status ?? "idle")

                if let queue = section.queueSize, let queueInt = Int(queue), queueInt > 0 {
                    LabeledContent("Queue size", value: queue)
                }

                if let succeeded = section.succeeded {
                    LabeledContent("Succeeded", value: succeeded)
                }

                if let failed = section.failed {
                    LabeledContent("Failed", value: failed)
                }

                if let slug = section.currentSlug, !slug.isEmpty {
                    LabeledContent("Current", value: slug)
                        .font(.caption)
                }

                if let result = section.lastResult {
                    LabeledContent("Last result", value: result)
                }
            } else {
                ContentUnavailableView("No Data", systemImage: "questionmark.circle")
            }
        } header: {
            HStack {
                Image(systemName: "arrow.circlepath")
                    .foregroundStyle(section?.status == "retrying" ? .blue : .secondary)
                Text("Fallback Retry")
            }
        }
    }
}

#Preview {
    List {
        FallbackRetrySectionView(section: APIStatusProgressSection(
            status: "retrying", currentSlug: "clausius-entropy", lastResult: "success",
            queueSize: "3", succeeded: "1", failed: "0"
        ))
    }
}
