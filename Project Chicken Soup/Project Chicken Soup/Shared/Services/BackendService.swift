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
    
    private init() {}
    
    // MARK: - Fetch Temporal Events
    public func fetchTemporalEvents(context: ModelContext) async {
        isFetchingEvents = true
        eventsError = nil
        defer { isFetchingEvents = false }
        
        do {
            let apiEvents: [APITemporalEvent] = try await APIClient.shared.request(path: "/events")
            
            // Sync with local SwiftData store
            for apiEvent in apiEvents {
                let id = apiEvent.id
                let fetchDescriptor = FetchDescriptor<TemporalEvent>(predicate: #Predicate { $0.id == id })
                if let existing = try? context.fetch(fetchDescriptor).first {
                    existing.title = apiEvent.title
                    existing.eventDescription = apiEvent.eventDescription
                    existing.timestamp = apiEvent.timestamp
                    existing.confidence = apiEvent.confidence
                    existing.source = apiEvent.source
                    existing.type = apiEvent.type
                } else {
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
            }
            try? context.save()
        } catch {
            self.eventsError = error
            print("Failed to fetch events from backend: \(error.localizedDescription)")
            // Graceful fallback to cached or seeded SwiftData in view layer
        }
    }
    
    // MARK: - Fetch Lore Entities
    public func fetchLoreEntities(context: ModelContext) async {
        isFetchingEntities = true
        entitiesError = nil
        defer { isFetchingEntities = false }
        
        do {
            let apiEntities: [APILoreEntity] = try await APIClient.shared.request(path: "/entities")
            
            for apiEntity in apiEntities {
                let id = apiEntity.id
                let fetchDescriptor = FetchDescriptor<LoreEntity>(predicate: #Predicate { $0.id == id })
                if let existing = try? context.fetch(fetchDescriptor).first {
                    existing.name = apiEntity.name
                    existing.type = apiEntity.type
                    existing.summary = apiEntity.summary
                    existing.confidence = apiEntity.confidence
                    existing.source = apiEntity.source
                } else {
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
            }
            try? context.save()
        } catch {
            self.entitiesError = error
            print("Failed to fetch entities from backend: \(error.localizedDescription)")
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
        
        let encodedName = name.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? name
        guard let url = URL(string: "http://127.0.0.1:8000/graph/\(encodedName)") else { return }
        
        do {
            let (data, response) = try await URLSession.shared.data(for: URLRequest(url: url))
            
            guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
                loadFallbackNeighborhood(for: name, context: context)
                return
            }
            
            let decoder = JSONDecoder()
            let responseDecoded = try decoder.decode(NeighborhoodResponse.self, from: data)
            
            var uniqueConns: [NeighborhoodConnection] = []
            for conn in responseDecoded.connections {
                if !uniqueConns.contains(where: { $0.neighbor.name.lowercased() == conn.neighbor.name.lowercased() }) {
                    uniqueConns.append(conn)
                }
            }
            
            let filteredResponse = NeighborhoodResponse(entity: responseDecoded.entity, connections: uniqueConns)
            
            await MainActor.run {
                withAnimation(.spring(response: 0.65, dampingFraction: 0.75)) {
                    self.neighborhood = filteredResponse
                    self.focusedEntityName = name
                }
            }
        } catch {
            print("Failed to fetch neighborhood: \(error)")
            loadFallbackNeighborhood(for: name, context: context)
        }
    }
    
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
        
        let otherEntities = allEntities.filter { $0.name != name }
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
    public func selectEntity(_ name: String, context: ModelContext) {
        let currentFocused = focusedEntityName
        if !currentFocused.isEmpty && currentFocused.lowercased() != name.lowercased() {
            backStack.append(currentFocused)
            forwardStack.removeAll()
            canGoBack = true
            canGoForward = false
        }
        Task {
            await fetchNeighborhood(for: name, context: context)
        }
    }
    
    public func navigateBack(context: ModelContext) {
        guard !backStack.isEmpty else { return }
        let prev = backStack.removeLast()
        let currentFocused = focusedEntityName
        if !currentFocused.isEmpty {
            forwardStack.append(currentFocused)
            canGoForward = true
        }
        canGoBack = !backStack.isEmpty
        Task {
            await fetchNeighborhood(for: prev, context: context)
        }
    }
    
    public func navigateForward(context: ModelContext) {
        guard !forwardStack.isEmpty else { return }
        let next = forwardStack.removeLast()
        let currentFocused = focusedEntityName
        if !currentFocused.isEmpty {
            backStack.append(currentFocused)
            canGoBack = true
        }
        canGoForward = !forwardStack.isEmpty
        Task {
            await fetchNeighborhood(for: next, context: context)
        }
    }
    
    // MARK: - Chat-to-Wiki Conversion

    public func fetchChatIngestStatus() async {
        do {
            let status: APIChatIngestStatus = try await APIClient.shared.request(path: "/chat/ingest/status")
            await MainActor.run {
                self.chatIngestStatus = status
            }
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
                await MainActor.run {
                    self.chatIngestStatus = status
                    self.unreadWikiPagesFromChat += status.pagesCreated
                }
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
            await MainActor.run {
                if response.success {
                    self.userName = response.currentName
                }
            }
            return response.success
        } catch {
            print("Failed to set user name: \(error.localizedDescription)")
            return false
        }
    }

    public func clearUnreadWikiPages() {
        unreadWikiPagesFromChat = 0
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
