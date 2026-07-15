import Foundation

@MainActor @Observable
public final class ConversationService {
    public static let shared = ConversationService()

    public private(set) var conversations: [Conversation] = []
    public var activeConversationId: String?
    public private(set) var isLoading = false

    private let storage = UserDefaults.standard
    private let conversationsKey = "saved_conversations"
    private let messagesPrefix = "conversation_messages_"

    private init() {
        loadConversations()
        if conversations.isEmpty {
            createNew()
        } else {
            activeConversationId = conversations.first?.id
        }
    }

    // MARK: - Conversation CRUD

    public func createNew() -> String {
        let id = UUID().uuidString
        let conversation = Conversation(
            id: id,
            title: "New Chat",
            createdAt: Date(),
            updatedAt: Date(),
            messageCount: 0,
            modelId: ""
        )
        conversations.insert(conversation, at: 0)
        activeConversationId = id
        saveConversations()
        clearActiveMessages()
        return id
    }

    public func delete(_ id: String) {
        conversations.removeAll { $0.id == id }
        storage.removeObject(forKey: messagesPrefix + id)
        if activeConversationId == id {
            activeConversationId = conversations.first?.id
        }
        saveConversations()
    }

    public func rename(_ id: String, to title: String) {
        guard let idx = conversations.firstIndex(where: { $0.id == id }) else { return }
        conversations[idx].title = String(title.prefix(100))
        conversations[idx].updatedAt = Date()
        saveConversations()
    }

    public func switchTo(_ id: String) {
        guard conversations.contains(where: { $0.id == id }) else { return }
        activeConversationId = id
    }

    // MARK: - Message Persistence

    public func saveMessages(_ messages: [ChatMessage]) {
        guard let id = activeConversationId else { return }
        let encoder = JSONEncoder()
        if let data = try? encoder.encode(messages) {
            storage.set(data, forKey: messagesPrefix + id)
            updateConversationMeta(messageCount: messages.count)
        }
    }

    public func loadMessages() -> [ChatMessage] {
        guard let id = activeConversationId else { return [] }
        guard let data = storage.data(forKey: messagesPrefix + id) else { return [] }
        let decoder = JSONDecoder()
        return (try? decoder.decode([ChatMessage].self, from: data)) ?? []
    }

    public func clearActiveMessages() {
        guard let id = activeConversationId else { return }
        storage.removeObject(forKey: messagesPrefix + id)
        updateConversationMeta(messageCount: 0)
    }

    // MARK: - Active Conversation Title

    public func updateActiveTitle(from messages: [ChatMessage]) {
        guard let id = activeConversationId else { return }
        guard let firstUserMsg = messages.first(where: { $0.isUser }) else { return }
        let title = String(firstUserMsg.text.prefix(60))
        guard let idx = conversations.firstIndex(where: { $0.id == id }) else { return }
        if conversations[idx].title == "New Chat" || conversations[idx].title.isEmpty {
            conversations[idx].title = title
            conversations[idx].updatedAt = Date()
            saveConversations()
        }
    }

    // MARK: - Private

    private func updateConversationMeta(messageCount: Int) {
        guard let id = activeConversationId else { return }
        guard let idx = conversations.firstIndex(where: { $0.id == id }) else { return }
        conversations[idx].messageCount = messageCount
        conversations[idx].updatedAt = Date()
        saveConversations()
    }

    private func loadConversations() {
        guard let data = storage.data(forKey: conversationsKey) else { return }
        let decoder = JSONDecoder()
        if let loaded = try? decoder.decode([Conversation].self, from: data) {
            conversations = loaded.sorted { $0.updatedAt > $1.updatedAt }
        }
    }

    private func saveConversations() {
        let encoder = JSONEncoder()
        if let data = try? encoder.encode(conversations) {
            storage.set(data, forKey: conversationsKey)
        }
    }
}

// MARK: - Conversation Model

public struct Conversation: Identifiable, Codable, Sendable {
    public var id: String
    public var title: String
    public var createdAt: Date
    public var updatedAt: Date
    public var messageCount: Int
    public var modelId: String

    public init(id: String, title: String, createdAt: Date, updatedAt: Date, messageCount: Int, modelId: String) {
        self.id = id
        self.title = title
        self.createdAt = createdAt
        self.updatedAt = updatedAt
        self.messageCount = messageCount
        self.modelId = modelId
    }
}
