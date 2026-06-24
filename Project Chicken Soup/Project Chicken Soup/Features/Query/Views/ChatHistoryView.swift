import SwiftUI

struct ChatMessage: Identifiable, Codable {
    var id = UUID()
    var isUser: Bool
    var text: String
    var timestamp = Date()
}

struct ChatHistoryView: View {
    @Binding var messages: [ChatMessage]
    var onClear: () -> Void
    var onClose: () -> Void
    
    @State private var scrollToBottom = false
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Label("Temporal Chat History", systemImage: "sparkles")
                    .font(.caption)
                    .bold()
                    .foregroundStyle(DesignConstants.systemOrangeText)
                
                Spacer()
                
                Button("Clear") {
                    onClear()
                }
                .font(.caption2)
                .foregroundStyle(.secondary)
                .padding(.horizontal, 6)
                .padding(.vertical, 2)
                .background(Color.secondary.opacity(0.1), in: Capsule())
                .buttonStyle(.plain)
                
                Button(action: onClose) {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundStyle(.secondary)
                }
                .buttonStyle(.plain)
            }
            
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(spacing: 8) {
                        ForEach(messages) { msg in
                            ChatBubbleView(message: msg)
                                .id(msg.id)
                        }
                    }
                    .padding(.vertical, 4)
                }
                .scrollDismissesKeyboard(.immediately)
                .frame(maxHeight: 240)
                .onChange(of: messages.count) { _, _ in
                    if let last = messages.last {
                        withAnimation {
                            proxy.scrollTo(last.id, anchor: .bottom)
                        }
                    }
                }
            }
        }
        .padding(12)
        .background(DesignConstants.cardBackground.opacity(0.85))
        .liquidGlass()
        .frame(maxWidth: 640)
        .padding(.horizontal, DesignConstants.standardPadding)
    }
}

struct ChatBubbleView: View {
    let message: ChatMessage
    
    var body: some View {
        HStack {
            if message.isUser {
                Spacer()
                Text(message.text)
                    .font(.subheadline)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 8)
                    .background(DesignConstants.systemOrange, in: RoundedRectangle(cornerRadius: 12))
                    .foregroundStyle(.white)
                    .multilineTextAlignment(.leading)
            } else {
                Text(message.text)
                    .font(.subheadline)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 8)
                    .background(DesignConstants.controlBackground, in: RoundedRectangle(cornerRadius: 12))
                    .overlay(RoundedRectangle(cornerRadius: 12).stroke(DesignConstants.dividerColor, lineWidth: 1))
                    .foregroundStyle(DesignConstants.primaryText)
                    .multilineTextAlignment(.leading)
                Spacer()
            }
        }
    }
}

#Preview {
    ChatHistoryView(
        messages: .constant([
            ChatMessage(isUser: true, text: "What is the Vatican UFO connection?"),
            ChatMessage(isUser: false, text: "Found relevant lore about the 1937 Vatican UFO crash recovery."),
        ]),
        onClear: {},
        onClose: {}
    )
    .padding()
    .background(Color.gray.opacity(0.1))
}
