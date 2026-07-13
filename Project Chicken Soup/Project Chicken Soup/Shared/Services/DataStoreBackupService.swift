import Foundation
import SwiftUI
import os

@MainActor @Observable
public final class DataStoreBackupService {
    public static let shared = DataStoreBackupService()
    private let logger = Logger(subsystem: "com.projectchickensoup.Project-Chicken-Soup", category: "DataStoreBackup")

    public var isBackingUp = false
    public var isRestoring = false
    public var lastBackupDate: Date?
    public var availableBackups: [BackupInfo] = []
    public var lastBackupError: String?
    public var lastRestoreError: String?
    public var storeIsEmptyAndBackupAvailable: Bool = false
    public var missingStoreDetected: Bool = false

    private let backupDirectoryName = "Backups"
    private let maxAutomaticBackups = 10
    private var hourlyTimer: Timer?

    private let bundleIdentifier = "milimo.Project-Chicken-Soup"
    private let appSupportSubdirectory = "Project Chicken Soup"

    private init() {}

    public func startAutomaticBackups() {
        Task { @MainActor in
            await performAutomaticBackup()
            hourlyTimer = Timer.scheduledTimer(withTimeInterval: 3600, repeats: true) { [weak self] _ in
                Task { @MainActor in
                    await self?.performAutomaticBackup()
                }
            }
        }
    }

    public func stopAutomaticBackups() {
        hourlyTimer?.invalidate()
        hourlyTimer = nil
    }

    public func refreshBackupList() {
        let backupsDir = backupsURL
        guard let contents = try? FileManager.default.contentsOfDirectory(at: backupsDir, includingPropertiesForKeys: [.creationDateKey, .fileSizeKey]) else {
            availableBackups = []
            return
        }
        var infos: [BackupInfo] = []
        for dir in contents where dir.hasDirectoryPath {
            let manifest = dir.appendingPathComponent("manifest.json")
            if let data = try? Data(contentsOf: manifest),
               let decoded = try? JSONDecoder().decode(BackupInfo.self, from: data) {
                infos.append(decoded)
            } else {
                let attrs = (try? FileManager.default.attributesOfItem(atPath: dir.path)) ?? [:]
                infos.append(BackupInfo(
                    id: dir.lastPathComponent,
                    date: (attrs[.creationDate] as? Date) ?? Date(),
                    schemaVersion: "unknown",
                    storeFiles: 0,
                    sizeBytes: (attrs[.size] as? NSNumber)?.int64Value ?? 0
                ))
            }
        }
        infos.sort { $0.date > $1.date }
        availableBackups = infos
    }

    public func performAutomaticBackup() async {
        guard !isBackingUp else { return }
        guard let sourceStoreURL = locateSwiftDataStore() else {
            logger.warning("Automatic backup skipped: SwiftData store not found on disk.")
            return
        }
        await createBackup(from: sourceStoreURL)
        refreshBackupList()
    }

    public func performManualBackup() async -> Bool {
        guard !isBackingUp else { return false }
        guard let sourceStoreURL = locateSwiftDataStore() else {
            lastBackupError = "SwiftData store not found on disk."
            return false
        }
        let result = await createBackup(from: sourceStoreURL)
        refreshBackupList()
        return result
    }

    public func restoreFromBackup(_ backup: BackupInfo) async -> Bool {
        guard !isRestoring else { return false }
        guard let currentStoreURL = locateSwiftDataStore() else {
            lastRestoreError = "Current SwiftData store not found; cannot prepare restore target."
            return false
        }
        isRestoring = true
        defer { isRestoring = false }
        lastRestoreError = nil

        let backupURL = backupsURL.appendingPathComponent(backup.id, isDirectory: true)
        guard FileManager.default.fileExists(atPath: backupURL.path) else {
            lastRestoreError = "Backup folder missing on disk."
            return false
        }

        let fm = FileManager.default
        let restoreTarget = currentStoreURL
        let quarantineName = currentStoreURL.lastPathComponent + ".quarantine.\(Date().timeIntervalSince1970)"
        let quarantineURL = currentStoreURL.deletingLastPathComponent().appendingPathComponent(quarantineName)

        do {
            try fm.moveItem(at: restoreTarget, to: quarantineURL)
        } catch {
            logger.error("Failed to quarantine current store: \(error.localizedDescription)")
            lastRestoreError = "Failed to quarantine existing store: \(error.localizedDescription)"
            return false
        }

        do {
            try fm.copyItem(at: backupURL, to: restoreTarget)
        } catch {
            logger.error("Failed to restore backup: \(error.localizedDescription)")
            do { try fm.moveItem(at: quarantineURL, to: restoreTarget) } catch { }
            lastRestoreError = "Failed to copy backup into place: \(error.localizedDescription)"
            return false
        }

        do {
            try fm.removeItem(at: quarantineURL)
        } catch {
            logger.warning("Could not remove quarantined store: \(error.localizedDescription)")
        }

        lastBackupDate = Date()
        refreshBackupList()
        return true
    }

    public func exportBackupToDocuments(_ backup: BackupInfo) async -> URL? {
        let backupURL = backupsURL.appendingPathComponent(backup.id, isDirectory: true)
        guard FileManager.default.fileExists(atPath: backupURL.path) else { return nil }
        let documentsURL = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first!

        #if os(macOS)
        let exportURL = documentsURL.appendingPathComponent("ChickenSoupBackup_\(backup.id).zip")
        #else
        let exportURL = documentsURL.appendingPathComponent("ChickenSoupBackup_\(backup.id)", isDirectory: true)
        #endif

        return await withCheckedContinuation { continuation in
            DispatchQueue.global(qos: .utility).async {
                do {
                    try FileManager.default.zipItem(at: backupURL, to: exportURL)
                    continuation.resume(returning: exportURL)
                } catch {
                    continuation.resume(returning: nil)
                }
            }
        }
    }

    public func performMigrationGuard() {
        guard let storeURL = locateSwiftDataStore() else {
            missingStoreDetected = true
            storeIsEmptyAndBackupAvailable = false
            return
        }

        let storePackage = storeURL
        let sqlitePath = storePackage.appendingPathComponent("default.sqlite").path
        let sqliteWAL = storePackage.appendingPathComponent("default.sqlite-wal").path
        let sqliteSHM = storePackage.appendingPathComponent("default.sqlite-shm").path

        let hasSQLite = FileManager.default.fileExists(atPath: sqlitePath)
        let hasWAL = FileManager.default.fileExists(atPath: sqliteWAL)
        let hasSHM = FileManager.default.fileExists(atPath: sqliteSHM)
        let storeDirEmpty = !hasSQLite && !hasWAL && !hasSHM

        missingStoreDetected = false
        storeIsEmptyAndBackupAvailable = false

        guard storeDirEmpty else { return }

        refreshBackupList()
        guard let latestBackup = availableBackups.first else {
            logger.info("Migration guard: store is empty, no backups found. Seeding fresh data.")
            return
        }

        logger.info("Migration guard: store is empty. Latest backup available: \(latestBackup.id). Prompting user.")
        storeIsEmptyAndBackupAvailable = true
    }

    public func clearMigrationGuardFlags() {
        storeIsEmptyAndBackupAvailable = false
        missingStoreDetected = false
    }

    private func locateSwiftDataStore() -> URL? {
        let appSupport = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first!
        let storeDir = appSupport
            .appendingPathComponent(bundleIdentifier, isDirectory: true)
            .appendingPathComponent("ChickenSoup", isDirectory: true)
            .appendingPathComponent("default.store", isDirectory: true)

        if FileManager.default.fileExists(atPath: storeDir.path) {
            return storeDir
        }

        let fallbackAppSupport = appSupport
            .appendingPathComponent(bundleIdentifier, isDirectory: true)
            .appendingPathComponent("default.store", isDirectory: true)
        if FileManager.default.fileExists(atPath: fallbackAppSupport.path) {
            return fallbackAppSupport
        }

        let altAppSupport = appSupport
            .appendingPathComponent(appSupportSubdirectory, isDirectory: true)
            .appendingPathComponent("default.store", isDirectory: true)
        if FileManager.default.fileExists(atPath: altAppSupport.path) {
            return altAppSupport
        }

        return nil
    }

    private var backupsURL: URL {
        let appSupport = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first!
        let dir = appSupport
            .appendingPathComponent(bundleIdentifier, isDirectory: true)
            .appendingPathComponent(backupDirectoryName, isDirectory: true)
        if !FileManager.default.fileExists(atPath: dir.path) {
            try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        }
        return dir
    }

    private func createBackup(from storeURL: URL) async -> Bool {
        isBackingUp = true
        defer { isBackingUp = false }
        lastBackupError = nil

        return await withCheckedContinuation { continuation in
            DispatchQueue.global(qos: .utility).async { [weak self] in
                let result: Bool
                let capturedBackupID: String?
                let capturedFileCount: Int
                let capturedTotalSize: Int64
                let capturedError: String?

                do {
                    let fm = FileManager.default
                    let timestamp = ISO8601DateFormatter().string(from: Date()).replacingOccurrences(of: ":", with: "-")
                    let backupID = "backup-\(timestamp)"
                    let backupDir = self?.backupsURL.appendingPathComponent(backupID, isDirectory: true)

                    try fm.createDirectory(at: backupDir!, withIntermediateDirectories: true)
                    let contents = try fm.contentsOfDirectory(at: storeURL, includingPropertiesForKeys: nil)
                    var fileCount = 0
                    var totalSize: Int64 = 0
                    for item in contents {
                        let dest = backupDir!.appendingPathComponent(item.lastPathComponent)
                        try fm.copyItem(at: item, to: dest)
                        fileCount += 1
                        if let size = try? fm.attributesOfItem(atPath: item.path)[.size] as? NSNumber {
                            totalSize += size.int64Value
                        }
                    }
                    let info = BackupInfo(id: backupID, date: Date(), schemaVersion: "SchemaV1.0.0", storeFiles: fileCount, sizeBytes: totalSize)
                    let manifestData = try JSONEncoder().encode(info)
                    try manifestData.write(to: backupDir!.appendingPathComponent("manifest.json"))

                    capturedBackupID = backupID
                    capturedFileCount = fileCount
                    capturedTotalSize = totalSize
                    capturedError = nil
                    result = true
                } catch {
                    capturedBackupID = nil
                    capturedFileCount = 0
                    capturedTotalSize = 0
                    capturedError = error.localizedDescription
                    result = false
                }

                Task { @MainActor in
                    if let id = capturedBackupID {
                        self?.enforceBackupRetention()
                        self?.lastBackupDate = Date()
                        self?.logger.info("Backup completed: \(id) (\(capturedFileCount) files, \(capturedTotalSize) bytes)")
                    }
                    self?.lastBackupError = capturedError
                    continuation.resume(returning: result)
                }
            }
        }
    }

    private func enforceBackupRetention() {
        refreshBackupList()
        let excess = availableBackups.dropFirst(maxAutomaticBackups)
        for backup in excess {
            let dir = backupsURL.appendingPathComponent(backup.id, isDirectory: true)
            try? FileManager.default.removeItem(at: dir)
        }
        refreshBackupList()
    }
}

public struct BackupInfo: Codable, Identifiable {
    public let id: String
    public let date: Date
    public let schemaVersion: String
    public let storeFiles: Int
    public let sizeBytes: Int64

    public var formattedDate: String {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.timeStyle = .short
        return formatter.string(from: date)
    }

    public var formattedSize: String {
        let kb = Double(sizeBytes) / 1024.0
        if kb < 1024 { return String(format: "%.1f KB", kb) }
        return String(format: "%.1f MB", kb / 1024.0)
    }
}

private extension FileManager {
    func zipItem(at sourceURL: URL, to destinationURL: URL) throws {
        #if os(macOS)
        let task = Process()
        task.executableURL = URL(fileURLWithPath: "/usr/bin/ditto")
        task.arguments = ["-c", "-k", "--keepParent", sourceURL.path, destinationURL.path]
        task.standardOutput = FileHandle.nullDevice
        task.standardError = FileHandle.nullDevice
        try task.run()
        task.waitUntilExit()
        if task.terminationStatus != 0 {
            throw NSError(domain: "DataStoreBackup", code: 1, userInfo: [NSLocalizedDescriptionKey: "ditto exited with code \(task.terminationStatus)"])
        }
        #else
        try createDirectory(at: destinationURL, withIntermediateDirectories: true)
        let contents = try contentsOfDirectory(at: sourceURL, includingPropertiesForKeys: nil)
        for item in contents {
            let dest = destinationURL.appendingPathComponent(item.lastPathComponent)
            try copyItem(at: item, to: dest)
        }
        #endif
    }
}
