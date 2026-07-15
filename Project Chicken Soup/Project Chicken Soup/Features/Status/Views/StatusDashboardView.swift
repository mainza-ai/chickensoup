import SwiftUI

struct StatusDashboardView: View {
    @State private var progress: APIStatusProgress?
    @State private var pollingTask: Task<Void, Never>?

    var body: some View {
        NavigationStack {
            List {
                ServerClockView()
                    .listRowSeparator(.hidden)
                    .listRowInsets(EdgeInsets(top: 4, leading: 0, bottom: 4, trailing: 0))

                ReconciliationSectionView(section: progress?.reconciliation)
                IdleIngestionSectionView(section: progress?.idleIngestion)
                FallbackRetrySectionView(section: progress?.fallbackRetry)
                LLMClientSectionView(section: progress?.llmClient)
                Neo4jSnapshotSectionView(section: progress?.neo4j)
            }
            .navigationTitle("System Status")
            .task {
                pollingTask = Task {
                    while !Task.isCancelled {
                        progress = await BackendService.shared.fetchStatusProgress()
                        try? await Task.sleep(for: .seconds(2))
                    }
                }
            }
            .onDisappear {
                pollingTask?.cancel()
                pollingTask = nil
            }
        }
    }
}

#Preview {
    StatusDashboardView()
}
