import SwiftUI

struct Neo4jBackupSettingsView: View {
    @State private var backups: [APIDBBackup] = []
    @State private var isCreatingBackup = false
    @State private var isRestoring = false
    @State private var restoreFileName: String?
    @State private var showRestoreConfirm = false
    @State private var lastError: String?
    @State private var lastSuccess: String?

    var body: some View {
        Section {
            if !backups.isEmpty {
                ForEach(backups.prefix(5)) { backup in
                    HStack {
                        VStack(alignment: .leading, spacing: 2) {
                            Text(backup.filename)
                                .font(.caption)
                                .lineLimit(1)
                            Text(backup.sizeHuman)
                                .font(.caption2)
                                .foregroundStyle(.secondary)
                        }
                        Spacer()
                        Button("Restore") {
                            restoreFileName = backup.filename
                            showRestoreConfirm = true
                        }
                        .font(.caption)
                        .foregroundStyle(.orange)
                        .buttonStyle(.plain)
                    }
                }
            } else {
                LabeledContent("Backups", value: "None yet")
                    .foregroundStyle(.secondary)
            }

            Button(action: { createBackup() }) {
                HStack {
                    if isCreatingBackup {
                        ProgressView()
                            .scaleEffect(0.8)
                    }
                    Text(isCreatingBackup ? "Creating..." : "Create Backup Now")
                }
                .frame(maxWidth: .infinity)
            }
            .disabled(isCreatingBackup || isRestoring)

            if let error = lastError {
                Label(error, systemImage: "exclamationmark.triangle")
                    .font(.caption).foregroundStyle(.red)
            }
            if let success = lastSuccess {
                Label(success, systemImage: "checkmark.circle")
                    .font(.caption).foregroundStyle(.green)
            }

            if isRestoring {
                HStack {
                    ProgressView()
                        .scaleEffect(0.8)
                    Text("Restoring — server will restart...")
                        .font(.caption)
                }
                .foregroundStyle(.orange)
            }
        } header: {
            HStack {
                Image(systemName: "cylinder.split.1x2")
                    .foregroundStyle(.secondary)
                Text("Neo4j Database Backups")
            }
        } footer: {
            Text("Restore stops the database, replaces data, and restarts. Takes ~30-60s.")
                .font(.caption2)
        }
        .confirmationDialog("Restore Backup?",
            isPresented: $showRestoreConfirm,
            titleVisibility: .visible) {
            Button("Restore", role: .destructive) { restoreBackup() }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text("This will replace the current Neo4j database with the backup. The server will be briefly unavailable.")
        }
        .task { await loadBackups() }
    }

    private func loadBackups() async {
        backups = await BackendService.shared.fetchNeo4jBackups()
    }

    private func createBackup() {
        isCreatingBackup = true
        lastError = nil
        lastSuccess = nil
        Task {
            let ok = await BackendService.shared.createNeo4jBackup()
            await MainActor.run {
                isCreatingBackup = false
                if ok {
                    lastSuccess = "Backup created"
                    Task { await loadBackups() }
                } else {
                    lastError = "Backup failed — check server log"
                }
            }
        }
    }

    private func restoreBackup() {
        guard let name = restoreFileName else { return }
        isRestoring = true
        lastError = nil
        lastSuccess = nil
        Task {
            let ok = await BackendService.shared.restoreNeo4jBackup(name)
            await MainActor.run {
                isRestoring = false
                if ok {
                    lastSuccess = "Restore complete"
                } else {
                    lastError = "Restore failed"
                }
            }
        }
    }
}
