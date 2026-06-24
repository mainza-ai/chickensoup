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
        APIDiscoveryStatus(modelName: "oMLX", isAvailable: false, isCurrent: false, latencyMs: 0.0),
        APIDiscoveryStatus(modelName: "Ollama", isAvailable: false, isCurrent: false, latencyMs: 0.0),
        APIDiscoveryStatus(modelName: "LM Studio", isAvailable: false, isCurrent: false, latencyMs: 0.0)
    ]
    @Published public private(set) var isRefreshing = false
    
    @Published public var availableModels: [String] = []
    @Published public var selectedModel: String = ""
    @Published public var activeProvider: String = ""
    @Published public var providerStates: [String: Bool] = [:]
    
    private init() {}
    
    public func discoverActiveModels() async {
        isRefreshing = true
        defer { isRefreshing = false }
        
        do {
            let config: APIConfigResponse = try await APIClient.shared.request(path: "/config")
            self.availableModels = config.llm_available_models
            self.selectedModel = config.llm_active_model
            self.activeProvider = config.llm_active_provider
            self.providerStates = config.llm_providers.mapValues { $0.available }
            
            // Build discovery chain from llm_providers response
            let providerOrder = ["omlx", "ollama", "lmstudio"]
            self.discoveryChain = providerOrder.map { name in
                let info = config.llm_providers[name]
                return APIDiscoveryStatus(
                    modelName: name.prefix(1).uppercased() + name.dropFirst(),
                    isAvailable: info?.available ?? false,
                    isCurrent: name == config.llm_active_provider,
                    latencyMs: 0.0
                )
            }
        } catch {
            try? await Task.sleep(for: .seconds(0.8))
            var mockStatuses = [
                APIDiscoveryStatus(modelName: "oMLX", isAvailable: true, isCurrent: true, latencyMs: 15.0),
                APIDiscoveryStatus(modelName: "Ollama", isAvailable: true, isCurrent: false, latencyMs: 38.0),
                APIDiscoveryStatus(modelName: "LM Studio", isAvailable: false, isCurrent: false, latencyMs: 0.0)
            ]
            if let index = mockStatuses.indices.randomElement() {
                mockStatuses[index].latencyMs = Double.random(in: 10...60)
            }
            self.discoveryChain = mockStatuses
        }
    }
}
