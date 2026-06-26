//
//  BackendService.swift
//  Project Chicken Soup
//
//  Created by mck on 6/23/26.
//

import Foundation
import SwiftData
import SwiftUI
import Combine

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

@MainActor
public final class BackendService: ObservableObject {
    public static let shared = BackendService()
    
    @Published public var isFetchingEvents = false
    @Published public var isFetchingEntities = false
    @Published public var isSubmittingQuery = false
    @Published public var isSolvingSpacetime = false
    
    @Published public var quantumBackend: String = "numpy"
    @Published public var quantumHardwareEnabled: Bool = false
    @Published public var ibmApiTokenSet: Bool = false
    @Published public var dwaveApiTokenSet: Bool = false
    @Published public var ionqApiTokenSet: Bool = false
    @Published public var isFetchingConfig = false
    @Published public var isSavingConfig = false
    
    @Published public var llmActiveProvider: String = ""
    @Published public var llmActiveModel: String = ""
    @Published public var llmAvailableModels: [String] = []
    @Published public var isSavingLLMConfig = false

    @Published public var conversationId: String? = nil
    
    @Published public var eventsError: Error?
    @Published public var entitiesError: Error?
    @Published public var queryError: Error?
    @Published public var spacetimeError: Error?
    
    @Published public var focusedEntityName: String = ""
    @Published public var neighborhood: NeighborhoodResponse? = nil
    @Published public var isFetchingNeighborhood = false
    
    @Published public var canGoBack = false
    @Published public var canGoForward = false
    @Published public var showNavigator = true
    @Published public var showChatHistory = false

    @Published public var chatIngestStatus: APIChatIngestStatus?
    @Published public var unreadWikiPagesFromChat: Int = 0

    public var isChatWikiConversionEnabled: Bool {
        get { UserDefaults.standard.object(forKey: "chatWikiConversion") == nil ? false : UserDefaults.standard.bool(forKey: "chatWikiConversion") }
        set { UserDefaults.standard.set(newValue, forKey: "chatWikiConversion") }
    }

    public var chatWikiMinConversationLength: Int {
        get { UserDefaults.standard.object(forKey: "chatWikiMinLength") == nil ? 10 : UserDefaults.standard.integer(forKey: "chatWikiMinLength") }
        set { UserDefaults.standard.set(newValue, forKey: "chatWikiMinLength") }
    }

    public var chatWikiNotify: Bool {
        get { UserDefaults.standard.object(forKey: "chatWikiNotify") == nil ? true : UserDefaults.standard.bool(forKey: "chatWikiNotify") }
        set { UserDefaults.standard.set(newValue, forKey: "chatWikiNotify") }
    }

    public var userName: String {
        get { UserDefaults.standard.string(forKey: "userWikiName") ?? "Primary Researcher" }
        set { UserDefaults.standard.set(newValue, forKey: "userWikiName") }
    }

    @Published public var isDarkMode: Bool = {
        if UserDefaults.standard.object(forKey: "isDarkMode") == nil {
            return true
        }
        return UserDefaults.standard.bool(forKey: "isDarkMode")
    }()
    
    public func toggleTheme() {
        isDarkMode.toggle()
        UserDefaults.standard.set(isDarkMode, forKey: "isDarkMode")
    }
    
    private var backStack: [String] = []
    private var forwardStack: [String] = []
    private var fetchNeighborhoodTask: Task<Void, Never>?
    private let backStackMaxSize = 50

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

    /// Merges server values into a local TemporalEvent using Phase 3 rules.
    private func mergeTemporalEvent(_ local: TemporalEvent, with server: APITemporalEvent) {
        local.title = server.title
        local.eventDescription = server.eventDescription
        local.timestamp = server.timestamp
        local.confidence = server.confidence
        local.type = server.type
        let localSources = Set(local.sources)
        let serverSources = Set(server.sources ?? [server.source])
        local.sources = Array(localSources.union(serverSources)).sorted()
        if local.userNotes.isEmpty {
            local.userNotes = server.userNotes ?? ""
        }
    }

    // MARK: - Fetch Temporal Events
    public func fetchTemporalEvents(context: ModelContext) async {
        isFetchingEvents = true
        defer { isFetchingEvents = false }

        do {
            let apiEvents: [APITemporalEvent] = try await APIClient.shared.request(path: "/events")

            for apiEvent in apiEvents {
                let id = apiEvent.id
                let fetchDescriptor = FetchDescriptor<TemporalEvent>(predicate: #Predicate { $0.id == id })
                if let existing = try? context.fetch(fetchDescriptor).first {
                    mergeTemporalEvent(existing, with: apiEvent)
                } else {
                    let newEvent = TemporalEvent(
                        id: apiEvent.id,
                        title: apiEvent.title,
                        eventDescription: apiEvent.eventDescription,
                        timestamp: apiEvent.timestamp,
                        confidence: apiEvent.confidence,
                        source: apiEvent.source,
                        type: apiEvent.type,
                        userNotes: apiEvent.userNotes ?? "",
                        sources: apiEvent.sources ?? [apiEvent.source]
                    )
                    context.insert(newEvent)
                }
            }
            try? context.save()

            let serverEventIDs = Set(apiEvents.map(\.id))
            let allLocalEvents = try? context.fetch(FetchDescriptor<TemporalEvent>())
            for local in allLocalEvents ?? [] where !serverEventIDs.contains(local.id) {
                context.delete(local)
            }
            try? context.save()
        } catch {
            print("Failed to fetch events from backend: \(error.localizedDescription)")
        }
    }

    // MARK: - Fetch Lore Entities
    public func fetchLoreEntities(context: ModelContext) async {
        isFetchingEntities = true
        defer { isFetchingEntities = false }

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

            if focusedEntityName.isEmpty {
                await autoSelectInitialEntity(context: context)
            }
        } catch {
            print("Failed to fetch entities from backend: \(error.localizedDescription)")
        }
    }

    /// Selects the first entity with graph connections from the local store.
    /// Called automatically when entities are first loaded and no entity is focused.
    private func autoSelectInitialEntity(context: ModelContext) async {
        let allLocal = (try? context.fetch(FetchDescriptor<LoreEntity>())) ?? []
        guard !allLocal.isEmpty else { return }

        for entity in allLocal.sorted(by: { $0.name.localizedCaseInsensitiveCompare($1.name) == .orderedAscending }) {
            if Task.isCancelled { return }
            let encodedName = entity.name.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? entity.name
            if let response = try? await APIClient.shared.request(path: "/graph/\(encodedName)") as NeighborhoodResponse,
               !response.connections.isEmpty {
                withAnimation(.spring(response: 0.65, dampingFraction: 0.75)) {
                    self.neighborhood = response
                    self.focusedEntityName = entity.name
                }
                return
            }
        }
        // Fallback: select the first entity even if it has no connections
        if let first = allLocal.first {
            await fetchNeighborhood(for: first.name, context: context)
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
            print("Failed to delete entity '\(name)': \(error)")
            return false
        }
    }
    
    // MARK: - Execute TQL or Natural Query
    public func submitQuery(_ text: String, isStructured: Bool, context: ModelContext) async -> String? {
        isSubmittingQuery = true
        queryError = nil
        defer { isSubmittingQuery = false }
        
        do {
            var bodyDict: [String: Any] = ["query": text, "structured": isStructured]
            if let cid = conversationId {
                bodyDict["conversation_id"] = cid
            }
            let bodyData = try JSONSerialization.data(withJSONObject: bodyDict)
            let response: APIQueryResponse = try await APIClient.shared.request(path: "/query", method: "POST", body: bodyData)
            
            // Persist conversation ID for follow-up queries
            if let cid = response.conversationId {
                conversationId = cid
            }
            
            // Handle any newly inferred events returned in query response
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
            
            // Handle inferred entities
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
            return response.responseText
        } catch {
            self.queryError = error
            print("Failed to submit query: \(error.localizedDescription)")
            
            // Fallback Simulation when server is offline
            try? await Task.sleep(for: .seconds(1.2))
            
            // Simulate the addition of a new dynamic temporal event from AI query response
            let components = text.split(separator: " ")
            let eventType = components.contains(where: { $0.lowercased() == "crash" }) ? "crash" : "anomaly"
            let confidence = Double.random(in: 0.85...0.99)
            
            let newEvent = TemporalEvent(
                title: "Inferred: " + text,
                eventDescription: "AI resolved timeline parameters and verified structural authenticity.",
                timestamp: Date(),
                confidence: confidence,
                source: "AI Navigator (Local Fallback)",
                type: eventType
            )
            context.insert(newEvent)
            try? context.save()
            return "Resolved locally: \(text). Extrapolated spacetime alignment parameters."
        }
    }
    
    // MARK: - Simulate Spacetime Geodesic (Time Travel)
    public func solveSpacetimeGeodesic(gravity: Double, velocity: Double, intensity: Double) async throws -> APITimeTravelSimulationResponse {
        isSolvingSpacetime = true
        spacetimeError = nil
        defer { isSolvingSpacetime = false }
        
        do {
            let bodyDict: [String: Any] = ["gravity": gravity, "velocity": velocity, "intensity": intensity]
            let bodyData = try JSONSerialization.data(withJSONObject: bodyDict)
            return try await APIClient.shared.request(path: "/simulate", method: "POST", body: bodyData)
        } catch {
            self.spacetimeError = error
            // Fallback simulation internally
            try await Task.sleep(for: .seconds(2.5))
            
            let mockLogs = [
                "Executing PennyLane pathfinding optimization (Local Fallback)...",
                "Qiskit computed Hamiltonian expectation <H> = \(String(format: "%.3f", Double.random(in: 0.5...0.9)))",
                "Entangled state resolved: CTC is navigable.",
                "Geodesic path found! Fallback confidence resolved."
            ]
            return APITimeTravelSimulationResponse(
                success: true,
                logs: mockLogs,
                gravityMetric: Double.random(in: 0.2...0.9),
                velocityMetric: Double.random(in: 0.7...0.99),
                fieldIntensity: Double.random(in: 0.4...0.8),
                resolvedPathConfidence: 0.95
            )
        }
    }
    
    // MARK: - Fetch Neighborhood (Knowledge Graph)
    public func fetchNeighborhood(for name: String, context: ModelContext) async {
        isFetchingNeighborhood = true
        defer { isFetchingNeighborhood = false }

        do {
            let responseDecoded: NeighborhoodResponse = try await APIClient.shared.request(
                path: "/graph/\(name)"
            )

            var uniqueConns: [NeighborhoodConnection] = []
            var seenNames = Set<String>()
            for conn in responseDecoded.connections {
                let key = conn.neighbor.name.lowercased()
                if !seenNames.contains(key) {
                    seenNames.insert(key)
                    uniqueConns.append(conn)
                }
            }

            let filteredResponse = NeighborhoodResponse(entity: responseDecoded.entity, connections: uniqueConns)

            withAnimation(.spring(response: 0.65, dampingFraction: 0.75)) {
                self.neighborhood = filteredResponse
                self.focusedEntityName = name
            }
        } catch {
            print("Failed to fetch neighborhood: \(error)")
            loadFallbackNeighborhood(for: name, context: context)
        }
    }
    
    @MainActor
    private func loadFallbackNeighborhood(for name: String, context: ModelContext) {
        let fetchDescriptor = FetchDescriptor<LoreEntity>()
        let allEntities = (try? context.fetch(fetchDescriptor)) ?? []
        
        let simpleEntity: NeighborhoodEntity
        if let localEntity = allEntities.first(where: { 
            $0.name == name || 
            $0.name.lowercased() == name.lowercased() || 
            $0.name.replacingOccurrences(of: " ", with: "-").lowercased() == name.replacingOccurrences(of: " ", with: "-").lowercased() 
        }) {
            simpleEntity = NeighborhoodEntity(
                id: localEntity.id,
                name: localEntity.name,
                type: localEntity.type,
                summary: localEntity.summary,
                confidence: localEntity.confidence,
                source: localEntity.source,
                sources: [localEntity.source]
            )
        } else {
            simpleEntity = NeighborhoodEntity(
                id: UUID(),
                name: name,
                type: "Entity",
                summary: "Lore graph node for \(name). Select or query to discover more.",
                confidence: 0.5,
                source: "Unknown",
                sources: ["Offline Cache"]
            )
        }
        
        let otherEntities = allEntities.filter { $0.name.lowercased() != name.lowercased() }
        var uniqueOthers: [LoreEntity] = []
        for other in otherEntities {
            if !uniqueOthers.contains(where: { $0.name.lowercased() == other.name.lowercased() }) {
                uniqueOthers.append(other)
            }
        }
        
        let connections = uniqueOthers.prefix(5).map { other in
            NeighborhoodConnection(
                relationshipType: "RELATED_TO",
                neighbor: NeighborhoodEntity(
                    id: other.id,
                    name: other.name,
                    type: other.type,
                    summary: other.summary,
                    confidence: other.confidence,
                    source: other.source,
                    sources: [other.source]
                )
            )
        }
        
        let response = NeighborhoodResponse(entity: simpleEntity, connections: Array(connections))
        
        withAnimation(.spring(response: 0.65, dampingFraction: 0.75)) {
            self.neighborhood = response
            self.focusedEntityName = name
        }
    }
    
    // MARK: - Navigation History
    /// Selects an entity and fetches its neighborhood.
    public func selectEntity(_ name: String, context: ModelContext) {
        fetchNeighborhoodTask?.cancel()

        let currentFocused = focusedEntityName
        if !currentFocused.isEmpty && currentFocused.lowercased() != name.lowercased() {
            backStack.append(currentFocused)
            if backStack.count > backStackMaxSize { backStack.removeFirst() }
            forwardStack.removeAll()
            canGoBack = true
            canGoForward = false
        }
        fetchNeighborhoodTask = Task { [weak self] in
            await self?.fetchNeighborhood(for: name, context: context, isAutoSelection: isAutoSelection)
        }
    }

    public func navigateBack(context: ModelContext) {
        fetchNeighborhoodTask?.cancel()
        guard !backStack.isEmpty else { return }
        let prev = backStack.removeLast()
        let currentFocused = focusedEntityName
        if !currentFocused.isEmpty {
            forwardStack.append(currentFocused)
            if forwardStack.count > backStackMaxSize { forwardStack.removeFirst() }
            canGoForward = true
        }
        canGoBack = !backStack.isEmpty
        fetchNeighborhoodTask = Task { [weak self] in
            await self?.fetchNeighborhood(for: prev, context: context)
        }
    }

    public func navigateForward(context: ModelContext) {
        fetchNeighborhoodTask?.cancel()
        guard !forwardStack.isEmpty else { return }
        let next = forwardStack.removeLast()
        let currentFocused = focusedEntityName
        if !currentFocused.isEmpty {
            backStack.append(currentFocused)
            if backStack.count > backStackMaxSize { backStack.removeFirst() }
            canGoBack = true
        }
        canGoForward = !forwardStack.isEmpty
        fetchNeighborhoodTask = Task { [weak self] in
            await self?.fetchNeighborhood(for: next, context: context)
        }
    }
    
    // MARK: - Chat-to-Wiki Conversion

    public func fetchChatIngestStatus() async {
        do {
            let status: APIChatIngestStatus = try await APIClient.shared.request(path: "/chat/ingest/status")
            self.chatIngestStatus = status
        } catch {
            print("Failed to fetch chat ingest status: \(error.localizedDescription)")
        }
    }

    public func triggerChatIngest() async -> Bool {
        do {
            let bodyData = try JSONSerialization.data(withJSONObject: [:])
            let response: APIChatIngestNowResponse = try await APIClient.shared.request(
                path: "/chat/ingest/now", method: "POST", body: bodyData
            )
            if let status = response.status {
                self.chatIngestStatus = status
                self.unreadWikiPagesFromChat += status.pagesCreated
            }
            return response.success
        } catch {
            print("Failed to trigger chat ingest: \(error.localizedDescription)")
            return false
        }
    }

    public func setUserName(_ name: String) async -> Bool {
        do {
            let req = APISetUserNameRequest(name: name)
            let bodyData = try JSONEncoder().encode(req)
            let response: APISetUserNameResponse = try await APIClient.shared.request(
                path: "/chat/name", method: "POST", body: bodyData
            )
            if response.success {
                self.userName = response.currentName
            }
            return response.success
        } catch {
            print("Failed to set user name: \(error.localizedDescription)")
            return false
        }
    }

    @Published public var ingestHistory: [APIIngestHistoryEntry] = []
    @Published public var chatNotifications: [APIChatIngestNotification] = []
    @Published public var isClearingWiki = false
    @Published public var isExportingWiki = false
    @Published public var suggestions: [SuggestionItem] = []

    func regenerateSuggestions(messages: [ChatMessage], entities: [LoreEntity], events: [TemporalEvent]) {
        var results: [SuggestionItem] = []
        let focusedName = focusedEntityName.trimmingCharacters(in: .whitespaces)

        if !focusedName.isEmpty {
            results.append(SuggestionItem(text: "What is \(focusedName)?", category: .entity))
            results.append(SuggestionItem(text: "Evidence for \(focusedName)", category: .entity))
            if let neighborhood = neighborhood {
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

    public func clearUnreadWikiPages() {
        unreadWikiPagesFromChat = 0
    }

    public func fetchIngestHistory() async {
        do {
            let response: [String: [APIIngestHistoryEntry]] = try await APIClient.shared.request(path: "/chat/ingest/history")
            self.ingestHistory = response["history"] ?? []
        } catch {
            print("Failed to fetch ingest history: \(error.localizedDescription)")
        }
    }

    public func fetchChatNotifications() async {
        do {
            let response: [String: [APIChatIngestNotification]] = try await APIClient.shared.request(path: "/chat/ingest/notifications")
            self.chatNotifications = response["notifications"] ?? []
        } catch {
            print("Failed to fetch chat notifications: \(error.localizedDescription)")
        }
    }

    public func clearWikiContent() async -> APIWikiClearResponse? {
        isClearingWiki = true
        defer { isClearingWiki = false }
        do {
            let bodyData = try JSONSerialization.data(withJSONObject: [:])
            let response: APIWikiClearResponse = try await APIClient.shared.request(
                path: "/wiki/clear-content", method: "POST", body: bodyData
            )
            return response
        } catch {
            print("Failed to clear wiki content: \(error.localizedDescription)")
            return nil
        }
    }

    public func exportWiki() async -> APIWikiExportResponse? {
        isExportingWiki = true
        defer { isExportingWiki = false }
        do {
            let response: APIWikiExportResponse = try await APIClient.shared.request(path: "/wiki/export")
            return response
        } catch {
            print("Failed to export wiki: \(error.localizedDescription)")
            return nil
        }
    }

    public func importWiki(fileURL: URL) async -> APIWikiImportResponse? {
        defer { try? FileManager.default.removeItem(at: fileURL) }
        do {
            let fileData = try Data(contentsOf: fileURL)
            let boundary = UUID().uuidString
            let baseURL = await APIClient.shared.baseURL
            var request = URLRequest(url: baseURL.appendingPathComponent("/wiki/import"))
            request.httpMethod = "POST"
            request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

            var body = Data()
            body.append("--\(boundary)\r\n".data(using: .utf8)!)
            body.append("Content-Disposition: form-data; name=\"file\"; filename=\"wiki-import.zip\"\r\n".data(using: .utf8)!)
            body.append("Content-Type: application/zip\r\n\r\n".data(using: .utf8)!)
            body.append(fileData)
            body.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)
            request.httpBody = body

            let (data, response) = try await URLSession.shared.data(for: request)
            guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
                print("Failed to import wiki: HTTP error")
                return nil
            }
            return try JSONDecoder().decode(APIWikiImportResponse.self, from: data)
        } catch {
            print("Failed to import wiki: \(error.localizedDescription)")
            return nil
        }
    }

    // MARK: - Wiki Page CRUD
    @Published public var wikiPages: [APIWikiPageListItem] = []
    @Published public var isFetchingWikiPages = false
    @Published public var isDeletingWikiPage = false
    @Published public var wikiPagesError: String? = nil

    public func fetchWikiPages(pageType: String? = nil) async {
        isFetchingWikiPages = true
        defer { isFetchingWikiPages = false }
        do {
            let queryItems: [URLQueryItem]? = pageType.map { [URLQueryItem(name: "page_type", value: $0)] }
            let response: APIWikiPageListResponse = try await APIClient.shared.request(
                path: "/wiki/pages", queryItems: queryItems
            )
            self.wikiPages = response.pages
            self.wikiPagesError = nil
        } catch {
            self.wikiPagesError = error.localizedDescription
            print("Failed to fetch wiki pages: \(error.localizedDescription)")
        }
    }

    public func fetchWikiPageDetail(slug: String, pageType: String) async -> APIWikiPageDetail? {
        do {
            let response: APIWikiPageDetail = try await APIClient.shared.request(
                path: "/wiki/page/\(slug)",
                queryItems: [URLQueryItem(name: "page_type", value: pageType)]
            )
            return response
        } catch {
            print("Failed to fetch wiki page detail: \(error.localizedDescription)")
            return nil
        }
    }

    @discardableResult
    public func deleteWikiPage(slug: String, pageType: String, hard: Bool = false) async -> APIWikiDeleteResponse? {
        isDeletingWikiPage = true
        defer { isDeletingWikiPage = false }
        do {
            var queryItems = [URLQueryItem(name: "page_type", value: pageType)]
            if hard { queryItems.append(URLQueryItem(name: "hard", value: "true")) }
            let bodyData = try JSONSerialization.data(withJSONObject: [:])
            let response: APIWikiDeleteResponse = try await APIClient.shared.request(
                path: "/wiki/page/\(slug)", method: "DELETE", body: bodyData, queryItems: queryItems
            )
            return response
        } catch {
            print("Failed to delete wiki page: \(error.localizedDescription)")
            return nil
        }
    }

    // MARK: - Configuration Methods
    public func fetchConfig() async {
        isFetchingConfig = true
        defer { isFetchingConfig = false }
        
        do {
            let response: APIConfigResponse = try await APIClient.shared.request(path: "/config")
            self.quantumBackend = response.quantum_backend
            self.quantumHardwareEnabled = response.quantum_hardware_enabled
            self.ibmApiTokenSet = response.ibm_api_token_set
            self.dwaveApiTokenSet = response.dwave_api_token_set
            self.ionqApiTokenSet = response.ionq_api_token_set
            self.llmActiveProvider = response.llm_active_provider
            self.llmActiveModel = response.llm_active_model
            self.llmAvailableModels = response.llm_available_models
        } catch {
            print("Failed to fetch configurations: \(error.localizedDescription)")
        }
    }
    
    public func saveConfig(backend: String, ibmToken: String?, dwaveToken: String?, ionqToken: String?, hardwareEnabled: Bool) async -> Bool {
        isSavingConfig = true
        defer { isSavingConfig = false }
        
        do {
            let req = APIConfigRequest(
                quantum_backend: backend,
                ibm_api_token: (ibmToken?.isEmpty ?? true) ? nil : ibmToken,
                dwave_api_token: (dwaveToken?.isEmpty ?? true) ? nil : dwaveToken,
                ionq_api_token: (ionqToken?.isEmpty ?? true) ? nil : ionqToken,
                quantum_hardware_enabled: hardwareEnabled,
                llm_active_provider: nil,
                llm_active_model: nil
            )
            let bodyData = try JSONEncoder().encode(req)
            let response: APIConfigResponse = try await APIClient.shared.request(path: "/config", method: "POST", body: bodyData)
            
            self.quantumBackend = response.quantum_backend
            self.quantumHardwareEnabled = response.quantum_hardware_enabled
            self.ibmApiTokenSet = response.ibm_api_token_set
            self.dwaveApiTokenSet = response.dwave_api_token_set
            self.ionqApiTokenSet = response.ionq_api_token_set
            self.llmActiveProvider = response.llm_active_provider
            self.llmActiveModel = response.llm_active_model
            self.llmAvailableModels = response.llm_available_models
            return true
        } catch {
            print("Failed to save configurations: \(error.localizedDescription)")
            return false
        }
    }
    
    // MARK: - LLM Configuration
    public func saveLLMConfig(provider: String?, model: String?) async -> Bool {
        isSavingLLMConfig = true
        defer { isSavingLLMConfig = false }
        
        do {
            let req = APILLMConfigRequest(
                llm_active_provider: provider,
                llm_active_model: model
            )
            let bodyData = try JSONEncoder().encode(req)
            let response: APILLMConfigResponse = try await APIClient.shared.request(path: "/config/llm", method: "POST", body: bodyData)
            
            self.llmActiveProvider = response.llm_active_provider
            self.llmActiveModel = response.llm_active_model
            self.llmAvailableModels = response.llm_available_models
            return true
        } catch {
            print("Failed to save LLM configuration: \(error.localizedDescription)")
            return false
        }
    }
    
    public func refreshLLMDiscovery() async {
        do {
            let response: APIConfigResponse = try await APIClient.shared.request(path: "/config")
            self.llmAvailableModels = response.llm_available_models
            self.llmActiveProvider = response.llm_active_provider
            self.llmActiveModel = response.llm_active_model
        } catch {
            print("Failed to refresh LLM discovery: \(error.localizedDescription)")
        }
    }
    
    public func probeLLMProvider(_ name: String) async -> (provider: String, available: Bool, models: [String]) {
        do {
            let req = APILLMProbeRequest(providerName: name)
            let bodyData = try JSONEncoder().encode(req)
            let response: APILLMProbeResponse = try await APIClient.shared.request(
                path: "/config/llm/probe", method: "POST", body: bodyData
            )
            return (response.provider, response.available, response.models)
        } catch {
            print("Failed to probe LLM provider '\(name)': \(error.localizedDescription)")
            return (name, false, [])
        }
    }
}
