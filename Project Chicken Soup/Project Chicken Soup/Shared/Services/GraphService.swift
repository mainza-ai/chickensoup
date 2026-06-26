import Foundation
import os
import SwiftData
import SwiftUI

@MainActor @Observable
public final class GraphService {
    public static let shared = GraphService()

    private let logger = Logger(subsystem: "com.chickensoup", category: "GraphService")

    public var focusedEntityName: String = ""
    public var neighborhood: NeighborhoodResponse? = nil
    public var isFetchingNeighborhood = false

    public var canGoBack = false
    public var canGoForward = false
    public var showNavigator = true
    public var showChatHistory = false

    private var backStack: [String] = []
    private var forwardStack: [String] = []
    private var fetchNeighborhoodTask: Task<Void, Never>?
    private let backStackMaxSize = 50

    private init() {}

    // MARK: - Fetch Neighborhood

    public func fetchNeighborhood(for name: String, context: ModelContext) async {
        isFetchingNeighborhood = true
        defer { isFetchingNeighborhood = false }

        do {
            let encodedName = name.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? name
            let responseDecoded: NeighborhoodResponse = try await APIClient.shared.request(
                path: "/graph/\(encodedName)"
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
            uniqueConns.sort(by: { $0.neighbor.name.localizedCaseInsensitiveCompare($1.neighbor.name) == .orderedAscending })

            let filteredResponse = NeighborhoodResponse(entity: responseDecoded.entity, connections: uniqueConns)

            self.neighborhood = filteredResponse
            self.focusedEntityName = name
        } catch {
            logger.error("Failed to fetch neighborhood: \(error)")
            loadFallbackNeighborhood(for: name, context: context)
        }
    }

    @MainActor
    private func loadFallbackNeighborhood(for name: String, context: ModelContext) {
        let fetchDescriptor = FetchDescriptor<LoreEntity>()
        let allEntities = (try? context.fetch(fetchDescriptor)) ?? []

        let simpleEntity: NeighborhoodEntity
        if let localEntity = allEntities.first(where: {
            $0.name.lowercased() == name.lowercased() ||
            $0.name.replacingOccurrences(of: " ", with: "-").lowercased() == name.replacingOccurrences(of: " ", with: "-").lowercased()
        }) {
            simpleEntity = NeighborhoodEntity(
                id: localEntity.name.lowercased(),
                name: localEntity.name,
                type: localEntity.type,
                summary: localEntity.summary,
                confidence: localEntity.confidence,
                source: localEntity.source,
                sources: [localEntity.source]
            )
        } else {
            simpleEntity = NeighborhoodEntity(
                id: name.lowercased(),
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
                    id: other.name.lowercased(),
                    name: other.name,
                    type: other.type,
                    summary: other.summary,
                    confidence: other.confidence,
                    source: other.source,
                    sources: [other.source]
                )
            )
        }
        let sortedConnections = connections.sorted(by: { $0.neighbor.name.localizedCaseInsensitiveCompare($1.neighbor.name) == .orderedAscending })

        let response = NeighborhoodResponse(entity: simpleEntity, connections: sortedConnections)

        self.neighborhood = response
        self.focusedEntityName = name
    }

    // MARK: - Navigation History

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
            await self?.fetchNeighborhood(for: name, context: context)
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

    // MARK: - Auto-Selection

    public func autoSelectInitialEntity(context: ModelContext) async {
        let allLocal = (try? context.fetch(FetchDescriptor<LoreEntity>())) ?? []
        guard !allLocal.isEmpty else { return }

        // Sort all entities alphabetically
        let sortedLocal = allLocal.sorted(by: { $0.name.localizedCaseInsensitiveCompare($1.name) == .orderedAscending })

        // Check at most 3 candidates to find a connected node, avoiding sequential network request storms
        let candidates = Array(sortedLocal.prefix(3))
        for entity in candidates {
            if Task.isCancelled { return }
            let encodedName = entity.name.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? entity.name
            if let response = try? await APIClient.shared.request(path: "/graph/\(encodedName)") as NeighborhoodResponse,
               !response.connections.isEmpty {
                var uniqueConns: [NeighborhoodConnection] = []
                var seenNames = Set<String>()
                for conn in response.connections {
                    let key = conn.neighbor.name.lowercased()
                    if !seenNames.contains(key) {
                        seenNames.insert(key)
                        uniqueConns.append(conn)
                    }
                }
                uniqueConns.sort(by: { $0.neighbor.name.localizedCaseInsensitiveCompare($1.neighbor.name) == .orderedAscending })

                let filteredResponse = NeighborhoodResponse(entity: response.entity, connections: uniqueConns)
                self.neighborhood = filteredResponse
                self.focusedEntityName = entity.name
                return
            }
        }
        
        // Fallback directly to the first entity without making extra connectivity checks
        if let first = sortedLocal.first {
            await fetchNeighborhood(for: first.name, context: context)
        }
    }
}
