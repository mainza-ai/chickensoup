import SwiftUI

struct ServerClockView: View {
    @State private var serverTime: Date?
    @State private var lastPoll: Date = .now
    @State private var pollingTask: Task<Void, Never>?

    private var formattedTime: String {
        let date = serverTime ?? .now
        return date.formatted(date: .abbreviated, time: .standard)
    }

    private var timezoneAbbreviation: String {
        TimeZone.current.abbreviation() ?? ""
    }

    private var connectionColor: Color {
        let elapsed = Date.now.timeIntervalSince(lastPoll)
        if elapsed < 3 { return .green }
        if elapsed < 6 { return .yellow }
        return .red
    }

    private var connectionLabel: String {
        let elapsed = Date.now.timeIntervalSince(lastPoll)
        if elapsed < 3 { return "Connected" }
        if elapsed < 6 { return "Slow" }
        return "Disconnected"
    }

    var body: some View {
        HStack(spacing: 6) {
            Circle()
                .fill(connectionColor)
                .frame(width: 8, height: 8)
                .accessibilityLabel(connectionLabel)

            Text(formattedTime)
                .font(.system(.caption, design: .monospaced))
                .foregroundStyle(.secondary)

            Text(timezoneAbbreviation)
                .font(.caption2)
                .foregroundStyle(.tertiary)
                .accessibilityLabel("Timezone: \(timezoneAbbreviation)")
        }
        .task {
            pollingTask = Task {
                while !Task.isCancelled {
                    if let time = await BackendService.shared.fetchServerTime() {
                        serverTime = time
                        lastPoll = .now
                    }
                    try? await Task.sleep(for: .seconds(1))
                }
            }
        }
        .onDisappear {
            pollingTask?.cancel()
            pollingTask = nil
        }
    }
}

#Preview {
    ServerClockView()
        .padding()
}
