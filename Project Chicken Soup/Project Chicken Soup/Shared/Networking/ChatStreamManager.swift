import Foundation

@MainActor @Observable
public final class ChatStreamManager {
    public static let shared = ChatStreamManager()

    public private(set) var isStreaming = false
    public private(set) var accumulatedText = ""
    public var onToken: ((String) -> Void)?
    public var onComplete: ((String) -> Void)?
    public var onError: ((String) -> Void)?

    private var webSocketTask: URLSessionWebSocketTask?
    private let session: URLSession
    private let baseURL: URL

    private init() {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 120
        self.session = URLSession(configuration: config)
        self.baseURL = URL(string: "http://127.0.0.1:8000")!
        // Convert http(s) to ws(s)
        var wsURL = baseURL
        if var components = URLComponents(url: baseURL, resolvingAgainstBaseURL: true) {
            components.scheme = components.scheme == "https" ? "wss" : "ws"
            components.path = "/ws/agent"
            if let url = components.url {
                wsURL = url
            }
        }
        self._wsURL = wsURL
    }

    private let _wsURL: URL

    public func sendQuery(_ text: String) {
        guard !isStreaming else { return }

        isStreaming = true
        accumulatedText = ""

        let request = URLRequest(url: _wsURL)
        webSocketTask = session.webSocketTask(with: request)
        webSocketTask?.resume()

        receiveMessage()

        let message = URLSessionWebSocketTask.Message.string(text)
        webSocketTask?.send(message) { [weak self] error in
            if let error = error {
                Task { @MainActor in
                    self?.handleError("WebSocket send failed: \(error.localizedDescription)")
                }
            }
        }
    }

    public func cancel() {
        webSocketTask?.cancel(with: .normalClosure, reason: nil)
        webSocketTask = nil
        isStreaming = false
    }

    private func receiveMessage() {
        webSocketTask?.receive { [weak self] result in
            Task { @MainActor in
                switch result {
                case .success(let message):
                    self?.handleMessage(message)
                case .failure(let error):
                    self?.handleError("WebSocket receive failed: \(error.localizedDescription)")
                }
            }
        }
    }

    private func handleMessage(_ message: URLSessionWebSocketTask.Message) {
        switch message {
        case .string(let text):
            guard let data = text.data(using: .utf8),
                  let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                  let status = json["status"] as? String else {
                receiveMessage()
                return
            }

            switch status {
            case "processing":
                onToken?("")
                receiveMessage()

            case "streaming":
                if let chunk = json["chunk"] as? String {
                    accumulatedText += chunk
                    onToken?(accumulatedText)
                }
                receiveMessage()

            case "completed":
                if let answer = json["answer"] as? String {
                    accumulatedText = answer
                    onComplete?(answer)
                } else {
                    onComplete?(accumulatedText)
                }
                isStreaming = false
                webSocketTask = nil

            case "error":
                let msg = json["message"] as? String ?? "Unknown WebSocket error"
                handleError(msg)

            default:
                receiveMessage()
            }

        case .data:
            receiveMessage()

        @unknown default:
            receiveMessage()
        }
    }

    private func handleError(_ message: String) {
        onError?(message)
        isStreaming = false
        webSocketTask = nil
    }
}
