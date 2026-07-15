//
//  BackendService.swift
//  Project Chicken Soup
//
//  Created by mck on 6/23/26.
//

import Foundation
import os
import SwiftData
import SwiftUI

public struct SuggestionItem: Identifiable, Equatable {
    public var id = UUID()
    public var text: String
    public var category: SuggestionCategory

    public static func == (lhs: SuggestionItem, rhs: SuggestionItem) -> Bool {
        lhs.text.lowercased() == rhs.text.lowercased()
    }
}

public enum SuggestionCategory: String, CaseIterable {
    case entity = "Entity"
    case event = "Event"
    case followUp = "Follow-up"
    case explore = "Explore"
    case temporal = "Temporal"

    public var icon: String {
        switch self {
        case .entity: return "person.fill"
        case .event: return "calendar.badge.clock"
        case .followUp: return "arrow.triangle.branch"
        case .explore: return "sparkle.magnifyingglass"
        case .temporal: return "clock.fill"
        }
    }

    public var color: Color {
        switch self {
        case .entity: return .blue
        case .event: return .red
        case .followUp: return .green
        case .explore: return .purple
        case .temporal: return .orange
        }
    }
}

@MainActor @Observable
public final class BackendService {
    public static let shared = BackendService()

    private let logger = Logger(subsystem: "com.chickensoup", category: "BackendService")
    
    public var isFetchingEvents = false
    public var isSubmittingQuery = false
    public var isSolvingSpacetime = false

    public var conversationId: String? = nil

    public var lastError: APIError?

    public let graph = GraphService.shared
    public let wiki = WikiService.shared
    public let chat = ChatService.shared
    public let config = ConfigService.shared
    public let almanac = AlmanacService.shared

    private init() {}
    
    // MARK: - Merge Helpers (previously in SyncService)

    /// Merges server values into a local LoreEntity using Phase 3 rules:
    /// - confidence: server-authoritative
    /// - userNotes: client-wins (kept unless local is empty)
    /// - sources: union of local and server
    private func mergeLoreEntity(_ local: LoreEntity, with server: APILoreEntity) {
        local.name = server.name
        local.type = server.type
        local.summary = server.summary
        local.confidence = server.confidence
        let localSources = Set(local.sources)
        let serverSources = Set(server.sources ?? [server.source])
        local.sources = Array(localSources.union(serverSources)).sorted()
        if local.userNotes.isEmpty {
            local.userNotes = server.userNotes ?? ""
        }
    }

    /// Merges server values into a local LoreEntity using Phase 3 rules.
    private func mergeEntity(_ local: LoreEntity, with server: APILoreEntity) {
        local.name = server.name
        local.type = server.type
        local.summary = server.summary
        local.confidence = server.confidence
        let localSources = Set(local.sources)
        let serverSources = Set(server.sources ?? [server.source])
        local.sources = Array(localSources.union(serverSources)).sorted()
    }

    // MARK: - Fetch Temporal Events
    public func fetchTemporalEvents(context: ModelContext) async {
        isFetchingEvents = true
        defer { isFetchingEvents = false }

        do {
            struct EventsResponse: Codable {
                let events: [APIRawEvent]
            }
            struct APIRawEvent: Codable {
                let id: String
                let title: String
                let description: String?
                let date: String?
                let confidence: Double?
                let source: String?
                let type: String?
                let sources: [String]?
            }

            let response: EventsResponse = try await APIClient.shared.request(path: "/events")
            let dateParser = DateFormatter()
            dateParser.dateFormat = "yyyy-MM-dd"
            dateParser.timeZone = TimeZone(abbreviation: "UTC")

            let allLocal = try? context.fetch(FetchDescriptor<TemporalEvent>())
            var seenTitles = Set<String>()

            for apiEvent in response.events {
                seenTitles.insert(apiEvent.title)

                let existing = allLocal?.first(where: { $0.title == apiEvent.title })
                if let existing {
                    existing.eventDescription = apiEvent.description ?? ""
                    if let dateStr = apiEvent.date, let d = dateParser.date(from: dateStr) {
                        existing.timestamp = d
                    }
                    existing.confidence = apiEvent.confidence ?? 1.0
                    existing.source = apiEvent.source ?? "Unknown"
                    existing.type = apiEvent.type ?? "anomaly"
                    existing.sources = apiEvent.sources ?? []
                } else {
                    var timestamp = Date()
                    if let dateStr = apiEvent.date, let d = dateParser.date(from: dateStr) {
                        timestamp = d
                    }
                    let newEvent = TemporalEvent(
                        title: apiEvent.title,
                        eventDescription: apiEvent.description ?? "",
                        timestamp: timestamp,
                        confidence: apiEvent.confidence ?? 1.0,
                        source: apiEvent.source ?? "Unknown",
                        type: apiEvent.type ?? "anomaly",
                        sources: apiEvent.sources ?? []
                    )
                    context.insert(newEvent)
                }
            }

            for local in allLocal ?? [] where !seenTitles.contains(local.title) {
                context.delete(local)
            }
            try? context.save()
        } catch {
            self.lastError = APIError.requestFailed(error)
            logger.error("Failed to fetch events from backend: \(error.localizedDescription)")
        }
    }

    // MARK: - Fetch Lore Entities
    public func fetchLoreEntities(context: ModelContext) async {
        do {
            let apiEntities: [APILoreEntity] = try await APIClient.shared.request(path: "/entities")

            for apiEntity in apiEntities {
                let id = apiEntity.id
                let fetchDescriptor = FetchDescriptor<LoreEntity>(predicate: #Predicate { $0.id == id })
                if let existing = try? context.fetch(fetchDescriptor).first {
                    mergeLoreEntity(existing, with: apiEntity)
                } else {
                    let newEntity = LoreEntity(
                        id: apiEntity.id,
                        name: apiEntity.name,
                        type: apiEntity.type,
                        summary: apiEntity.summary,
                        confidence: apiEntity.confidence,
                        source: apiEntity.source,
                        userNotes: apiEntity.userNotes ?? "",
                        sources: apiEntity.sources ?? [apiEntity.source]
                    )
                    context.insert(newEntity)
                }
            }
            try? context.save()

            let serverEntityIDs = Set(apiEntities.map(\.id))
            let allLocalEntities = try? context.fetch(FetchDescriptor<LoreEntity>())
            for local in allLocalEntities ?? [] where !serverEntityIDs.contains(local.id) {
                context.delete(local)
            }
            try? context.save()

            if graph.focusedEntityName.isEmpty {
                await graph.autoSelectInitialEntity(context: context)
            }
        } catch {
            self.lastError = APIError.requestFailed(error)
            logger.error("Failed to fetch entities from backend: \(error.localizedDescription)")
        }
    }

    @discardableResult
    public func deleteLoreEntity(name: String) async -> Bool {
        do {
            let response: APIEntityDeleteResponse = try await APIClient.shared.request(
                path: "/entities/\(name)", method: "DELETE"
            )
            return response.success
        } catch {
            logger.error("Failed to delete entity '\(name)': \(error)")
            return false
        }
    }

    public func submitQuery(_ text: String, isStructured: Bool, context: ModelContext) async -> BackendQueryResult {
        isSubmittingQuery = true
        defer { isSubmittingQuery = false }

        do {
            var bodyDict: [String: Any] = ["query": text, "structured": isStructured]
            if let cid = conversationId {
                bodyDict["conversation_id"] = cid
            }
            let bodyData = try JSONSerialization.data(withJSONObject: bodyDict)
            let response: APIQueryResponse = try await APIClient.shared.request(path: "/query", method: "POST", body: bodyData)

            if let cid = response.conversationId {
                conversationId = cid
            }

            for apiEvent in response.inferredEvents {
                let newEvent = TemporalEvent(
                    id: apiEvent.id,
                    title: apiEvent.title,
                    eventDescription: apiEvent.eventDescription,
                    timestamp: apiEvent.timestamp,
                    confidence: apiEvent.confidence,
                    source: apiEvent.source,
                    type: apiEvent.type
                )
                context.insert(newEvent)
            }

            for apiEntity in response.inferredEntities {
                let newEntity = LoreEntity(
                    id: apiEntity.id,
                    name: apiEntity.name,
                    type: apiEntity.type,
                    summary: apiEntity.summary,
                    confidence: apiEntity.confidence,
                    source: apiEntity.source
                )
                context.insert(newEntity)
            }

                try? context.save()
            return BackendQueryResult(
                responseText: response.responseText,
                conversationId: response.conversationId,
                taskId: response.taskId,
                threadId: response.threadId,
                status: response.status
            )
        } catch {
            self.lastError = APIError.requestFailed(error)
            logger.error("Failed to submit query: \(error.localizedDescription)")
            return BackendQueryResult(
                responseText: "Error processing query: \(error.localizedDescription)",
                conversationId: conversationId,
                taskId: nil
            )
        }
    }

    public func solveSpacetimeGeodesic(gravity: Double, velocity: Double, intensity: Double) async throws -> APITimeTravelSimulationResponse {
        isSolvingSpacetime = true
        defer { isSolvingSpacetime = false }

        do {
            let bodyDict: [String: Any] = ["gravity": gravity, "velocity": velocity, "intensity": intensity]
            let bodyData = try JSONSerialization.data(withJSONObject: bodyDict)
            return try await APIClient.shared.request(path: "/simulate", method: "POST", body: bodyData)
        } catch {
            self.lastError = APIError.requestFailed(error)
            logger.error("Failed to solve spacetime geodesic: \(error.localizedDescription)")
            throw APIError.requestFailed(error)
        }
    }
    
    /// Selects an entity. Delegated to GraphService.
    public func selectEntity(_ name: String, context: ModelContext) {
        graph.selectEntity(name, context: context)
    }

    /// Delegated to GraphService.
    public func navigateBack(context: ModelContext) {
        graph.navigateBack(context: context)
    }

    /// Delegated to GraphService.
    public func navigateForward(context: ModelContext) {
        graph.navigateForward(context: context)
    }

    /// Delegated to GraphService.
    public func fetchNeighborhood(for name: String, context: ModelContext) async {
        await graph.fetchNeighborhood(for: name, context: context)
    }
    
    // MARK: - Chat Delegation

    public func fetchChatIngestStatus() async {
        await chat.fetchChatIngestStatus()
    }

    public func triggerChatIngest() async -> Bool {
        await chat.triggerChatIngest()
    }

    public func setUserName(_ name: String) async -> Bool {
        await chat.setUserName(name)
    }

    public func clearUnreadWikiPages() {
        chat.clearUnreadWikiPages()
    }

    public func fetchIngestHistory() async {
        await chat.fetchIngestHistory()
    }

    public func fetchChatNotifications() async {
        await chat.fetchChatNotifications()
    }

    public var suggestions: [SuggestionItem] = []

    func regenerateSuggestions(messages: [ChatMessage], entities: [LoreEntity], events: [TemporalEvent]) {
        var results: [SuggestionItem] = []
        let focusedName = graph.focusedEntityName.trimmingCharacters(in: .whitespaces)

        if !focusedName.isEmpty {
            results.append(SuggestionItem(text: "What is \(focusedName)?", category: .entity))
            results.append(SuggestionItem(text: "Evidence for \(focusedName)", category: .entity))
            if let neighborhood = graph.neighborhood {
                for conn in neighborhood.connections.prefix(2) {
                    results.append(SuggestionItem(
                        text: "How does \(conn.neighbor.name) relate to \(focusedName)?",
                        category: .followUp
                    ))
                }
            }
        }

        if messages.count >= 2 {
            let lastAssistantMessages = messages.filter { !$0.isUser }.suffix(2)
            for msg in lastAssistantMessages {
                let words = msg.text.split(separator: " ").filter { $0.count > 3 }
                for word in words.prefix(2) {
                    let topic = String(word).trimmingCharacters(in: .punctuationCharacters)
                    if !topic.isEmpty && topic.count > 2 {
                        let q = "Tell me more about \(topic)"
                        if !results.contains(where: { $0.text.lowercased() == q.lowercased() }) {
                            results.append(SuggestionItem(text: q, category: .followUp))
                        }
                    }
                }
            }
            let general = "What else should I know?"
            if !results.contains(where: { $0.text.lowercased() == general.lowercased() }) {
                results.append(SuggestionItem(text: general, category: .followUp))
            }
        }

        let personEntities = entities.filter { $0.type == "Person" && !focusedName.lowercased().contains($0.name.lowercased()) }.prefix(1)
        for entity in personEntities {
            results.append(SuggestionItem(text: "Who is \(entity.name)?", category: .entity))
        }

        let conceptEntities = entities.filter { $0.type == "Concept" && !focusedName.lowercased().contains($0.name.lowercased()) }.prefix(1)
        for entity in conceptEntities {
            results.append(SuggestionItem(text: "Explain \(entity.name)", category: .explore))
        }

        let projectEntities = entities.filter { $0.type == "Project" }.prefix(1)
        for entity in projectEntities {
            results.append(SuggestionItem(text: "What is the \(entity.name) project?", category: .explore))
        }

        if let event = events.first {
            let year = Calendar.current.component(.year, from: event.timestamp)
            if year > 1900 {
                let q = "What happened in \(year)?"
                if !results.contains(where: { $0.text.lowercased() == q.lowercased() }) {
                    results.append(SuggestionItem(text: q, category: .temporal))
                }
            }
        }

        let explorationPrompts = explorationFallbacks(focusedName: focusedName)
        for prompt in explorationPrompts {
            if !results.contains(where: { $0.text.lowercased() == prompt.lowercased() }) {
                results.append(SuggestionItem(text: prompt, category: .explore))
            }
        }

        var seen = Set<String>()
        suggestions = results.filter { seen.insert($0.text.lowercased()).inserted }.prefix(4).map { $0 }
    }

    private func explorationFallbacks(focusedName: String) -> [String] {
        var prompts = [
            "Plot timelines connected to historical events",
            "Show connections between whistleblowers",
            "What crash retrievals are documented?",
            "How does field manipulation work?",
        ]
        if !focusedName.isEmpty {
            prompts.insert("Timeline of \(focusedName)", at: 0)
        }
        return prompts
    }

    public func clearWikiContent() async -> APIWikiClearResponse? {
        await wiki.clearWikiContent()
    }

    public func exportWiki() async -> APIWikiExportResponse? {
        await wiki.exportWiki()
    }

    public func importWiki(fileURL: URL) async -> APIWikiImportResponse? {
        await wiki.importWiki(fileURL: fileURL)
    }

    /// Refresh the local cache of both lore entities and temporal events after an ingest operation.
    public func refreshAfterIngest(context: ModelContext) async {
        await fetchLoreEntities(context: context)
        await fetchTemporalEvents(context: context)
    }

    // MARK: - Wiki Service Delegation
    public func fetchWikiPages(pageType: String? = nil) async {
        await wiki.fetchWikiPages(pageType: pageType)
    }

    public func fetchWikiPageDetail(slug: String, pageType: String) async -> APIWikiPageDetail? {
        await wiki.fetchWikiPageDetail(slug: slug, pageType: pageType)
    }

    @discardableResult
    public func deleteWikiPage(slug: String, pageType: String, hard: Bool = false) async -> APIWikiDeleteResponse? {
        await wiki.deleteWikiPage(slug: slug, pageType: pageType, hard: hard)
    }

    // MARK: - Config Delegation
    public func fetchConfig() async {
        await config.fetchConfig()
    }

    public func saveConfig(backend: String, ibmToken: String?, dwaveToken: String?, ionqToken: String?, hardwareEnabled: Bool) async -> Bool {
        await config.saveConfig(backend: backend, ibmToken: ibmToken, dwaveToken: dwaveToken, ionqToken: ionqToken, hardwareEnabled: hardwareEnabled)
    }

    public func saveLLMConfig(provider: String?, model: String?) async -> Bool {
        await config.saveLLMConfig(provider: provider, model: model)
    }

    public func refreshLLMDiscovery() async {
        await config.refreshLLMDiscovery()
    }

    public func probeLLMProvider(_ name: String) async -> (provider: String, available: Bool, models: [String]) {
        await config.probeLLMProvider(name)
    }

    @discardableResult
    public func approveResearch(threadId: String) async -> (success: Bool, summary: String)? {
        do {
            struct ApproveResponse: Codable {
                let success: Bool
                let thread_id: String
                let summary: String
            }
            let bodyData = try JSONSerialization.data(withJSONObject: [:])
            let response: ApproveResponse = try await APIClient.shared.request(
                path: "/research/\(threadId)/approve",
                method: "POST",
                body: bodyData
            )
            return (success: response.success, summary: response.summary)
        } catch {
            logger.error("Failed to approve research for thread '\(threadId)': \(error.localizedDescription)")
            return nil
        }
    }

    public func fetchStatusProgress() async -> APIStatusProgress? {
        do {
            let response: APIStatusProgress = try await APIClient.shared.request(path: "/status/progress")
            return response
        } catch {
            logger.error("Failed to fetch status progress: \(error.localizedDescription)")
            return nil
        }
    }

    public func fetchServerTime() async -> Date? {
        do {
            let response: APIServerTime = try await APIClient.shared.request(path: "/status/time")
            return ISO8601DateFormatter().date(from: response.iso8601)
        } catch {
            logger.error("Failed to fetch server time: \(error.localizedDescription)")
            return nil
        }
    }

    public func performSearch(query: String, limit: Int = 20) async -> APISearchResponse? {
        do {
            let response: APISearchResponse = try await APIClient.shared.request(
                path: "/search",
                method: "GET",
                queryItems: [
                    URLQueryItem(name: "q", value: query),
                    URLQueryItem(name: "limit", value: String(limit)),
                ]
            )
            return response
        } catch {
            logger.error("Search failed: \(error.localizedDescription)")
            return nil
        }
    }

    // MARK: - Neo4j Backup

    public func fetchNeo4jBackups() async -> [APIDBBackup] {
        do {
            let response: APIDBBackupListResponse = try await APIClient.shared.request(path: "/neo4j/backups")
            return response.backups
        } catch {
            logger.error("Failed to fetch Neo4j backups: \(error.localizedDescription)")
            return []
        }
    }

    @discardableResult
    public func createNeo4jBackup() async -> Bool {
        do {
            let response: APIDBBackupCreateResponse = try await APIClient.shared.request(
                path: "/neo4j/backup", method: "POST"
            )
            return response.success
        } catch {
            logger.error("Failed to create Neo4j backup: \(error.localizedDescription)")
            return false
        }
    }

    @discardableResult
    public func restoreNeo4jBackup(_ filename: String) async -> Bool {
        do {
            let encoded = filename.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? filename
            let response: APIDBBackupRestoreResponse = try await APIClient.shared.request(
                path: "/neo4j/restore/\(encoded)", method: "POST"
            )
            return response.success
        } catch {
            logger.error("Failed to restore Neo4j backup: \(error.localizedDescription)")
            return false
        }
    }
}

public struct BackendQueryResult {
    public let responseText: String
    public let conversationId: String?
    public let taskId: String?
    public let threadId: String?
    public let status: String?

    public init(responseText: String, conversationId: String? = nil, taskId: String? = nil, threadId: String? = nil, status: String? = nil) {
        self.responseText = responseText
        self.conversationId = conversationId
        self.taskId = taskId
        self.threadId = threadId
        self.status = status
    }
}
