import SwiftUI

struct ConversationListView: View {
    @State private var conversationService = ConversationService.shared
    var onSelectConversation: (String) -> Void
    var onNewConversation: () -> Void

    @State private var renameId: String?
    @State private var renameText = ""
    @State private var deleteId: String?

    var body: some View {
        List(selection: $conversationService.activeConversationId) {
            Section {
                ForEach(conversationService.conversations) { conversation in
                    ConversationRow(
                        conversation: conversation,
                        isRenaming: renameId == conversation.id,
                        renameText: $renameText,
                        onStartRename: { renameId = conversation.id; renameText = conversation.title },
                        onFinishRename: { newTitle in
                            conversationService.rename(conversation.id, to: newTitle)
                            renameId = nil
                        },
                        onDelete: { deleteId = conversation.id }
                    )
                    .tag(conversation.id as String?)
                    .onTapGesture {
                        if renameId != conversation.id {
                            onSelectConversation(conversation.id)
                        }
                    }
                }
                .onDelete { indexSet in
                    for index in indexSet {
                        conversationService.delete(conversationService.conversations[index].id)
                    }
                }
            } header: {
                HStack {
                    Text("Conversations").font(.caption).foregroundStyle(.secondary)
                    Spacer()
                }
            }
        }
        .listStyle(.sidebar)
        .toolbar {
            ToolbarItem {
                Button("New Chat", systemImage: "square.and.pencil") {
                    onNewConversation()
                }
                .buttonStyle(.plain)
                .labelStyle(.iconOnly)
                .help("New Chat")
            }
        }
        .alert("Delete Conversation", isPresented: .init(
            get: { deleteId != nil },
            set: { if !$0 { deleteId = nil } }
        )) {
            Button("Cancel", role: .cancel) { deleteId = nil }
            Button("Delete", role: .destructive) {
                if let id = deleteId { conversationService.delete(id) }
                deleteId = nil
            }
        } message: {
            Text("This will permanently delete the conversation and all its messages.")
        }
    }
}

private struct ConversationRow: View {
    let conversation: Conversation
    let isRenaming: Bool
    @Binding var renameText: String
    let onStartRename: () -> Void
    let onFinishRename: (String) -> Void
    let onDelete: () -> Void

    var body: some View {
        HStack(spacing: 8) {
            Image(systemName: "bubble.left.and.bubble.right")
                .font(.caption).foregroundStyle(.secondary)
                .frame(width: 16)

            if isRenaming {
                TextField("Conversation name", text: $renameText)
                    .textFieldStyle(.plain)
                    .font(.subheadline)
                    .onSubmit { onFinishRename(renameText) }
            } else {
                VStack(alignment: .leading, spacing: 2) {
                    Text(conversation.title)
                        .font(.subheadline).fontWeight(.medium)
                        .lineLimit(1)
                    HStack(spacing: 4) {
                        Text("\(conversation.messageCount) msgs")
                            .font(.caption2).foregroundStyle(.tertiary)
                        Text(conversation.updatedAt, format: .relative(presentation: .numeric))
                            .font(.caption2).foregroundStyle(.tertiary)
                    }
                }
            }
        }
        .padding(.vertical, 2)
        .contextMenu {
            Button("Rename", systemImage: "pencil", action: onStartRename)
            Divider()
            Button("Delete", systemImage: "trash", role: .destructive, action: onDelete)
        }
    }
}

#Preview {
    ConversationListView(
        onSelectConversation: { _ in },
        onNewConversation: {}
    )
    .frame(width: 250)
}
