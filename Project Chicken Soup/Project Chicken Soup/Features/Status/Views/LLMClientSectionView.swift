import SwiftUI

struct LLMClientSectionView: View {
    let section: APIStatusProgressSection?

    var isBreakerOpen: Bool {
        section?.breakerOpen == "true"
    }

    var statusColor: Color {
        isBreakerOpen ? .red : .green
    }

    var failedColor: Color {
        section?.failedCalls == "0" ? .secondary : .red
    }

    var successRate: Double? {
        guard let total = section?.totalCalls.flatMap(Double.init),
              let success = section?.successCalls.flatMap(Double.init),
              total > 0 else { return nil }
        return success / total * 100
    }

    var successRateColor: Color {
        guard let rate = successRate else { return .secondary }
        return rate > 95 ? .green : .orange
    }

    var body: some View {
        Section {
            if let section {
                LabeledContent("Status", value: isBreakerOpen ? "Breaker Open" : "Online")
                    .foregroundStyle(statusColor)

                LabeledContent("Total calls", value: section.totalCalls ?? "0")

                if let failed = section.failedCalls {
                    LabeledContent("Failed", value: failed)
                        .foregroundStyle(failedColor)
                }

                if let rate = successRate {
                    LabeledContent("Success rate", value: "\(Int(rate))%")
                        .foregroundStyle(successRateColor)
                }
            } else {
                LabeledContent("Status", value: "idle")
                    .foregroundStyle(.secondary)
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
