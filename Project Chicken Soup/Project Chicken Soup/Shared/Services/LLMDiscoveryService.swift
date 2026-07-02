//
//  LLMDiscoveryService.swift
//  Project Chicken Soup
//
//  Created by mck on 6/23/26.
//
//  Production-graded: surfaces real backend errors, never fabricates discovery state.
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
    public private(set) var discoveryError: String? = nil

    public var availableModels: [String] = []
    public var selectedModel: String = ""
    public var activeProvider: String = ""
    public var providerStates: [String: Bool] = [:]

    private init() {}

    public func discoverActiveModels() async {
        isRefreshing = true
        discoveryError = nil
        defer { isRefreshing = false }

        do {
            let config: APIConfigResponse = try await APIClient.shared.request(path: "/config")
            self.availableModels = config.llmAvailableModels
            self.selectedModel = config.llmActiveModel
            self.activeProvider = config.llmActiveProvider
            self.providerStates = config.llmProviders.mapValues { $0.available }

            BackendService.shared.config.llmActiveModel = config.llmActiveModel
            BackendService.shared.config.llmActiveProvider = config.llmActiveProvider

            let providerOrder = ["omlx", "ollama", "lmstudio"]
            self.discoveryChain = providerOrder.map { name in
                let info = config.llmProviders[name]
                return APIDiscoveryStatus(
                    modelName: name.prefix(1).uppercased() + name.dropFirst(),
                    isAvailable: info?.available ?? false,
                    isCurrent: name == config.llmActiveProvider,
                    latencyMs: 0.0,
                    error: info?.error
                )
            }
        } catch {
            discoveryError = "Backend unreachable: \(error.localizedDescription)"
            self.discoveryChain = [
                APIDiscoveryStatus(modelName: "oMLX", isAvailable: false, isCurrent: false, latencyMs: 0.0, error: "Backend unreachable"),
                APIDiscoveryStatus(modelName: "Ollama", isAvailable: false, isCurrent: false, latencyMs: 0.0, error: "Backend unreachable"),
                APIDiscoveryStatus(modelName: "LM Studio", isAvailable: false, isCurrent: false, latencyMs: 0.0, error: "Backend unreachable")
            ]
        }
    }
}
