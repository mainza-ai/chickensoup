import SwiftUI

struct ChatBubbleView: View {
    let message: ChatMessage
    var isCompact: Bool = false
    var onApprove: ((String) -> Void)?
    var onCancel: ((String) -> Void)?
    var onEdit: ((UUID) -> Void)?
    var onDelete: ((UUID) -> Void)?
    var onReact: ((UUID, String) -> Void)?

    @State private var showTimestamp = false

    private var isResearching: Bool {
        !message.isUser && message.taskId != nil
            && message.researchStatus != "completed"
            && message.researchStatus != "failed"
            && message.researchStatus != "pending_approval"
    }

    var body: some View {
        HStack(alignment: .bottom, spacing: isCompact ? 4 : 8) {
            if message.isUser {
                Spacer(minLength: 40)
                UserBubbleContent(message: message, showTimestamp: showTimestamp)
            } else {
                AssistantBubbleContent(
                    message: message,
                    showTimestamp: showTimestamp,
                    isResearching: isResearching,
                    onApprove: onApprove,
                    onCancel: onCancel,
                    onReact: onReact
                )
                Spacer(minLength: 40)
            }
        }
        .contextMenu {
            MessageContextMenu(
                message: message,
                onEdit: onEdit.map { cb in { cb(message.id) } },
                onDelete: onDelete.map { cb in { cb(message.id) } }
            )
        }
        .accessibilityAction(named: "Toggle timestamp") {
            withAnimation { showTimestamp.toggle() }
        }
    }
}

// MARK: - User Bubble

private struct UserBubbleContent: View {
    let message: ChatMessage
    let showTimestamp: Bool

    var body: some View {
        VStack(alignment: .trailing, spacing: 2) {
            MarkdownText(message.text)
                .font(.subheadline)
                .padding(.horizontal, 12).padding(.vertical, 8)
                .background(DesignConstants.systemOrange, in: RoundedRectangle(cornerRadius: 12))
                .foregroundStyle(.white)
                .multilineTextAlignment(.leading)
                .textSelection(.enabled)

            if showTimestamp {
                Text(message.timestamp, format: .dateTime.hour().minute())
                    .font(.caption2).foregroundStyle(.white.opacity(0.6))
                    .padding(.trailing, 4)
            }
        }
    }
}

// MARK: - Assistant Bubble

private struct AssistantBubbleContent: View {
    let message: ChatMessage
    let showTimestamp: Bool
    let isResearching: Bool
    let onApprove: ((String) -> Void)?
    let onCancel: ((String) -> Void)?
    let onReact: ((UUID, String) -> Void)?

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            if isResearching {
                ResearchingBubbleContent(message: message, onCancel: onCancel)
            } else if message.researchStatus == "pending_approval" {
                ApprovalBubbleContent(message: message, showTimestamp: showTimestamp, onApprove: onApprove)
            } else {
                AssistantBubbleStandard(message: message, showTimestamp: showTimestamp, onReact: onReact)
            }
        }
    }
}

// MARK: - Researching State

private struct ResearchingBubbleContent: View {
    let message: ChatMessage
    let onCancel: ((String) -> Void)?

    var body: some View {
        HStack(spacing: 6) {
            ProgressView().scaleEffect(0.8)
            Text("Researching\u{2026}")
                .font(.caption).foregroundStyle(DesignConstants.systemOrangeText)

            if let taskId = message.taskId, let onCancel {
                Spacer()
                Button("Cancel Research", systemImage: "stop.circle.fill") {
                    onCancel(taskId)
                }
                .buttonStyle(.plain)
                .font(.caption2).foregroundStyle(.secondary)
                .labelStyle(.iconOnly)
            }
        }
        .padding(.horizontal, 12).padding(.vertical, 8)
        .background(DesignConstants.controlBackground, in: RoundedRectangle(cornerRadius: 12))
        .overlay(RoundedRectangle(cornerRadius: 12).stroke(DesignConstants.dividerColor, lineWidth: 1))
    }
}

// MARK: - Approval State

private struct ApprovalBubbleContent: View {
    let message: ChatMessage
    let showTimestamp: Bool
    let onApprove: ((String) -> Void)?

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            MarkdownText(message.text)
                .font(.subheadline)
                .padding(.horizontal, 12).padding(.vertical, 8)
                .background(DesignConstants.controlBackground, in: RoundedRectangle(cornerRadius: 12))
                .overlay(RoundedRectangle(cornerRadius: 12).stroke(DesignConstants.systemOrange.opacity(0.5), lineWidth: 1))
                .foregroundStyle(DesignConstants.primaryText)
                .multilineTextAlignment(.leading)

            if let threadId = message.threadId {
                ApprovalActionsView(threadId: threadId, onApprove: onApprove)
            }

            if showTimestamp {
                Text(message.timestamp, format: .relative(presentation: .numeric))
                    .font(.caption2).foregroundStyle(.tertiary).padding(.leading, 4)
            }
        }
    }
}

private struct ApprovalActionsView: View {
    let threadId: String
    let onApprove: ((String) -> Void)?

    var body: some View {
        HStack(spacing: 10) {
            Button("Approve Research", systemImage: "checkmark.circle.fill") {
                onApprove?(threadId)
            }
            .font(.caption).bold().foregroundStyle(.white)
            .padding(.horizontal, 12).padding(.vertical, 6)
            .background(Color.green, in: RoundedRectangle(cornerRadius: 8))
            .buttonStyle(.plain)

            Button("Deny", systemImage: "xmark.circle.fill", action: {})
                .font(.caption).bold().foregroundStyle(.red)
                .padding(.horizontal, 12).padding(.vertical, 6)
                .background(Color.red.opacity(0.1), in: RoundedRectangle(cornerRadius: 8))
                .buttonStyle(.plain)
        }
        .padding(.leading, 4)
    }
}

// MARK: - Standard Assistant Bubble

private struct AssistantBubbleStandard: View {
    let message: ChatMessage
    let showTimestamp: Bool
    let onReact: ((UUID, String) -> Void)?

    @State private var userReaction: String?

    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            MarkdownText(message.text)
                .font(.subheadline)
                .padding(.horizontal, 12).padding(.vertical, 8)
                .background(DesignConstants.controlBackground, in: RoundedRectangle(cornerRadius: 12))
                .overlay(RoundedRectangle(cornerRadius: 12).stroke(DesignConstants.dividerColor, lineWidth: 1))
                .foregroundStyle(DesignConstants.primaryText)
                .multilineTextAlignment(.leading)
                .textSelection(.enabled)

            if showTimestamp {
                Text(message.timestamp, format: .relative(presentation: .numeric))
                    .font(.caption2).foregroundStyle(.tertiary).padding(.leading, 4)
            }

            HStack(spacing: 4) {
                Button { react("thumbsup") } label: {
                    Image(systemName: userReaction == "thumbsup" ? "hand.thumbsup.fill" : "hand.thumbsup")
                        .font(.caption2).foregroundStyle(userReaction == "thumbsup" ? DesignConstants.systemOrangeText : .secondary)
                }
                .buttonStyle(.plain)
                .accessibilityLabel("Like")

                Button { react("thumbsdown") } label: {
                    Image(systemName: userReaction == "thumbsdown" ? "hand.thumbsdown.fill" : "hand.thumbsdown")
                        .font(.caption2).foregroundStyle(userReaction == "thumbsdown" ? DesignConstants.systemOrangeText : .secondary)
                }
                .buttonStyle(.plain)
                .accessibilityLabel("Dislike")
            }
            .padding(.leading, 4).padding(.top, 2)
        }
    }

    private func react(_ reaction: String) {
        userReaction = (userReaction == reaction) ? nil : reaction
        onReact?(message.id, userReaction ?? "")
    }
}

// MARK: - Context Menu

private struct MessageContextMenu: View {
    let message: ChatMessage
    var onEdit: (() -> Void)?
    var onDelete: (() -> Void)?

    var body: some View {
        Button("Copy", systemImage: "doc.on.doc", action: copyMessage)

        if message.isUser {
            Button("Edit", systemImage: "pencil", action: { onEdit?() })
        }

        Divider()

        Button("Delete", systemImage: "trash", role: .destructive, action: { onDelete?() })
    }

    private func copyMessage() {
        #if os(macOS)
        NSPasteboard.general.clearContents()
        NSPasteboard.general.setString(message.text, forType: .string)
        #else
        UIPasteboard.general.string = message.text
        #endif
    }
}

#Preview {
    VStack(spacing: 16) {
        ChatBubbleView(
            message: ChatMessage(isUser: true, text: "What is the Vatican UFO connection?")
        )
        ChatBubbleView(
            message: ChatMessage(
                isUser: false,
                text: "Found relevant lore about the **1937** Vatican UFO crash recovery.\n\n```\nSource: Vatican Leak\nConfidence: 0.88\n```"
            )
        )
    }
    .padding()
}
