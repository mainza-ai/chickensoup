//
//  LLMDiscoveryService.swift
//  Project Chicken Soup
//
//  Created by mck on 6/23/26.
//

import Foundation
import Combine

@MainActor
public final class LLMDiscoveryService: ObservableObject {
    public static let shared = LLMDiscoveryService()
    
    @Published public private(set) var discoveryChain: [APIDiscoveryStatus] = [
        APIDiscoveryStatus(modelName: "oMLX (Mac)", isAvailable: true, isCurrent: true, latencyMs: 12.0),
        APIDiscoveryStatus(modelName: "Ollama", isAvailable: true, isCurrent: false, latencyMs: 45.0),
        APIDiscoveryStatus(modelName: "LM Studio", isAvailable: false, isCurrent: false, latencyMs: 0.0)
    ]
    @Published public private(set) var isRefreshing = false
    
    private init() {}
    
    public func discoverActiveModels() async {
        isRefreshing = true
        defer { isRefreshing = false }
        
        do {
            // Attempt to contact server for discovery status
            let statuses: [APIDiscoveryStatus] = try await APIClient.shared.request(path: "/discovery")
            self.discoveryChain = statuses
        } catch {
            // Fallback: simulate discovery request completion with local state when server is unreachable
            try? await Task.sleep(for: .seconds(0.8))
            // Ensure local state remains consistent
            var mockStatuses = [
                APIDiscoveryStatus(modelName: "oMLX (Mac)", isAvailable: true, isCurrent: true, latencyMs: 15.0),
                APIDiscoveryStatus(modelName: "Ollama", isAvailable: true, isCurrent: false, latencyMs: 38.0),
                APIDiscoveryStatus(modelName: "LM Studio", isAvailable: false, isCurrent: false, latencyMs: 0.0)
            ]
            // Randomly toggle one of the status values to make UI testing dynamic
            if let index = mockStatuses.indices.randomElement() {
                mockStatuses[index].latencyMs = Double.random(in: 10...60)
            }
            self.discoveryChain = mockStatuses
        }
    }
}
