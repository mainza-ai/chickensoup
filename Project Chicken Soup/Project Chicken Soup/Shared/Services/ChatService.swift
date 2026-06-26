import Foundation
import SwiftUI

@MainActor
public final class ChatService: ObservableObject {
    public static let shared = ChatService()

    @Published public var chatIngestStatus: APIChatIngestStatus?
    @Published public var unreadWikiPagesFromChat: Int = 0
    @Published public var chatNotifications: [APIChatIngestNotification] = []
    public var ingestHistory: [APIIngestHistoryEntry] = []

    public var isChatWikiConversionEnabled: Bool {
        get { UserDefaults.standard.object(forKey: "chatWikiConversion") == nil ? false : UserDefaults.standard.bool(forKey: "chatWikiConversion") }
        set { UserDefaults.standard.set(newValue, forKey: "chatWikiConversion") }
    }

    public var chatWikiMinConversationLength: Int {
        get { UserDefaults.standard.object(forKey: "chatWikiMinLength") == nil ? 10 : UserDefaults.standard.integer(forKey: "chatWikiMinLength") }
        set { UserDefaults.standard.set(newValue, forKey: "chatWikiMinLength") }
    }

    public var chatWikiNotify: Bool {
        get { UserDefaults.standard.object(forKey: "chatWikiNotify") == nil ? true : UserDefaults.standard.bool(forKey: "chatWikiNotify") }
        set { UserDefaults.standard.set(newValue, forKey: "chatWikiNotify") }
    }

    public var userName: String {
        get { UserDefaults.standard.string(forKey: "userWikiName") ?? "Primary Researcher" }
        set { UserDefaults.standard.set(newValue, forKey: "userWikiName") }
    }

    private init() {}

    public func fetchChatIngestStatus() async {
        do {
            let status: APIChatIngestStatus = try await APIClient.shared.request(path: "/chat/ingest/status")
            self.chatIngestStatus = status
        } catch {
            print("Failed to fetch chat ingest status: \(error.localizedDescription)")
        }
    }

    public func triggerChatIngest() async -> Bool {
        do {
            let bodyData = try JSONSerialization.data(withJSONObject: [:])
            let response: APIChatIngestNowResponse = try await APIClient.shared.request(
                path: "/chat/ingest/now", method: "POST", body: bodyData
            )
            if let status = response.status {
                self.chatIngestStatus = status
                self.unreadWikiPagesFromChat += status.pagesCreated
            }
            return response.success
        } catch {
            print("Failed to trigger chat ingest: \(error.localizedDescription)")
            return false
        }
    }

    public func setUserName(_ name: String) async -> Bool {
        do {
            let req = APISetUserNameRequest(name: name)
            let bodyData = try JSONEncoder().encode(req)
            let response: APISetUserNameResponse = try await APIClient.shared.request(
                path: "/chat/name", method: "POST", body: bodyData
            )
            if response.success {
                self.userName = response.currentName
            }
            return response.success
        } catch {
            print("Failed to set user name: \(error.localizedDescription)")
            return false
        }
    }

    public func clearUnreadWikiPages() {
        unreadWikiPagesFromChat = 0
    }

    public func fetchIngestHistory() async {
        do {
            let response: [String: [APIIngestHistoryEntry]] = try await APIClient.shared.request(path: "/chat/ingest/history")
            self.ingestHistory = response["history"] ?? []
        } catch {
            print("Failed to fetch ingest history: \(error.localizedDescription)")
        }
    }

    public func fetchChatNotifications() async {
        do {
            let response: [String: [APIChatIngestNotification]] = try await APIClient.shared.request(path: "/chat/ingest/notifications")
            self.chatNotifications = response["notifications"] ?? []
        } catch {
            print("Failed to fetch chat notifications: \(error.localizedDescription)")
        }
    }
}
