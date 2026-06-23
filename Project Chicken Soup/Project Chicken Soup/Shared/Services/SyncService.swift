//
//  SyncService.swift
//  Project Chicken Soup
//
//  Created by mck on 6/22/26.
//

import Foundation
import SwiftData
import SwiftUI
import Combine

@MainActor
final class SyncService: ObservableObject {
    static let shared = SyncService()
    
    @Published var isSyncing = false
    @Published var lastSyncTime: Date?
    @Published var pendingSyncCount: Int = 0
    @Published var syncError: String?
    
    // Offline queue of operations that need to be pushed to the server
    private var offlineQueue: [SyncOperation] = []
    private let queueKey = "com.chickensoup.sync.offlineQueue"
    
    struct SyncOperation: Codable, Identifiable {
        var id = UUID()
        var entityId: UUID
        var entityType: String // "LoreEntity" or "TemporalEvent"
        var action: String // "create", "update", "delete"
        var timestamp = Date()
    }
    
    private init() {
        loadOfflineQueue()
    }
    
    // MARK: - Queue Management
    private func loadOfflineQueue() {
        if let data = UserDefaults.standard.data(forKey: queueKey),
           let queue = try? JSONDecoder().decode([SyncOperation].self, from: data) {
            self.offlineQueue = queue
            self.pendingSyncCount = queue.count
        }
    }
    
    private func saveOfflineQueue() {
        if let data = try? JSONEncoder().encode(offlineQueue) {
            UserDefaults.standard.set(data, forKey: queueKey)
        }
        self.pendingSyncCount = offlineQueue.count
    }
    
    func queueSync(entityId: UUID, type: String, action: String = "update") {
        let operation = SyncOperation(entityId: entityId, entityType: type, action: action)
        // Remove duplicate pending operations for the same entity
        offlineQueue.removeAll { $0.entityId == entityId && $0.entityType == type }
        offlineQueue.append(operation)
        saveOfflineQueue()
    }
    
    // MARK: - Field-level Merge Resolution
    /// Merges local SwiftData LoreEntity with server response values using specific Phase 3 rules:
    /// - confidence: server-authoritative
    /// - userNotes: client-wins
    /// - sources: union
    func mergeLoreEntity(_ local: LoreEntity, with server: APILoreEntity) {
        // 1. confidence: server-authoritative
        local.confidence = server.confidence
        
        // 2. userNotes: client-wins (local wins, so only use server if local is empty)
        if local.userNotes.isEmpty {
            local.userNotes = server.userNotes ?? ""
        }
        
        // 3. sources: union
        let localSources = Set(local.sources)
        let serverSources = Set(server.sources ?? [server.source])
        local.sources = Array(localSources.union(serverSources)).sorted()
        
        // Merge remaining fields with server defaults
        local.name = server.name
        local.type = server.type
        local.summary = server.summary
    }
    
    /// Merges local SwiftData TemporalEvent with server response values using specific Phase 3 rules:
    /// - confidence: server-authoritative
    /// - userNotes: client-wins
    /// - sources: union
    func mergeTemporalEvent(_ local: TemporalEvent, with server: APITemporalEvent) {
        // 1. confidence: server-authoritative
        local.confidence = server.confidence
        
        // 2. userNotes: client-wins (local wins)
        if local.userNotes.isEmpty {
            local.userNotes = server.userNotes ?? ""
        }
        
        // 3. sources: union
        let localSources = Set(local.sources)
        let serverSources = Set(server.sources ?? [server.source])
        local.sources = Array(localSources.union(serverSources)).sorted()
        
        // Merge remaining fields
        local.title = server.title
        local.eventDescription = server.eventDescription
        local.timestamp = server.timestamp
        local.type = server.type
    }
    
    // MARK: - Synchronize Store
    func sync(context: ModelContext) async {
        guard !isSyncing else { return }
        isSyncing = true
        syncError = nil
        
        // Process offline queue (push local updates to server)
        await processOfflineQueue()
        
        // Fetch updates from Server (Neo4j simulation via APIClient)
        do {
            // Fetch remote events
            let serverEvents: [APITemporalEvent] = try await APIClient.shared.request(path: "/events")
            for serverEvent in serverEvents {
                let id = serverEvent.id
                let fetchDescriptor = FetchDescriptor<TemporalEvent>(predicate: #Predicate { $0.id == id })
                if let localEvent = try? context.fetch(fetchDescriptor).first {
                    mergeTemporalEvent(localEvent, with: serverEvent)
                } else {
                    let newEvent = TemporalEvent(
                        id: serverEvent.id,
                        title: serverEvent.title,
                        eventDescription: serverEvent.eventDescription,
                        timestamp: serverEvent.timestamp,
                        confidence: serverEvent.confidence,
                        source: serverEvent.source,
                        type: serverEvent.type,
                        userNotes: serverEvent.userNotes ?? "",
                        sources: serverEvent.sources ?? [serverEvent.source]
                    )
                    context.insert(newEvent)
                }
            }
            
            // Fetch remote entities
            let serverEntities: [APILoreEntity] = try await APIClient.shared.request(path: "/entities")
            for serverEntity in serverEntities {
                let id = serverEntity.id
                let fetchDescriptor = FetchDescriptor<LoreEntity>(predicate: #Predicate { $0.id == id })
                if let localEntity = try? context.fetch(fetchDescriptor).first {
                    mergeLoreEntity(localEntity, with: serverEntity)
                } else {
                    let newEntity = LoreEntity(
                        id: serverEntity.id,
                        name: serverEntity.name,
                        type: serverEntity.type,
                        summary: serverEntity.summary,
                        confidence: serverEntity.confidence,
                        source: serverEntity.source,
                        userNotes: serverEntity.userNotes ?? "",
                        sources: serverEntity.sources ?? [serverEntity.source]
                    )
                    context.insert(newEntity)
                }
            }
            
            try? context.save()
            lastSyncTime = Date()
        } catch {
            syncError = "Failed to pull updates from server: \(error.localizedDescription)"
        }
        
        isSyncing = false
    }
    
    private func processOfflineQueue() async {
        guard !offlineQueue.isEmpty else { return }
        
        // Simulate uploading each operation to Neo4j database endpoint
        var successfulOps: [UUID] = []
        
        for operation in offlineQueue {
            do {
                // In production, we'd make a POST/PUT request to a sync or transaction endpoint
                // e.g. let response = try await APIClient.shared.request(path: "/sync", method: "POST", ...)
                try await Task.sleep(for: .seconds(0.1)) // simulate request latency
                successfulOps.append(operation.id)
            } catch {
                print("Failed to sync operation \(operation.id): \(error.localizedDescription)")
            }
        }
        
        offlineQueue.removeAll { successfulOps.contains($0.id) }
        saveOfflineQueue()
    }
}
