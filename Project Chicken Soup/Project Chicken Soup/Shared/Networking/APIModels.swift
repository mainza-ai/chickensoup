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
    public var type: String // "Person", "Place", "Concept", "Object", "Project"
    public var summary: String
    public var confidence: Double
    public var source: String
    public var userNotes: String?
    public var sources: [String]?
    
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
    
    public init(success: Bool, logs: [String], gravityMetric: Double, velocityMetric: Double, fieldIntensity: Double, resolvedPathConfidence: Double) {
        self.success = success
        self.logs = logs
        self.gravityMetric = gravityMetric
        self.velocityMetric = velocityMetric
        self.fieldIntensity = fieldIntensity
        self.resolvedPathConfidence = resolvedPathConfidence
    }
}

public struct APIQueryResponse: Codable {
    public var responseText: String
    public var inferredEvents: [APITemporalEvent]
    public var inferredEntities: [APILoreEntity]
    public var conversationId: String?
    
    enum CodingKeys: String, CodingKey {
        case responseText = "answer"
        case inferredEvents = "inferred_events"
        case inferredEntities = "inferred_entities"
        case conversationId = "conversation_id"
    }
    
    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        self.responseText = try container.decode(String.self, forKey: .responseText)
        self.inferredEvents = try container.decodeIfPresent([APITemporalEvent].self, forKey: .inferredEvents) ?? []
        self.inferredEntities = try container.decodeIfPresent([APILoreEntity].self, forKey: .inferredEntities) ?? []
        self.conversationId = try container.decodeIfPresent(String.self, forKey: .conversationId)
    }
    
    public init(responseText: String, inferredEvents: [APITemporalEvent] = [], inferredEntities: [APILoreEntity] = [], conversationId: String? = nil) {
        self.responseText = responseText
        self.inferredEvents = inferredEvents
        self.inferredEntities = inferredEntities
        self.conversationId = conversationId
    }
}

public struct APIDiscoveryStatus: Codable {
    public var modelName: String
    public var isAvailable: Bool
    public var isCurrent: Bool
    public var latencyMs: Double
    
    public init(modelName: String, isAvailable: Bool, isCurrent: Bool, latencyMs: Double) {
        self.modelName = modelName
        self.isAvailable = isAvailable
        self.isCurrent = isCurrent
        self.latencyMs = latencyMs
    }
}

public struct NeighborhoodEntity: Codable, Identifiable, Hashable {
    public var id: UUID
    public var name: String
    public var type: String // "Person", "Place", "Concept", "Object", "Project", "Event"
    public var summary: String
    public var confidence: Double
    public var source: String
    public var sources: [String]
    
    public func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }
    
    public static func == (lhs: NeighborhoodEntity, rhs: NeighborhoodEntity) -> Bool {
        lhs.id == rhs.id
    }
    
    public init(id: UUID = UUID(), name: String, type: String, summary: String, confidence: Double, source: String, sources: [String]) {
        self.id = id
        self.name = name
        self.type = type
        self.summary = summary
        self.confidence = confidence
        self.source = source
        self.sources = sources
    }
}

public struct NeighborhoodConnection: Codable, Identifiable {
    public var id: UUID { neighbor.id }
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
    
    public init(entity: NeighborhoodEntity, connections: [NeighborhoodConnection]) {
        self.entity = entity
        self.connections = connections
    }
}

public struct APIConfigRequest: Codable {
    public var quantum_backend: String
    public var ibm_api_token: String?
    public var dwave_api_token: String?
    public var ionq_api_token: String?
    public var quantum_hardware_enabled: Bool
    public var llm_active_provider: String?
    public var llm_active_model: String?
    
    public init(quantum_backend: String, ibm_api_token: String? = nil, dwave_api_token: String? = nil, ionq_api_token: String? = nil, quantum_hardware_enabled: Bool, llm_active_provider: String? = nil, llm_active_model: String? = nil) {
        self.quantum_backend = quantum_backend
        self.ibm_api_token = ibm_api_token
        self.dwave_api_token = dwave_api_token
        self.ionq_api_token = ionq_api_token
        self.quantum_hardware_enabled = quantum_hardware_enabled
        self.llm_active_provider = llm_active_provider
        self.llm_active_model = llm_active_model
    }
}

public struct APILLMProviderStatus: Codable {
    public var available: Bool
    public var models: [String]
}

public struct APIConfigResponse: Codable {
    public var success: Bool
    public var quantum_backend: String
    public var quantum_hardware_enabled: Bool
    public var ibm_api_token_set: Bool
    public var dwave_api_token_set: Bool
    public var ionq_api_token_set: Bool
    public var llm_active_provider: String
    public var llm_active_model: String
    public var llm_available_models: [String]
    public var llm_providers: [String: APILLMProviderStatus]
    
    public init(success: Bool, quantum_backend: String, quantum_hardware_enabled: Bool, ibm_api_token_set: Bool, dwave_api_token_set: Bool, ionq_api_token_set: Bool, llm_active_provider: String, llm_active_model: String, llm_available_models: [String], llm_providers: [String: APILLMProviderStatus]) {
        self.success = success
        self.quantum_backend = quantum_backend
        self.quantum_hardware_enabled = quantum_hardware_enabled
        self.ibm_api_token_set = ibm_api_token_set
        self.dwave_api_token_set = dwave_api_token_set
        self.ionq_api_token_set = ionq_api_token_set
        self.llm_active_provider = llm_active_provider
        self.llm_active_model = llm_active_model
        self.llm_available_models = llm_available_models
        self.llm_providers = llm_providers
    }
}

public struct APILLMConfigRequest: Codable {
    public var llm_active_provider: String?
    public var llm_active_model: String?
    
    public init(llm_active_provider: String? = nil, llm_active_model: String? = nil) {
        self.llm_active_provider = llm_active_provider
        self.llm_active_model = llm_active_model
    }
}

public struct APILLMConfigResponse: Codable {
    public var success: Bool
    public var llm_active_provider: String
    public var llm_active_model: String
    public var llm_available_models: [String]
    public var llm_providers: [String: APILLMProviderStatus]
}

public struct APILLMProbeRequest: Codable {
    public var provider_name: String
    public init(providerName: String) {
        self.provider_name = providerName
    }
}

public struct APILLMProbeResponse: Codable {
    public var provider: String
    public var available: Bool
    public var models: [String]
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

    public init(success: Bool, status: APIChatIngestStatus? = nil) {
        self.success = success
        self.status = status
    }
}

public struct APISetUserNameRequest: Codable {
    public var name: String

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
