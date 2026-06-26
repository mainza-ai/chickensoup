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
    @State private var showWikiInsight = false
    @Environment(\.horizontalSizeClass) private var horizontalSizeClass
    var backendService = BackendService.shared
    
    private var isCompact: Bool { horizontalSizeClass == .compact }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Label("Temporal Chat History", systemImage: "sparkles")
                    .font(.caption)
                    .bold()
                    .foregroundStyle(DesignConstants.systemOrangeText)
                
                Spacer()
                
                if showWikiInsight {
                    Label("Wiki", systemImage: "leaf.fill")
                        .font(.caption2)
                        .foregroundStyle(DesignConstants.systemGreenText)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(DesignConstants.systemGreen.opacity(0.1), in: Capsule())
                }
                
                Button("Clear") {
                    onClear()
                }
                .font(.caption)
                .foregroundStyle(.secondary)
                .padding(.horizontal, 6)
                .padding(.vertical, 2)
                .background(Color.secondary.opacity(0.1), in: Capsule())
                .buttonStyle(.plain)
                
                Button("Close Chat", systemImage: "xmark.circle.fill", action: onClose)
                    .buttonStyle(.plain)
                    .labelStyle(.iconOnly)
            }
            
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(spacing: 8) {
                        ForEach(messages) { msg in
                            ChatBubbleView(message: msg, isCompact: isCompact)
                                .id(msg.id)
                        }
                    }
                    .padding(.vertical, 4)
                }
                .scrollDismissesKeyboard(.immediately)
                .frame(maxHeight: isCompact ? 160 : 240)
                .onChange(of: messages.count) { _, _ in
                    if let last = messages.last {
                        withAnimation {
                            proxy.scrollTo(last.id, anchor: .bottom)
                        }
                    }
                }
            }
        }
        .padding(isCompact ? 8 : 12)
        .background(DesignConstants.cardBackground.opacity(0.85))
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .overlay(RoundedRectangle(cornerRadius: 12).stroke(DesignConstants.dividerColor, lineWidth: 1))
        .frame(maxWidth: isCompact ? .infinity : 640)
        .padding(.horizontal, DesignConstants.compactPadding)
        .onChange(of: backendService.chat.unreadWikiPagesFromChat) { _, newValue in
            withAnimation(.easeInOut(duration: 0.3)) {
                showWikiInsight = newValue > 0
            }
            if newValue > 0 {
                DispatchQueue.main.asyncAfter(deadline: .now() + 5.0) {
                    withAnimation(.easeInOut(duration: 0.3)) {
                        showWikiInsight = false
                    }
                }
            }
        }
    }
}

struct ChatBubbleView: View {
    let message: ChatMessage
    var isCompact: Bool = false
    
    var body: some View {
        HStack(alignment: .top, spacing: isCompact ? 4 : 8) {
            if message.isUser {
                Spacer(minLength: 40)
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
                Spacer(minLength: 40)
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
