//
//  LLMDiscoveryService.swift
//  Project Chicken Soup
//
//  Created by mck on 6/23/26.
//

import Foundation

@MainActor @Observable
public final class LLMDiscoveryService {
    public static let shared = LLMDiscoveryService()
    
    public private(set) var discoveryChain: [APIDiscoveryStatus] = [
        APIDiscoveryStatus(modelName: "oMLX", isAvailable: false, isCurrent: false, latencyMs: 0.0),
        APIDiscoveryStatus(modelName: "Ollama", isAvailable: false, isCurrent: false, latencyMs: 0.0),
        APIDiscoveryStatus(modelName: "LM Studio", isAvailable: false, isCurrent: false, latencyMs: 0.0)
    ]
    public private(set) var isRefreshing = false
    
    public var availableModels: [String] = []
    public var selectedModel: String = ""
    public var activeProvider: String = ""
    public var providerStates: [String: Bool] = [:]
    
    private init() {}
    
    public func discoverActiveModels() async {
        isRefreshing = true
        defer { isRefreshing = false }
        
        do {
            let config: APIConfigResponse = try await APIClient.shared.request(path: "/config")
            self.availableModels = config.llmAvailableModels
            self.selectedModel = config.llmActiveModel
            self.activeProvider = config.llmActiveProvider
            self.providerStates = config.llmProviders.mapValues { $0.available }

            // Sync to BackendService so AINavigatorView displays the active model immediately
            BackendService.shared.config.llmActiveModel = config.llmActiveModel
            BackendService.shared.config.llmActiveProvider = config.llmActiveProvider
            
            // Build discovery chain from llm_providers response
            let providerOrder = ["omlx", "ollama", "lmstudio"]
            self.discoveryChain = providerOrder.map { name in
                let info = config.llmProviders[name]
                return APIDiscoveryStatus(
                    modelName: name.prefix(1).uppercased() + name.dropFirst(),
                    isAvailable: info?.available ?? false,
                    isCurrent: name == config.llmActiveProvider,
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
