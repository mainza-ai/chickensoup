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
    
    @Published public var eventsError: Error?
    @Published public var entitiesError: Error?
    @Published public var queryError: Error?
    @Published public var spacetimeError: Error?
    
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
            let bodyDict: [String: Any] = ["query": text, "structured": isStructured]
            let bodyData = try JSONSerialization.data(withJSONObject: bodyDict)
            let response: APIQueryResponse = try await APIClient.shared.request(path: "/query", method: "POST", body: bodyData)
            
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
}
