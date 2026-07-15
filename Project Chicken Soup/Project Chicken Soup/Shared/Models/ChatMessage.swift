import Foundation

public struct ChatMessage: Identifiable, Codable, Equatable {
    public var id = UUID()
    public var isUser: Bool
    public var text: String
    public var timestamp = Date()
    public var taskId: String?
    public var threadId: String?
    public var researchStatus: String?

    public init(id: UUID = UUID(), isUser: Bool, text: String, timestamp: Date = Date(), taskId: String? = nil, threadId: String? = nil, researchStatus: String? = nil) {
        self.id = id
        self.isUser = isUser
        self.text = text
        self.timestamp = timestamp
        self.taskId = taskId
        self.threadId = threadId
        self.researchStatus = researchStatus
    }
}
