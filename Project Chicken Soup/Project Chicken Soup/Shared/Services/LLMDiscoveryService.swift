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
    
    @Published public var availableModels: [String] = []
    @Published public var selectedModel: String = ""
    @Published public var activeProvider: String = ""
    
    private init() {}
    
    public func discoverActiveModels() async {
        isRefreshing = true
        defer { isRefreshing = false }
        
        do {
            // Fetch config from server which includes LLM discovery state
            let config: APIConfigResponse = try await APIClient.shared.request(path: "/config")
            self.availableModels = config.llm_available_models
            self.selectedModel = config.llm_active_model
            self.activeProvider = config.llm_active_provider
            
            // Build discovery chain from available models and provider info
            self.discoveryChain = config.llm_available_models.map { modelName in
                APIDiscoveryStatus(
                    modelName: modelName,
                    isAvailable: true,
                    isCurrent: modelName == config.llm_active_model,
                    latencyMs: 0.0
                )
            }
        } catch {
            // Fallback: simulate discovery when server is unreachable
            try? await Task.sleep(for: .seconds(0.8))
            var mockStatuses = [
                APIDiscoveryStatus(modelName: "oMLX (Mac)", isAvailable: true, isCurrent: true, latencyMs: 15.0),
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
