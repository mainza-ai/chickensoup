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
    
    public init(responseText: String, inferredEvents: [APITemporalEvent] = [], inferredEntities: [APILoreEntity] = []) {
        self.responseText = responseText
        self.inferredEvents = inferredEvents
        self.inferredEntities = inferredEntities
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
