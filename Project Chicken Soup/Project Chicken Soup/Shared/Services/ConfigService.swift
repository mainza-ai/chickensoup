import Foundation
import SwiftUI
import os

@MainActor @Observable
public final class ConfigService {
    public static let shared = ConfigService()
    private let logger = Logger(subsystem: "com.projectchickensoup.Project-Chicken-Soup", category: "ConfigService")

    public var quantumBackend: String = "numpy"
    public var quantumHardwareEnabled: Bool = false
    public var ibmApiTokenSet: Bool = false
    public var dwaveApiTokenSet: Bool = false
    public var ionqApiTokenSet: Bool = false
    public var isFetchingConfig = false
    public var isSavingConfig = false

    public var llmActiveProvider: String = ""
    public var llmActiveModel: String = ""
    public var llmAvailableModels: [String] = []
    public var isSavingLLMConfig = false

    public var isDarkMode: Bool = {
        if UserDefaults.standard.object(forKey: "isDarkMode") == nil {
            return true
        }
        return UserDefaults.standard.bool(forKey: "isDarkMode")
    }()

    private init() {}

    public func toggleTheme() {
        isDarkMode.toggle()
        UserDefaults.standard.set(isDarkMode, forKey: "isDarkMode")
    }

    public func fetchConfig() async {
        isFetchingConfig = true
        defer { isFetchingConfig = false }

        do {
            let response: APIConfigResponse = try await APIClient.shared.request(path: "/config")
            self.quantumBackend = response.quantumBackend
            self.quantumHardwareEnabled = response.quantumHardwareEnabled
            self.ibmApiTokenSet = response.ibmApiTokenSet
            self.dwaveApiTokenSet = response.dwaveApiTokenSet
            self.ionqApiTokenSet = response.ionqApiTokenSet
            self.llmActiveProvider = response.llmActiveProvider
            self.llmActiveModel = response.llmActiveModel
            self.llmAvailableModels = response.llmAvailableModels
        } catch {
            logger.error("Failed to fetch configurations: \(error.localizedDescription)")
        }
    }

    public func saveConfig(backend: String, ibmToken: String?, dwaveToken: String?, ionqToken: String?, hardwareEnabled: Bool) async -> Bool {
        isSavingConfig = true
        defer { isSavingConfig = false }

        do {
            let req = APIConfigRequest(
                quantumBackend: backend,
                ibmApiToken: (ibmToken?.isEmpty ?? true) ? nil : ibmToken,
                dwaveApiToken: (dwaveToken?.isEmpty ?? true) ? nil : dwaveToken,
                ionqApiToken: (ionqToken?.isEmpty ?? true) ? nil : ionqToken,
                quantumHardwareEnabled: hardwareEnabled,
                llmActiveProvider: nil,
                llmActiveModel: nil
            )
            let bodyData = try JSONEncoder().encode(req)
            let response: APIConfigResponse = try await APIClient.shared.request(path: "/config", method: "POST", body: bodyData)

            self.quantumBackend = response.quantumBackend
            self.quantumHardwareEnabled = response.quantumHardwareEnabled
            self.ibmApiTokenSet = response.ibmApiTokenSet
            self.dwaveApiTokenSet = response.dwaveApiTokenSet
            self.ionqApiTokenSet = response.ionqApiTokenSet
            self.llmActiveProvider = response.llmActiveProvider
            self.llmActiveModel = response.llmActiveModel
            self.llmAvailableModels = response.llmAvailableModels
            return true
        } catch {
            logger.error("Failed to save configurations: \(error.localizedDescription)")
            return false
        }
    }

    // MARK: - LLM Configuration

    public func saveLLMConfig(provider: String?, model: String?) async -> Bool {
        isSavingLLMConfig = true
        defer { isSavingLLMConfig = false }

        do {
            let req = APILLMConfigRequest(
                llmActiveProvider: provider,
                llmActiveModel: model
            )
            let bodyData = try JSONEncoder().encode(req)
            let response: APILLMConfigResponse = try await APIClient.shared.request(path: "/config/llm", method: "POST", body: bodyData)

            self.llmActiveProvider = response.llmActiveProvider
            self.llmActiveModel = response.llmActiveModel
            self.llmAvailableModels = response.llmAvailableModels
            return true
        } catch {
            logger.error("Failed to save LLM configuration: \(error.localizedDescription)")
            return false
        }
    }

    public func refreshLLMDiscovery() async {
        do {
            let response: APIConfigResponse = try await APIClient.shared.request(path: "/config")
            self.llmAvailableModels = response.llmAvailableModels
            self.llmActiveProvider = response.llmActiveProvider
            self.llmActiveModel = response.llmActiveModel
        } catch {
            logger.error("Failed to refresh LLM discovery: \(error.localizedDescription)")
        }
    }

    public func probeLLMProvider(_ name: String) async -> (provider: String, available: Bool, models: [String], error: String?) {
        do {
            let req = APILLMProbeRequest(providerName: name)
            let bodyData = try JSONEncoder().encode(req)
            let response: APILLMProbeResponse = try await APIClient.shared.request(
                path: "/config/llm/probe", method: "POST", body: bodyData
            )
            return (response.provider, response.available, response.models, response.error)
        } catch {
            logger.error("Failed to probe LLM provider '\(name)': \(error.localizedDescription)")
            return (name, false, [], error.localizedDescription)
        }
    }
}
