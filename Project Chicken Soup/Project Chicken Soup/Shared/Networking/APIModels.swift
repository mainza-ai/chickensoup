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
