import Foundation
import SwiftUI
import os

@MainActor @Observable
public final class AlmanacService {
    public static let shared = AlmanacService()
    private let logger = Logger(subsystem: "com.projectchickensoup.Project-Chicken-Soup", category: "AlmanacService")

    public var budgetStatus: APIBudgetStatus? = nil
    public var lastPulseResults: [APIPulseResult] = []
    public var pulseHistory: [APIPulseHistoryEntry] = []
    public var almanacHistory: [APIAlmanacHistoryEntry] = []

    public var isFetchingBudget = false
    public var isPulsing = false
    public var isGeneratingAlmanac = false
    public var isFetchingHistory = false

    private init() {}

    public func fetchBudgetStatus() async {
        isFetchingBudget = true
        defer { isFetchingBudget = false }
        do {
            let res: APIBudgetStatus = try await APIClient.shared.request(path: "/budget/status")
            self.budgetStatus = res
        } catch {
            logger.error("Failed to fetch budget status: \(error.localizedDescription)")
        }
    }

    public func approveBudgetHold() async -> Bool {
        do {
            let _: [String: AnyDecodableValue] = try await APIClient.shared.request(path: "/budget/approve", method: "POST")
            await fetchBudgetStatus()
            return true
        } catch {
            logger.error("Failed to approve budget hold: \(error.localizedDescription)")
            return false
        }
    }

    public func triggerPulse(entityName: String, handles: [String: String]? = nil) async -> APIPulseResult? {
        isPulsing = true
        defer { isPulsing = false }
        do {
            struct PulseReq: Codable {
                var handles: [String: String]?
            }
            let req = PulseReq(handles: handles)
            let bodyData = try JSONEncoder().encode(req)
            let res: APIPulseResult = try await APIClient.shared.request(
                path: "/pulse/\(entityName)",
                method: "POST",
                body: bodyData
            )
            self.lastPulseResults.append(res)
            // Refresh budget and pulse history
            await fetchBudgetStatus()
            await fetchPulseHistory()
            return res
        } catch {
            logger.error("Failed to trigger pulse for \(entityName): \(error.localizedDescription)")
            return nil
        }
    }

    public func fetchPulseHistory(limit: Int = 50, latest: Bool = false) async {
        isFetchingHistory = true
        defer { isFetchingHistory = false }
        do {
            var queryItems = [URLQueryItem(name: "limit", value: String(limit))]
            if latest {
                queryItems.append(URLQueryItem(name: "latest", value: "true"))
            }
            let res: APIPulseHistoryResponse = try await APIClient.shared.request(
                path: "/pulse/history",
                queryItems: queryItems
            )
            self.pulseHistory = res.pulses
        } catch {
            logger.error("Failed to fetch pulse history: \(error.localizedDescription)")
        }
    }

    public func fetchDivergence(entityName: String) async -> APIDivergenceResult? {
        do {
            let res: APIDivergenceResult = try await APIClient.shared.request(path: "/entities/\(entityName)/divergence")
            return res
        } catch {
            logger.error("Failed to fetch divergence for \(entityName): \(error.localizedDescription)")
            return nil
        }
    }

    public func fetchTimeline(entityName: String, days: Int = 30) async -> APITimelineResponse? {
        do {
            let res: APITimelineResponse = try await APIClient.shared.request(
                path: "/entities/\(entityName)/timeline",
                queryItems: [URLQueryItem(name: "days", value: String(days))]
            )
            return res
        } catch {
            logger.error("Failed to fetch timeline for \(entityName): \(error.localizedDescription)")
            return nil
        }
    }

    public func fetchEntanglement(entityName: String) async -> APIEntanglementResponse? {
        do {
            let res: APIEntanglementResponse = try await APIClient.shared.request(path: "/entities/\(entityName)/entanglement")
            return res
        } catch {
            logger.error("Failed to fetch entanglement for \(entityName): \(error.localizedDescription)")
            return nil
        }
    }

    public func runTribunal(entityName: String, claimText: String, divergenceRisk: Double = 0.0) async -> APITribunalResponse? {
        do {
            struct TribunalReq: Codable {
                var claim_text: String
                var divergence_risk: Double
            }
            let req = TribunalReq(claim_text: claimText, divergence_risk: divergenceRisk)
            let bodyData = try JSONEncoder().encode(req)
            let res: APITribunalResponse = try await APIClient.shared.request(
                path: "/entities/\(entityName)/tribunal",
                method: "POST",
                body: bodyData
            )
            return res
        } catch {
            logger.error("Failed to run tribunal for \(entityName): \(error.localizedDescription)")
            return nil
        }
    }

    public func generateAlmanac(dryRun: Bool = true) async -> APIAlmanacGenerateResponse? {
        isGeneratingAlmanac = true
        defer { isGeneratingAlmanac = false }
        do {
            let res: APIAlmanacGenerateResponse = try await APIClient.shared.request(
                path: "/almanac/generate",
                method: "POST",
                queryItems: [URLQueryItem(name: "dry_run", value: String(dryRun))]
            )
            if !dryRun {
                await fetchAlmanacHistory()
                await fetchBudgetStatus()
            }
            return res
        } catch {
            logger.error("Failed to generate almanac (dryRun: \(dryRun)): \(error.localizedDescription)")
            return nil
        }
    }

    public func triggerPulseAsync(entityName: String, handles: [String: String]? = nil) async -> APIAsyncTaskResponse? {
        do {
            struct PulseReq: Codable {
                var handles: [String: String]?
            }
            let req = PulseReq(handles: handles)
            let bodyData = try JSONEncoder().encode(req)
            let res: APIAsyncTaskResponse = try await APIClient.shared.request(
                path: "/pulse/\(entityName)",
                method: "POST",
                body: bodyData
            )
            return res
        } catch {
            logger.error("Failed to trigger async pulse for \(entityName): \(error.localizedDescription)")
            return nil
        }
    }

    public func generateAlmanacAsync(dryRun: Bool = true) async -> APIAsyncTaskResponse? {
        do {
            let res: APIAsyncTaskResponse = try await APIClient.shared.request(
                path: "/almanac/generate",
                method: "POST",
                queryItems: [URLQueryItem(name: "dry_run", value: String(dryRun))]
            )
            return res
        } catch {
            logger.error("Failed to trigger async almanac generation (dryRun: \(dryRun)): \(error.localizedDescription)")
            return nil
        }
    }

    public func fetchTaskStatus(taskId: String) async -> APITaskStatus? {
        do {
            let res: APITaskStatus = try await APIClient.shared.request(
                path: "/tasks/\(taskId)"
            )
            return res
        } catch {
            logger.error("Failed to fetch status for task \(taskId): \(error.localizedDescription)")
            return nil
        }
    }

    public func fetchAlmanacHistory(limit: Int = 20) async {
        do {
            let res: APIAlmanacHistoryResponse = try await APIClient.shared.request(
                path: "/almanac/history",
                queryItems: [URLQueryItem(name: "limit", value: String(limit))]
            )
            self.almanacHistory = res.almanacs
        } catch {
            logger.error("Failed to fetch almanac history: \(error.localizedDescription)")
        }
    }

    public func fetchAlmanacFile(date: String) async -> String? {
        do {
            let res: APIAlmanacFileResponse = try await APIClient.shared.request(
                path: "/almanac/file/\(date)"
            )
            return res.content
        } catch {
            logger.error("Failed to fetch almanac content for \(date): \(error.localizedDescription)")
            return nil
        }
    }

    public func fetchPulseSnapshot(filePath: String) async -> [String: AnyDecodableValue]? {
        do {
            let res: [String: AnyDecodableValue] = try await APIClient.shared.request(
                path: "/pulse/snapshot",
                queryItems: [URLQueryItem(name: "filepath", value: filePath)]
            )
            return res
        } catch {
            logger.error("Failed to fetch pulse snapshot for \(filePath): \(error.localizedDescription)")
            return nil
        }
    }

    public func purgeEmptyPulses() async -> Bool {
        do {
            struct PurgeResponse: Codable {
                var purged_count: Int
                var status: String
            }
            let res: PurgeResponse = try await APIClient.shared.request(
                path: "/pulse/purge-empty",
                method: "POST"
            )
            return res.status == "success"
        } catch {
            logger.error("Failed to purge empty pulses: \(error.localizedDescription)")
            return false
        }
    }
}
