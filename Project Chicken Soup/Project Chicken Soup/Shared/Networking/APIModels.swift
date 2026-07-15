//
//  APIModels.swift
//  Project Chicken Soup
//
//  Created by mck on 6/23/26.
//

import Foundation

public struct APITemporalEvent: Codable, Identifiable {
    public var id: UUID
    public var title: String
    public var eventDescription: String
    public var timestamp: Date
    public var confidence: Double
    public var source: String
    public var type: String // "crash", "testimony", "anomaly", "theory"
    public var userNotes: String?
    public var sources: [String]?
    
    enum CodingKeys: String, CodingKey {
        case id
        case title
        case eventDescription = "description"
        case timestamp
        case confidence
        case source
        case type
        case userNotes
        case sources
    }
    
    public init(id: UUID = UUID(), title: String, eventDescription: String, timestamp: Date, confidence: Double, source: String, type: String, userNotes: String? = nil, sources: [String]? = nil) {
        self.id = id
        self.title = title
        self.eventDescription = eventDescription
        self.timestamp = timestamp
        self.confidence = confidence
        self.source = source
        self.type = type
        self.userNotes = userNotes
        self.sources = sources
    }
}

public struct APILoreEntity: Codable, Identifiable {
    public var id: UUID
    public var name: String
    public var type: String
    public var summary: String
    public var confidence: Double
    public var source: String
    public var userNotes: String?
    public var sources: [String]?
    
    enum CodingKeys: String, CodingKey {
        case id, name, type, summary, confidence, source, sources
        case userNotes = "user_notes"
    }
    
    public init(id: UUID = UUID(), name: String, type: String, summary: String, confidence: Double, source: String, userNotes: String? = nil, sources: [String]? = nil) {
        self.id = id
        self.name = name
        self.type = type
        self.summary = summary
        self.confidence = confidence
        self.source = source
        self.userNotes = userNotes
        self.sources = sources
    }
}

public struct APITimeTravelSimulationResponse: Codable {
    public var success: Bool
    public var logs: [String]
    public var gravityMetric: Double
    public var velocityMetric: Double
    public var fieldIntensity: Double
    public var resolvedPathConfidence: Double
    public var warpFactor: Double?
    public var targetYear: Int?

    enum CodingKeys: String, CodingKey {
        case success, logs
        case gravityMetric = "gravity_metric"
        case velocityMetric = "velocity_metric"
        case fieldIntensity = "field_intensity"
        case resolvedPathConfidence = "resolved_path_confidence"
        case warpFactor = "warp_factor"
        case targetYear = "target_year"
    }

    public init(success: Bool, logs: [String], gravityMetric: Double, velocityMetric: Double, fieldIntensity: Double, resolvedPathConfidence: Double, warpFactor: Double? = nil, targetYear: Int? = nil) {
        self.success = success
        self.logs = logs
        self.gravityMetric = gravityMetric
        self.velocityMetric = velocityMetric
        self.fieldIntensity = fieldIntensity
        self.resolvedPathConfidence = resolvedPathConfidence
        self.warpFactor = warpFactor
        self.targetYear = targetYear
    }
}

public struct APIQueryResponse: Codable {
    public var responseText: String
    public var inferredEvents: [APITemporalEvent]
    public var inferredEntities: [APILoreEntity]
    public var conversationId: String?
    public var taskId: String?
    public var threadId: String?
    public var status: String?

    enum CodingKeys: String, CodingKey {
        case responseText = "answer"
        case inferredEvents = "inferred_events"
        case inferredEntities = "inferred_entities"
        case conversationId = "conversation_id"
        case taskId = "task_id"
        case threadId = "thread_id"
        case status
    }

    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        self.responseText = try container.decode(String.self, forKey: .responseText)
        self.inferredEvents = try container.decodeIfPresent([APITemporalEvent].self, forKey: .inferredEvents) ?? []
        self.inferredEntities = try container.decodeIfPresent([APILoreEntity].self, forKey: .inferredEntities) ?? []
        self.conversationId = try container.decodeIfPresent(String.self, forKey: .conversationId)
        self.taskId = try container.decodeIfPresent(String.self, forKey: .taskId)
        self.threadId = try container.decodeIfPresent(String.self, forKey: .threadId)
        self.status = try container.decodeIfPresent(String.self, forKey: .status)
    }

    public init(responseText: String, inferredEvents: [APITemporalEvent] = [], inferredEntities: [APILoreEntity] = [], conversationId: String? = nil, taskId: String? = nil, threadId: String? = nil, status: String? = nil) {
        self.responseText = responseText
        self.inferredEvents = inferredEvents
        self.inferredEntities = inferredEntities
        self.conversationId = conversationId
        self.taskId = taskId
        self.threadId = threadId
        self.status = status
    }
}

public struct APIDiscoveryStatus: Codable {
    public var modelName: String
    public var isAvailable: Bool
    public var isCurrent: Bool
    public var latencyMs: Double

    enum CodingKeys: String, CodingKey {
        case modelName = "model_name"
        case isAvailable = "is_available"
        case isCurrent = "is_current"
        case latencyMs = "latency_ms"
    }

    public init(modelName: String, isAvailable: Bool, isCurrent: Bool, latencyMs: Double) {
        self.modelName = modelName
        self.isAvailable = isAvailable
        self.isCurrent = isCurrent
        self.latencyMs = latencyMs
    }
}

public struct NeighborhoodEntity: Codable, Identifiable, Hashable {
    public var id: String
    public var name: String
    public var type: String
    public var summary: String
    public var confidence: Double
    public var source: String
    public var sources: [String]

    enum CodingKeys: String, CodingKey {
        case id, name, type, summary, confidence, source, sources
    }

    public func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }

    public static func == (lhs: NeighborhoodEntity, rhs: NeighborhoodEntity) -> Bool {
        lhs.id == rhs.id
    }

    public init(id: String? = nil, name: String, type: String, summary: String, confidence: Double, source: String, sources: [String]) {
        self.id = id ?? name.lowercased()
        self.name = name
        self.type = type
        self.summary = summary
        self.confidence = confidence
        self.source = source
        self.sources = sources
    }
}

public struct NeighborhoodConnection: Codable, Identifiable {
    public var id: String { neighbor.id }
    public var relationshipType: String
    public var neighbor: NeighborhoodEntity
    
    enum CodingKeys: String, CodingKey {
        case relationshipType = "relationship_type"
        case neighbor
    }
    
    public init(relationshipType: String, neighbor: NeighborhoodEntity) {
        self.relationshipType = relationshipType
        self.neighbor = neighbor
    }
}

public struct NeighborhoodResponse: Codable {
    public var entity: NeighborhoodEntity
    public var connections: [NeighborhoodConnection]

    enum CodingKeys: String, CodingKey {
        case entity, connections
    }

    public init(entity: NeighborhoodEntity, connections: [NeighborhoodConnection]) {
        self.entity = entity
        self.connections = connections
    }
}

public struct APIConfigRequest: Codable {
    public var quantumBackend: String
    public var ibmApiToken: String?
    public var dwaveApiToken: String?
    public var ionqApiToken: String?
    public var quantumHardwareEnabled: Bool
    public var llmActiveProvider: String?
    public var llmActiveModel: String?

    enum CodingKeys: String, CodingKey {
        case quantumBackend = "quantum_backend"
        case ibmApiToken = "ibm_api_token"
        case dwaveApiToken = "dwave_api_token"
        case ionqApiToken = "ionq_api_token"
        case quantumHardwareEnabled = "quantum_hardware_enabled"
        case llmActiveProvider = "llm_active_provider"
        case llmActiveModel = "llm_active_model"
    }

    public init(quantumBackend: String, ibmApiToken: String? = nil, dwaveApiToken: String? = nil, ionqApiToken: String? = nil, quantumHardwareEnabled: Bool, llmActiveProvider: String? = nil, llmActiveModel: String? = nil) {
        self.quantumBackend = quantumBackend
        self.ibmApiToken = ibmApiToken
        self.dwaveApiToken = dwaveApiToken
        self.ionqApiToken = ionqApiToken
        self.quantumHardwareEnabled = quantumHardwareEnabled
        self.llmActiveProvider = llmActiveProvider
        self.llmActiveModel = llmActiveModel
    }
}

public struct APILLMProviderStatus: Codable {
    public var available: Bool
    public var models: [String]

    enum CodingKeys: String, CodingKey {
        case available, models
    }
}

public struct APIConfigResponse: Codable {
    public var success: Bool
    public var quantumBackend: String
    public var quantumHardwareEnabled: Bool
    public var ibmApiTokenSet: Bool
    public var dwaveApiTokenSet: Bool
    public var ionqApiTokenSet: Bool
    public var llmActiveProvider: String
    public var llmActiveModel: String
    public var llmAvailableModels: [String]
    public var llmProviders: [String: APILLMProviderStatus]
    public var last30daysEnabled: Bool

    enum CodingKeys: String, CodingKey {
        case success
        case quantumBackend = "quantum_backend"
        case quantumHardwareEnabled = "quantum_hardware_enabled"
        case ibmApiTokenSet = "ibm_api_token_set"
        case dwaveApiTokenSet = "dwave_api_token_set"
        case ionqApiTokenSet = "ionq_api_token_set"
        case llmActiveProvider = "llm_active_provider"
        case llmActiveModel = "llm_active_model"
        case llmAvailableModels = "llm_available_models"
        case llmProviders = "llm_providers"
        case last30daysEnabled = "last30days_enabled"
    }

    public init(success: Bool, quantumBackend: String, quantumHardwareEnabled: Bool, ibmApiTokenSet: Bool, dwaveApiTokenSet: Bool, ionqApiTokenSet: Bool, llmActiveProvider: String, llmActiveModel: String, llmAvailableModels: [String], llmProviders: [String: APILLMProviderStatus], last30daysEnabled: Bool = false) {
        self.success = success
        self.quantumBackend = quantumBackend
        self.quantumHardwareEnabled = quantumHardwareEnabled
        self.ibmApiTokenSet = ibmApiTokenSet
        self.dwaveApiTokenSet = dwaveApiTokenSet
        self.ionqApiTokenSet = ionqApiTokenSet
        self.llmActiveProvider = llmActiveProvider
        self.llmActiveModel = llmActiveModel
        self.llmAvailableModels = llmAvailableModels
        self.llmProviders = llmProviders
        self.last30daysEnabled = last30daysEnabled
    }
}

public struct APILLMConfigRequest: Codable {
    public var llmActiveProvider: String?
    public var llmActiveModel: String?

    enum CodingKeys: String, CodingKey {
        case llmActiveProvider = "llm_active_provider"
        case llmActiveModel = "llm_active_model"
    }

    public init(llmActiveProvider: String? = nil, llmActiveModel: String? = nil) {
        self.llmActiveProvider = llmActiveProvider
        self.llmActiveModel = llmActiveModel
    }
}

public struct APILLMConfigResponse: Codable {
    public var success: Bool
    public var llmActiveProvider: String
    public var llmActiveModel: String
    public var llmAvailableModels: [String]
    public var llmProviders: [String: APILLMProviderStatus]

    enum CodingKeys: String, CodingKey {
        case success
        case llmActiveProvider = "llm_active_provider"
        case llmActiveModel = "llm_active_model"
        case llmAvailableModels = "llm_available_models"
        case llmProviders = "llm_providers"
    }
}

public struct APILLMProbeRequest: Codable {
    public var providerName: String

    enum CodingKeys: String, CodingKey {
        case providerName = "provider_name"
    }

    public init(providerName: String) {
        self.providerName = providerName
    }
}

public struct APILLMProbeResponse: Codable {
    public var provider: String
    public var available: Bool
    public var models: [String]

    enum CodingKeys: String, CodingKey {
        case provider, available, models
    }
}

// MARK: - Ingest Analysis Models

public struct APIAnalyzedPage: Codable, Identifiable {
    public var id: String { title }
    public var title: String
    public var pageType: String
    public var tags: [String]
    public var sources: [String]
    public var summary: String
    public var body: String
    public var related: [String]
    public var confidence: Double

    enum CodingKeys: String, CodingKey {
        case title
        case pageType = "page_type"
        case tags
        case sources
        case summary
        case body
        case related
        case confidence
    }

    public init(title: String, pageType: String, tags: [String], sources: [String], summary: String, body: String, related: [String], confidence: Double) {
        self.title = title
        self.pageType = pageType
        self.tags = tags
        self.sources = sources
        self.summary = summary
        self.body = body
        self.related = related
        self.confidence = confidence
    }
}

public struct APIAnalyzeResponse: Codable {
    public var success: Bool
    public var suggestedPages: [APIAnalyzedPage]
    public var confidence: Double
    public var rawTextPreview: String

    enum CodingKeys: String, CodingKey {
        case success
        case suggestedPages = "suggested_pages"
        case confidence
        case rawTextPreview = "raw_text_preview"
    }

    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        self.success = try container.decode(Bool.self, forKey: .success)
        self.suggestedPages = try container.decodeIfPresent([APIAnalyzedPage].self, forKey: .suggestedPages) ?? []
        self.confidence = try container.decode(Double.self, forKey: .confidence)
        self.rawTextPreview = try container.decodeIfPresent(String.self, forKey: .rawTextPreview) ?? ""
    }

    public init(success: Bool, suggestedPages: [APIAnalyzedPage], confidence: Double, rawTextPreview: String) {
        self.success = success
        self.suggestedPages = suggestedPages
        self.confidence = confidence
        self.rawTextPreview = rawTextPreview
    }
}

public struct APIFileIngestResponse: Codable {
    public var success: Bool
    public var pagesCreated: [String]
    public var pagesUpdated: [String]
    public var totalPages: Int
    public var nodesCreated: Int
    public var relationshipsCreated: Int

    enum CodingKeys: String, CodingKey {
        case success
        case pagesCreated = "pages_created"
        case pagesUpdated = "pages_updated"
        case totalPages = "total_pages"
        case nodesCreated = "nodes_created"
        case relationshipsCreated = "relationships_created"
    }

    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        self.success = try container.decode(Bool.self, forKey: .success)
        self.pagesCreated = try container.decodeIfPresent([String].self, forKey: .pagesCreated) ?? []
        self.pagesUpdated = try container.decodeIfPresent([String].self, forKey: .pagesUpdated) ?? []
        self.totalPages = try container.decodeIfPresent(Int.self, forKey: .totalPages) ?? 0
        self.nodesCreated = try container.decodeIfPresent(Int.self, forKey: .nodesCreated) ?? 0
        self.relationshipsCreated = try container.decodeIfPresent(Int.self, forKey: .relationshipsCreated) ?? 0
    }

    public init(success: Bool, pagesCreated: [String], pagesUpdated: [String], totalPages: Int, nodesCreated: Int, relationshipsCreated: Int) {
        self.success = success
        self.pagesCreated = pagesCreated
        self.pagesUpdated = pagesUpdated
        self.totalPages = totalPages
        self.nodesCreated = nodesCreated
        self.relationshipsCreated = relationshipsCreated
    }
}

// MARK: - Chat-to-Wiki Models

public struct APIChatIngestStatus: Codable {
    public var enabled: Bool
    public var lastRun: String?
    public var conversationsChecked: Int
    public var conversationsIngested: Int
    public var pagesCreated: Int
    public var pagesUpdated: Int

    enum CodingKeys: String, CodingKey {
        case enabled
        case lastRun = "last_run"
        case conversationsChecked = "conversations_checked"
        case conversationsIngested = "conversations_ingested"
        case pagesCreated = "pages_created"
        case pagesUpdated = "pages_updated"
    }

    public init(enabled: Bool, lastRun: String? = nil, conversationsChecked: Int = 0, conversationsIngested: Int = 0, pagesCreated: Int = 0, pagesUpdated: Int = 0) {
        self.enabled = enabled
        self.lastRun = lastRun
        self.conversationsChecked = conversationsChecked
        self.conversationsIngested = conversationsIngested
        self.pagesCreated = pagesCreated
        self.pagesUpdated = pagesUpdated
    }
}

public struct APIChatIngestNowResponse: Codable {
    public var success: Bool
    public var status: APIChatIngestStatus?

    enum CodingKeys: String, CodingKey {
        case success, status
    }

    public init(success: Bool, status: APIChatIngestStatus? = nil) {
        self.success = success
        self.status = status
    }
}

public struct APISetUserNameRequest: Codable {
    public var name: String

    enum CodingKeys: String, CodingKey {
        case name
    }

    public init(name: String) {
        self.name = name
    }
}

public struct APISetUserNameResponse: Codable {
    public var success: Bool
    public var previousName: String
    public var currentName: String
    public var slug: String

    enum CodingKeys: String, CodingKey {
        case success
        case previousName = "previous_name"
        case currentName = "current_name"
        case slug
    }

    public init(success: Bool, previousName: String, currentName: String, slug: String) {
        self.success = success
        self.previousName = previousName
        self.currentName = currentName
        self.slug = slug
    }
}

// MARK: - Phase 5: Granular Notifications & History

public struct APIIngestHistoryEntry: Codable, Identifiable {
    public var id: String { "\(date)-\(description)" }
    public var date: String
    public var type: String
    public var description: String

    enum CodingKeys: String, CodingKey {
        case date, type, description
    }

    public init(date: String, type: String, description: String) {
        self.date = date
        self.type = type
        self.description = description
    }
}

public struct APIChatIngestNotification: Codable, Identifiable {
    public var id: String { "\(date)-\(description)" }
    public var date: String
    public var type: String
    public var description: String
    public var pagesCreated: Int

    enum CodingKeys: String, CodingKey {
        case date
        case type
        case description
        case pagesCreated = "pages_created"
    }

    public init(date: String, type: String, description: String, pagesCreated: Int) {
        self.date = date
        self.type = type
        self.description = description
        self.pagesCreated = pagesCreated
    }
}

// MARK: - Wiki Clear Content

public struct APIWikiClearResponse: Codable {
    public var success: Bool
    public var preservedCount: Int
    public var deletedCount: Int
    public var protectedAddedCount: Int
    public var preservedSlugs: [String]
    public var deletedSlugs: [String]

    enum CodingKeys: String, CodingKey {
        case success
        case preservedCount = "preserved_count"
        case deletedCount = "deleted_count"
        case protectedAddedCount = "protected_added_count"
        case preservedSlugs = "preserved_slugs"
        case deletedSlugs = "deleted_slugs"
    }

    public init(success: Bool, preservedCount: Int, deletedCount: Int, protectedAddedCount: Int, preservedSlugs: [String], deletedSlugs: [String]) {
        self.success = success
        self.preservedCount = preservedCount
        self.deletedCount = deletedCount
        self.protectedAddedCount = protectedAddedCount
        self.preservedSlugs = preservedSlugs
        self.deletedSlugs = deletedSlugs
    }
}

// MARK: - Wiki Backup/Restore

public struct APIWikiExportResponse: Codable {
    public var success: Bool
    public var filepath: String
    public var sizeKb: Double
    public var pageCount: Int

    enum CodingKeys: String, CodingKey {
        case success
        case filepath
        case sizeKb = "size_kb"
        case pageCount = "page_count"
    }

    public init(success: Bool, filepath: String, sizeKb: Double, pageCount: Int) {
        self.success = success
        self.filepath = filepath
        self.sizeKb = sizeKb
        self.pageCount = pageCount
    }
}

public struct APIWikiImportResponse: Codable {
    public var success: Bool
    public var restoredCount: Int

    enum CodingKeys: String, CodingKey {
        case success
        case restoredCount = "restored_count"
    }

    public init(success: Bool, restoredCount: Int) {
        self.success = success
        self.restoredCount = restoredCount
    }
}

public struct APIFolderIngestResponse: Codable {
    public var success: Bool
    public var totalFiles: Int
    public var totalPagesCreated: Int
    public var totalPagesUpdated: Int
    public var totalNodesCreated: Int
    public var totalRelationshipsCreated: Int
    public var fileResults: [APIFileIngestResponse]

    enum CodingKeys: String, CodingKey {
        case success
        case totalFiles = "total_files"
        case totalPagesCreated = "total_pages_created"
        case totalPagesUpdated = "total_pages_updated"
        case totalNodesCreated = "total_nodes_created"
        case totalRelationshipsCreated = "total_relationships_created"
        case fileResults = "file_results"
    }

    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        self.success = try container.decode(Bool.self, forKey: .success)
        self.totalFiles = try container.decodeIfPresent(Int.self, forKey: .totalFiles) ?? 0
        self.totalPagesCreated = try container.decodeIfPresent(Int.self, forKey: .totalPagesCreated) ?? 0
        self.totalPagesUpdated = try container.decodeIfPresent(Int.self, forKey: .totalPagesUpdated) ?? 0
        self.totalNodesCreated = try container.decodeIfPresent(Int.self, forKey: .totalNodesCreated) ?? 0
        self.totalRelationshipsCreated = try container.decodeIfPresent(Int.self, forKey: .totalRelationshipsCreated) ?? 0
        self.fileResults = try container.decodeIfPresent([APIFileIngestResponse].self, forKey: .fileResults) ?? []
    }

    public init(success: Bool, totalFiles: Int, totalPagesCreated: Int, totalPagesUpdated: Int, totalNodesCreated: Int = 0, totalRelationshipsCreated: Int = 0, fileResults: [APIFileIngestResponse] = []) {
        self.success = success
        self.totalFiles = totalFiles
        self.totalPagesCreated = totalPagesCreated
        self.totalPagesUpdated = totalPagesUpdated
        self.totalNodesCreated = totalNodesCreated
        self.totalRelationshipsCreated = totalRelationshipsCreated
        self.fileResults = fileResults
    }
}

// MARK: - Entity Delete

public struct APIEntityDeleteResponse: Codable {
    public var success: Bool
    public var deleted: Bool

    enum CodingKeys: String, CodingKey {
        case success, deleted
    }

    public init(success: Bool, deleted: Bool) {
        self.success = success
        self.deleted = deleted
    }
}

// MARK: - Wiki Page CRUD

public struct APIWikiPageListItem: Codable, Identifiable, Hashable {
    public var id: String { slug }
    public var slug: String
    public var title: String
    public var pageType: String
    public var tags: [String]
    public var created: String
    public var updated: String
    public var protected: Bool

    enum CodingKeys: String, CodingKey {
        case slug
        case title
        case pageType = "page_type"
        case tags
        case created
        case updated
        case protected
    }

    public init(slug: String, title: String, pageType: String, tags: [String], created: String, updated: String, protected: Bool) {
        self.slug = slug
        self.title = title
        self.pageType = pageType
        self.tags = tags
        self.created = created
        self.updated = updated
        self.protected = protected
    }
}

public struct APIWikiPageListResponse: Codable {
    public var success: Bool
    public var pages: [APIWikiPageListItem]
    public var total: Int

    enum CodingKeys: String, CodingKey {
        case success, pages, total
    }

    public init(success: Bool, pages: [APIWikiPageListItem], total: Int) {
        self.success = success
        self.pages = pages
        self.total = total
    }
}

public struct APIWikiPageDetail: Codable {
    public var success: Bool
    public var slug: String
    public var title: String
    public var pageType: String
    public var tags: [String]
    public var sources: [String]
    public var related: [String]
    public var body: String
    public var created: String
    public var updated: String
    public var protected: Bool

    enum CodingKeys: String, CodingKey {
        case success
        case slug
        case title
        case pageType = "page_type"
        case tags
        case sources
        case related
        case body
        case created
        case updated
        case protected
    }

    public init(success: Bool, slug: String, title: String, pageType: String, tags: [String], sources: [String], related: [String], body: String, created: String, updated: String, protected: Bool) {
        self.success = success
        self.slug = slug
        self.title = title
        self.pageType = pageType
        self.tags = tags
        self.sources = sources
        self.related = related
        self.body = body
        self.created = created
        self.updated = updated
        self.protected = protected
    }
}

public struct APIWikiDeleteResponse: Codable {
    public var success: Bool
    public var slug: String
    public var pageType: String
    public var title: String
    public var neo4jCleaned: Bool
    public var crossRefsCleaned: Int

    enum CodingKeys: String, CodingKey {
        case success
        case slug
        case pageType = "page_type"
        case title
        case neo4jCleaned = "neo4j_cleaned"
        case crossRefsCleaned = "cross_refs_cleaned"
    }

    public init(success: Bool, slug: String, pageType: String, title: String, neo4jCleaned: Bool, crossRefsCleaned: Int) {
        self.success = success
        self.slug = slug
        self.pageType = pageType
        self.title = title
        self.neo4jCleaned = neo4jCleaned
        self.crossRefsCleaned = crossRefsCleaned
    }
}

public struct APIBulkIngestResponse: Codable {
    public var success: Bool
    public var pagesIngested: Int
    public var nodesCreated: Int
    public var relationshipsCreated: Int

    enum CodingKeys: String, CodingKey {
        case success
        case pagesIngested = "pages_ingested"
        case nodesCreated = "nodes_created"
        case relationshipsCreated = "relationships_created"
    }

    public init(success: Bool, pagesIngested: Int, nodesCreated: Int, relationshipsCreated: Int) {
        self.success = success
        self.pagesIngested = pagesIngested
        self.nodesCreated = nodesCreated
        self.relationshipsCreated = relationshipsCreated
    }
}

// MARK: - AnyDecodableValue Utility

public enum AnyDecodableValue: Codable, Hashable {
    case string(String)
    case double(Double)
    case bool(Bool)
    case array([AnyDecodableValue])
    case dictionary([String: AnyDecodableValue])
    case null
    
    private struct DynamicCodingKeys: CodingKey {
        var stringValue: String
        init?(stringValue: String) {
            self.stringValue = stringValue
        }
        var intValue: Int?
        init?(intValue: Int) {
            return nil
        }
    }
    
    public init(from decoder: Decoder) throws {
        if let container = try? decoder.container(keyedBy: DynamicCodingKeys.self) {
            var dict = [String: AnyDecodableValue]()
            for key in container.allKeys {
                if let val = try? container.decode(AnyDecodableValue.self, forKey: key) {
                    dict[key.stringValue] = val
                }
            }
            self = .dictionary(dict)
        } else if var container = try? decoder.unkeyedContainer() {
            var array = [AnyDecodableValue]()
            while !container.isAtEnd {
                if let val = try? container.decode(AnyDecodableValue.self) {
                    array.append(val)
                }
            }
            self = .array(array)
        } else {
            let container = try decoder.singleValueContainer()
            if let str = try? container.decode(String.self) {
                self = .string(str)
            } else if let dbl = try? container.decode(Double.self) {
                self = .double(dbl)
            } else if let int = try? container.decode(Int.self) {
                self = .double(Double(int))
            } else if let bl = try? container.decode(Bool.self) {
                self = .bool(bl)
            } else {
                self = .null
            }
        }
    }
    
    public func encode(to encoder: Encoder) throws {
        switch self {
        case .string(let s):
            var container = encoder.singleValueContainer()
            try container.encode(s)
        case .double(let d):
            var container = encoder.singleValueContainer()
            try container.encode(d)
        case .bool(let b):
            var container = encoder.singleValueContainer()
            try container.encode(b)
        case .array(let arr):
            var container = encoder.unkeyedContainer()
            for item in arr {
                try container.encode(item)
            }
        case .dictionary(let dict):
            var container = encoder.container(keyedBy: DynamicCodingKeys.self)
            for (key, val) in dict {
                if let codingKey = DynamicCodingKeys(stringValue: key) {
                    try container.encode(val, forKey: codingKey)
                }
            }
        case .null:
            var container = encoder.singleValueContainer()
            try container.encodeNil()
        }
    }
    
    public var stringValue: String {
        switch self {
        case .string(let s): return s
        case .double(let d): return String(d)
        case .bool(let b): return String(b)
        case .array(let arr): return "[\(arr.map { $0.stringValue }.joined(separator: ", "))]"
        case .dictionary(let dict): return "{\(dict.map { "\($0): \($1.stringValue)" }.joined(separator: ", "))}"
        case .null: return "null"
        }
    }

    public var value: AnyHashable {
        switch self {
        case .string(let s): return s
        case .double(let d): return d
        case .bool(let b): return b
        case .array(let arr): return arr.map { $0.value }
        case .dictionary(let dict): return dict.mapValues { $0.value }
        case .null: return ""
        }
    }

    public var asArray: [AnyDecodableValue]? {
        if case .array(let arr) = self { return arr }
        return nil
    }
    
    public var asDictionary: [String: AnyDecodableValue]? {
        if case .dictionary(let dict) = self { return dict }
        return nil
    }
    
    public var asString: String? {
        if case .string(let s) = self { return s }
        return nil
    }

    public var asDouble: Double? {
        if case .double(let d) = self { return d }
        return nil
    }

    public var asInt: Int? {
        if case .double(let d) = self { return Int(d) }
        return nil
    }

    public var asBool: Bool? {
        if case .bool(let b) = self { return b }
        return nil
    }
}

// MARK: - Living Almanac Models

public struct APIClaimEvidence: Codable, Identifiable, Hashable {
    public var id: String { clusterId.isEmpty ? UUID().uuidString : clusterId }
    public var claimText: String
    public var sourcePlatform: String
    public var engagementCount: Int
    public var url: String
    public var timestamp: String
    public var clusterId: String
    public var polymarketOdds: Double?
    public var engagementDecayed: Double?
    public var provenanceChain: [String]

    enum CodingKeys: String, CodingKey {
        case claimText = "claim_text"
        case sourcePlatform = "source_platform"
        case engagementCount = "engagement_count"
        case url
        case timestamp
        case clusterId = "cluster_id"
        case polymarketOdds = "polymarket_odds"
        case engagementDecayed = "engagement_decayed"
        case provenanceChain = "provenance_chain"
    }

    public init(claimText: String, sourcePlatform: String, engagementCount: Int = 0, url: String = "", timestamp: String = "", clusterId: String = "", polymarketOdds: Double? = nil, engagementDecayed: Double? = nil, provenanceChain: [String] = []) {
        self.claimText = claimText
        self.sourcePlatform = sourcePlatform
        self.engagementCount = engagementCount
        self.url = url
        self.timestamp = timestamp
        self.clusterId = clusterId
        self.polymarketOdds = polymarketOdds
        self.engagementDecayed = engagementDecayed
        self.provenanceChain = provenanceChain
    }
}

public struct APIClaimConfidence: Codable, Hashable {
    public var epistemicConfidence: Double
    public var socialTraction: Double
    public var stateLabel: String
    public var collapsed: Bool
    public var evidenceCount: Int
    public var lastPulseAt: String?
    public var scoringVersion: String
    public var scoringInputs: [String: AnyDecodableValue]?
    public var claimText: String?

    enum CodingKeys: String, CodingKey {
        case epistemicConfidence = "epistemic_confidence"
        case socialTraction = "social_traction"
        case stateLabel = "state_label"
        case collapsed
        case evidenceCount = "evidence_count"
        case lastPulseAt = "last_pulse_at"
        case scoringVersion = "scoring_version"
        case scoringInputs = "scoring_inputs"
        case claimText = "claim_text"
    }

    public init(epistemicConfidence: Double, socialTraction: Double, stateLabel: String, collapsed: Bool = false, evidenceCount: Int = 0, lastPulseAt: String? = nil, scoringVersion: String = "v1-wavefunction", scoringInputs: [String: AnyDecodableValue]? = nil, claimText: String? = nil) {
        self.epistemicConfidence = epistemicConfidence
        self.socialTraction = socialTraction
        self.stateLabel = stateLabel
        self.collapsed = collapsed
        self.evidenceCount = evidenceCount
        self.lastPulseAt = lastPulseAt
        self.scoringVersion = scoringVersion
        self.scoringInputs = scoringInputs
        self.claimText = claimText
    }
}

public struct APIDrivingClaim: Codable, Identifiable, Hashable {
    public var id: String { claimText }
    public var claimText: String
    public var platform: String
    public var oldConfidence: Double?
    public var newConfidence: Double
    public var delta: Double

    enum CodingKeys: String, CodingKey {
        case claimText = "claim_text"
        case platform
        case oldConfidence = "old_confidence"
        case newConfidence = "new_confidence"
        case delta
    }

    public init(claimText: String, platform: String = "", oldConfidence: Double? = nil, newConfidence: Double, delta: Double = 0.0) {
        self.claimText = claimText
        self.platform = platform
        self.oldConfidence = oldConfidence
        self.newConfidence = newConfidence
        self.delta = delta
    }
}

public struct APIDivergenceResult: Codable, Hashable {
    public var entityName: String
    public var divergenceRisk: Double
    public var canonVectorHash: String
    public var liveVectorHash: String
    public var drivingClaims: [APIDrivingClaim]
    public var computedAt: String

    enum CodingKeys: String, CodingKey {
        case entityName = "entity_name"
        case divergenceRisk = "divergence_risk"
        case canonVectorHash = "canon_vector_hash"
        case liveVectorHash = "live_vector_hash"
        case drivingClaims = "driving_claims"
        case computedAt = "computed_at"
    }

    public init(entityName: String, divergenceRisk: Double, canonVectorHash: String = "", liveVectorHash: String = "", drivingClaims: [APIDrivingClaim] = [], computedAt: String = "") {
        self.entityName = entityName
        self.divergenceRisk = divergenceRisk
        self.canonVectorHash = canonVectorHash
        self.liveVectorHash = liveVectorHash
        self.drivingClaims = drivingClaims
        self.computedAt = computedAt
    }
}

public struct APIPulseResult: Codable, Hashable {
    public var entityName: String
    public var status: String // "success", "disabled", "budget_exceeded", "error", "no_data"
    public var evidence: [APIClaimEvidence]
    public var rawSnapshotPath: String?
    public var budgetRemaining: Double
    public var error: String?

    enum CodingKeys: String, CodingKey {
        case entityName = "entity_name"
        case status
        case evidence
        case rawSnapshotPath = "raw_snapshot_path"
        case budgetRemaining = "budget_remaining"
        case error
    }

    public init(entityName: String, status: String, evidence: [APIClaimEvidence] = [], rawSnapshotPath: String? = nil, budgetRemaining: Double = 0.0, error: String? = nil) {
        self.entityName = entityName
        self.status = status
        self.evidence = evidence
        self.rawSnapshotPath = rawSnapshotPath
        self.budgetRemaining = budgetRemaining
        self.error = error
    }
}

public struct APITimelinePoint: Codable, Identifiable, Hashable {
    public var id: String { date }
    public var date: String
    public var epistemicConfidence: Double
    public var socialTraction: Double
    public var divergenceRisk: Double
    public var activeClaims: [String]
    public var pulseFile: String?
    public var wikiCommit: String?

    enum CodingKeys: String, CodingKey {
        case date
        case epistemicConfidence = "epistemic_confidence"
        case socialTraction = "social_traction"
        case divergenceRisk = "divergence_risk"
        case activeClaims = "active_claims"
        case pulseFile = "pulse_file"
        case wikiCommit = "wiki_commit"
    }

    public init(date: String, epistemicConfidence: Double = 0.5, socialTraction: Double = 0.0, divergenceRisk: Double = 0.0, activeClaims: [String] = [], pulseFile: String? = nil, wikiCommit: String? = nil) {
        self.date = date
        self.epistemicConfidence = epistemicConfidence
        self.socialTraction = socialTraction
        self.divergenceRisk = divergenceRisk
        self.activeClaims = activeClaims
        self.pulseFile = pulseFile
        self.wikiCommit = wikiCommit
    }
}

public struct APITimelineResponse: Codable {
    public var entityName: String
    public var days: Int
    public var points: [APITimelinePoint]
    public var total: Int

    enum CodingKeys: String, CodingKey {
        case entityName = "entity_name"
        case days
        case points
        case total
    }
}

public struct APIPulseHistoryEntry: Codable, Identifiable, Hashable {
    public var id: String { file }
    public var entityName: String
    public var date: String
    public var timestamp: String
    public var evidenceCount: Int
    public var evidence: [APIClaimEvidence]
    public var file: String

    enum CodingKeys: String, CodingKey {
        case entityName = "entity_name"
        case date
        case timestamp
        case evidenceCount = "evidence_count"
        case evidence
        case file
    }

    public init(entityName: String, date: String, timestamp: String, evidenceCount: Int = 0, evidence: [APIClaimEvidence] = [], file: String) {
        self.entityName = entityName
        self.date = date
        self.timestamp = timestamp
        self.evidenceCount = evidenceCount
        self.evidence = evidence
        self.file = file
    }
}

public struct APIPulseHistoryResponse: Codable {
    public var pulses: [APIPulseHistoryEntry]
    public var total: Int
    public var uniqueEntities: Int = 0
    public var emptyCount: Int = 0

    enum CodingKeys: String, CodingKey {
        case pulses
        case total
        case uniqueEntities = "unique_entities"
        case emptyCount = "empty_count"
    }

    public init(pulses: [APIPulseHistoryEntry] = [], total: Int = 0, uniqueEntities: Int = 0, emptyCount: Int = 0) {
        self.pulses = pulses
        self.total = total
        self.uniqueEntities = uniqueEntities
        self.emptyCount = emptyCount
    }
}

public struct APIBudgetStatus: Codable, Hashable {
    public var monthKey: String
    public var spentUsd: Double
    public var pullsCount: Int
    public var remainingUsd: Double
    public var ceilingUsd: Double
    public var onHold: Bool

    enum CodingKeys: String, CodingKey {
        case monthKey = "month_key"
        case spentUsd = "spent_usd"
        case pullsCount = "pulls_count"
        case remainingUsd = "remaining_usd"
        case ceilingUsd = "ceiling_usd"
        case onHold = "on_hold"
    }

    public init(monthKey: String = "", spentUsd: Double = 0.0, pullsCount: Int = 0, remainingUsd: Double = 0.0, ceilingUsd: Double = 0.0, onHold: Bool = false) {
        self.monthKey = monthKey
        self.spentUsd = spentUsd
        self.pullsCount = pullsCount
        self.remainingUsd = remainingUsd
        self.ceilingUsd = ceilingUsd
        self.onHold = onHold
    }
}

public struct APIAlmanacHistoryEntry: Codable, Identifiable, Hashable {
    public var id: String { path }
    public var date: String
    public var filename: String
    public var path: String
    public var sizeKb: Double
    public var created: String

    enum CodingKeys: String, CodingKey {
        case date
        case filename
        case path
        case sizeKb = "size_kb"
        case created
    }
}

public struct APIAlmanacHistoryResponse: Codable {
    public var almanacs: [APIAlmanacHistoryEntry]
    public var total: Int
}

public struct APIAlmanacGenerateResponse: Codable, Hashable {
    public var status: String
    public var date: String
    public var htmlPath: String?
    public var mdPath: String?
    public var entitiesProcessed: Int
    public var claimsMoved: Int
    public var claimsCollapsed: Int
    public var newlyContested: Int
    public var entanglements: Int
    public var elapsedSeconds: Double
    public var error: String?
    public var dryRun: Bool

    enum CodingKeys: String, CodingKey {
        case status
        case date
        case htmlPath = "html_path"
        case mdPath = "md_path"
        case entitiesProcessed = "entities_processed"
        case claimsMoved = "claims_moved"
        case claimsCollapsed = "claims_collapsed"
        case newlyContested = "newly_contested"
        case entanglements
        case elapsedSeconds = "elapsed_seconds"
        case error
        case dryRun = "dry_run"
    }

    public init(status: String, date: String, htmlPath: String? = nil, mdPath: String? = nil, entitiesProcessed: Int = 0, claimsMoved: Int = 0, claimsCollapsed: Int = 0, newlyContested: Int = 0, entanglements: Int = 0, elapsedSeconds: Double = 0.0, error: String? = nil, dryRun: Bool = true) {
        self.status = status
        self.date = date
        self.htmlPath = htmlPath
        self.mdPath = mdPath
        self.entitiesProcessed = entitiesProcessed
        self.claimsMoved = claimsMoved
        self.claimsCollapsed = claimsCollapsed
        self.newlyContested = newlyContested
        self.entanglements = entanglements
        self.elapsedSeconds = elapsedSeconds
        self.error = error
        self.dryRun = dryRun
    }
}


public struct APIEntanglementEntry: Codable, Identifiable, Hashable {
    public var id: String { "\(entityA)-\(entityB)" }
    public var entityA: String
    public var entityB: String
    public var entanglementScore: Double
    public var coOccurrenceCount: Int
    public var independentPlatforms: [String]
    public var independentClusters: Int
    public var isStrong: Bool
    public var meyerWallachRaw: Double?

    enum CodingKeys: String, CodingKey {
        case entityA = "entity_a"
        case entityB = "entity_b"
        case entanglementScore = "entanglement_score"
        case coOccurrenceCount = "co_occurrence_count"
        case independentPlatforms = "independent_platforms"
        case independentClusters = "independent_clusters"
        case isStrong = "is_strong"
        case meyerWallachRaw = "meyer_wallach_raw"
    }
}

public struct APIEntanglementResponse: Codable {
    public var entityName: String
    public var entanglements: [APIEntanglementEntry]
    public var total: Int

    enum CodingKeys: String, CodingKey {
        case entityName = "entity_name"
        case entanglements
        case total
    }
}

public struct APITribunalDisagreement: Codable, Hashable {
    public var topic: String?
    public var skeptic: String?
    public var empiricist: String?
    public var believer: String?
    public var resolution: String?
}

public struct APITribunalResponse: Codable, Hashable {
    public var triggered: Bool
    public var claimText: String?
    public var wavefunction: APIClaimConfidence?
    public var divergenceRisk: Double?
    public var skepticPosition: String?
    public var empiricistPosition: String?
    public var believerPosition: String?
    public var skepticCitations: [String]?
    public var empiricistCitations: [String]?
    public var believerCitations: [String]?
    public var refereeSynthesis: String?
    public var finalStateLabel: String?
    public var disagreements: [APITribunalDisagreement]?
    public var allCitations: [String]?

    enum CodingKeys: String, CodingKey {
        case triggered
        case claimText = "claim_text"
        case wavefunction
        case divergenceRisk = "divergence_risk"
        case skepticPosition = "skeptic_position"
        case empiricistPosition = "empiricist_position"
        case believerPosition = "believer_position"
        case skepticCitations = "skeptic_citations"
        case empiricistCitations = "empiricist_citations"
        case believerCitations = "believer_citations"
        case refereeSynthesis = "referee_synthesis"
        case finalStateLabel = "final_state_label"
        case disagreements
        case allCitations = "all_citations"
    }
}



public struct APIAsyncTaskResponse: Codable, Hashable {
    public var taskId: String
    public var status: String
    public var message: String

    enum CodingKeys: String, CodingKey {
        case taskId = "task_id"
        case status
        case message
    }

    public init(taskId: String, status: String, message: String) {
        self.taskId = taskId
        self.status = status
        self.message = message
    }
}

public struct APITaskStatus: Codable, Hashable {
    public var id: String
    public var name: String
    public var status: String
    public var progress: Double
    public var logs: [String]
    public var result: [String: AnyDecodableValue]?
    public var elapsed: Double

    enum CodingKeys: String, CodingKey {
        case id
        case name
        case status
        case progress
        case logs
        case result
        case elapsed
    }

    public init(id: String, name: String, status: String, progress: Double, logs: [String], result: [String: AnyDecodableValue]? = nil, elapsed: Double = 0.0) {
        self.id = id
        self.name = name
        self.status = status
        self.progress = progress
        self.logs = logs
        self.result = result
        self.elapsed = elapsed
    }
}

public struct APIAlmanacFileResponse: Codable, Hashable {
    public var date: String
    public var content: String
}

public struct APIAlmanacSummaryResponse: Codable, Hashable {
    public var date: String?
    public var contestedClaims: [String]
    public var newlyContested: Int
    public var entitiesProcessed: [String]

    enum CodingKeys: String, CodingKey {
        case date
        case contestedClaims = "contested_claims"
        case newlyContested = "newly_contested"
        case entitiesProcessed = "entities_processed"
    }

    public init(date: String?, contestedClaims: [String], newlyContested: Int, entitiesProcessed: [String]) {
        self.date = date
        self.contestedClaims = contestedClaims
        self.newlyContested = newlyContested
        self.entitiesProcessed = entitiesProcessed
    }
}

// MARK: - System Status Progress

public struct APIStatusProgressSection: Codable {
    public var status: String?
    public var current: String?
    public var total: String?
    public var currentSlug: String?
    public var pagesProcessed: String?
    public var errors: String?
    public var pulsesSuccess: String?
    public var pulsesError: String?
    public var lastResult: String?
    public var lastRun: String?
    public var queueSize: String?
    public var succeeded: String?
    public var failed: String?
    public var eventsProcessed: String?
    public var totalCalls: String?
    public var successCalls: String?
    public var failedCalls: String?
    public var breakerOpen: String?
    public var nodes: String?
    public var relationships: String?
    public var startedAt: String?
    public var completedAt: String?

    enum CodingKeys: String, CodingKey {
        case status, current, total, errors
        case currentSlug = "current_slug"
        case pagesProcessed = "pages_processed"
        case pulsesSuccess = "pulses_success"
        case pulsesError = "pulses_error"
        case lastResult = "last_result"
        case lastRun = "last_run"
        case queueSize = "queue_size"
        case succeeded, failed
        case eventsProcessed = "events_processed"
        case totalCalls = "total_calls"
        case successCalls = "success_calls"
        case failedCalls = "failed_calls"
        case breakerOpen = "breaker_open"
        case nodes, relationships
        case startedAt = "started_at"
        case completedAt = "completed_at"
    }
}

public struct APIServerTime: Codable {
    public var iso8601: String
    public var unix: Double
    public var datetime: String
    public var timezone: String
    public var utcOffset: String
    public var utcIso8601: String

    enum CodingKeys: String, CodingKey {
        case iso8601, unix, datetime, timezone
        case utcOffset = "utc_offset"
        case utcIso8601 = "utc_iso8601"
    }
}


public struct APIStatusProgress: Codable {
    public var reconciliation: APIStatusProgressSection?
    public var idleIngestion: APIStatusProgressSection?
    public var chatIngest: APIStatusProgressSection?
    public var fallbackRetry: APIStatusProgressSection?
    public var wikiWatcher: APIStatusProgressSection?
    public var llmClient: APIStatusProgressSection?
    public var neo4j: APIStatusProgressSection?

    enum CodingKeys: String, CodingKey {
        case reconciliation
        case idleIngestion = "idle_ingestion"
        case chatIngest = "chat_ingest"
        case fallbackRetry = "fallback_retry"
        case wikiWatcher = "wiki_watcher"
        case llmClient = "llm_client"
        case neo4j
    }
}


public struct APISearchResult: Codable, Identifiable {
    public var id: String { name }
    public let name: String
    public let displayName: String
    public let labels: [String]
    public let preview: String?
    public let confidence: Double
    public let tags: [String]?
    public let score: Double

    enum CodingKeys: String, CodingKey {
        case name
        case displayName = "display_name"
        case labels
        case preview
        case confidence
        case tags
        case score
    }
}


public struct APISearchResponse: Codable {
    public let results: [APISearchResult]
    public let query: String
    public let total: Int
}
