import SwiftUI

struct LLMClientSectionView: View {
    let section: APIStatusProgressSection?

    var isBreakerOpen: Bool {
        section?.breakerOpen == "true"
    }

    var successRate: Double? {
        guard let total = section?.totalCalls.flatMap(Double.init),
              let success = section?.successCalls.flatMap(Double.init),
              total > 0 else { return nil }
        return success / total * 100
    }

    var body: some View {
        Section {
            if let section {
                LabeledContent("Status", value: isBreakerOpen ? "Breaker Open" : "Online")
                    .foregroundColor(isBreakerOpen ? .red : .green)

                LabeledContent("Total calls", value: section.totalCalls ?? "0")

                if let failed = section.failedCalls {
                    LabeledContent("Failed", value: failed)
                        .foregroundColor(failed == "0" ? .secondary : .red)
                }

                if let rate = successRate {
                    LabeledContent("Success rate", value: "\(Int(rate))%")
                        .foregroundStyle(rate > 95 ? .green : .orange)
                }
            } else {
                ContentUnavailableView("No Data", systemImage: "questionmark.circle")
            }
        } header: {
            HStack {
                Circle()
                    .fill(isBreakerOpen ? Color.red : Color.green)
                    .frame(width: 8, height: 8)
                Text("LLM Engine")
            }
        }
    }
}

#Preview {
    List {
        LLMClientSectionView(section: APIStatusProgressSection(
            status: "online", totalCalls: "412",
            successCalls: "398", failedCalls: "14",
            breakerOpen: "false"
        ))
    }
}
