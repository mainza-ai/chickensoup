import SwiftUI

struct ChatHistoryView: View {
    @Binding var messages: [ChatMessage]
    var onClear: () -> Void
    var onClose: () -> Void
    var onApproveResearch: ((String) -> Void)?
    var onCancelResearch: ((String) -> Void)?

    @State private var showWikiInsight = false
    @State private var showChatSettings = false
    @State private var isNearBottom = true
    @Environment(\.horizontalSizeClass) private var horizontalSizeClass
    private let backendService = BackendService.shared
    @AppStorage("chatTemperature") private var chatTemperature: Double = 0.7
    @AppStorage("chatMaxTokens") private var chatMaxTokens: Double = 2048
    @AppStorage("chatSystemPrompt") private var chatSystemPrompt: String = "You are a helpful assistant."

    private var isCompact: Bool { horizontalSizeClass == .compact }

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            header

            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(spacing: 8) {
                        ForEach(messages) { msg in
                            ChatBubbleView(
                                message: msg,
                                isCompact: isCompact,
                                onApprove: onApproveResearch,
                                onCancel: onCancelResearch
                            )
                            .id(msg.id)
                        }

                        GeometryReader { geo in
                            Color.clear
                                .onChange(of: geo.frame(in: .named("chatScroll")).minY) { _, minY in
                                    isNearBottom = minY > -50
                                }
                        }
                        .frame(height: 0)
                    }
                    .padding(.vertical, 4)
                }
                .coordinateSpace(name: "chatScroll")
                .scrollDismissesKeyboard(.immediately)
                .onChange(of: messages.count) { _, _ in
                    if isNearBottom, let last = messages.last {
                        withAnimation { proxy.scrollTo(last.id, anchor: .bottom) }
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
            withAnimation(.easeInOut(duration: 0.3)) { showWikiInsight = newValue > 0 }
            if newValue > 0 {
                DispatchQueue.main.asyncAfter(deadline: .now() + 5.0) {
                    withAnimation(.easeInOut(duration: 0.3)) { showWikiInsight = false }
                }
            }
        }
    }

    private var header: some View {
        HStack {
            Label("Temporal Chat History", systemImage: "sparkles")
                .font(.caption).bold()
                .foregroundStyle(DesignConstants.systemOrangeText)

            Spacer()

            if showWikiInsight {
                    Label("Wiki", systemImage: "leaf.fill")
                        .font(.caption2)
                        .foregroundStyle(DesignConstants.systemGreenText)
                        .padding(.horizontal, 6).padding(.vertical, 2)
                        .background(DesignConstants.systemGreen.opacity(0.1), in: Capsule())
                }

                if !backendService.config.llmAvailableModels.isEmpty {
                    Menu {
                        Button("Refresh models") {
                            Task { await backendService.config.refreshLLMDiscovery() }
                        }
                        Divider()
                        ForEach(backendService.config.llmAvailableModels, id: \.self) { model in
                            Button(model) {
                                Task {
                                    await backendService.config.saveLLMConfig(
                                        provider: backendService.config.llmActiveProvider,
                                        model: model
                                    )
                                }
                            }
                        }
                    } label: {
                        HStack(spacing: 3) {
                            Text(backendService.config.llmActiveModel.isEmpty
                                 ? "Model"
                                 : backendService.config.llmActiveModel)
                                .font(.system(.caption, design: .monospaced))
                                .lineLimit(1)
                            Image(systemName: "chevron.up.chevron.down")
                                .font(.system(size: 8))
                        }
                        .padding(.horizontal, 6).padding(.vertical, 3)
                        .background(DesignConstants.controlBackground, in: RoundedRectangle(cornerRadius: 6))
                        .overlay(RoundedRectangle(cornerRadius: 6).stroke(DesignConstants.dividerColor, lineWidth: 1))
                    }
                    .menuStyle(.button)
                    .buttonStyle(.plain)
                }

                Button("Settings", systemImage: "slider.horizontal.3") {
                    showChatSettings.toggle()
                }
                .buttonStyle(.plain)
                .labelStyle(.iconOnly)
                .font(.caption2)
                .foregroundStyle(.secondary)
                .accessibilityLabel("Chat settings")
                .popover(isPresented: $showChatSettings) {
                    ChatSettingsPopover(
                        temperature: $chatTemperature,
                        maxTokens: $chatMaxTokens,
                        systemPrompt: $chatSystemPrompt
                    )
                    .frame(width: 260)
                    .padding()
                }

                Button("Clear", action: onClear)
                .font(.caption).foregroundStyle(.secondary)
                .padding(.horizontal, 6).padding(.vertical, 2)
                .background(Color.secondary.opacity(0.1), in: Capsule())
                .buttonStyle(.plain)

            Button("Close Chat", systemImage: "xmark.circle.fill", action: onClose)
                .buttonStyle(.plain).labelStyle(.iconOnly)
                .accessibilityLabel("Close chat history")
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


private struct ChatSettingsPopover: View {
    @Binding var temperature: Double
    @Binding var maxTokens: Double
    @Binding var systemPrompt: String

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Chat Settings")
                .font(.headline).bold()

            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Text("Temperature").font(.caption).foregroundStyle(.secondary)
                    Spacer()
                    Text(temperature, format: .number.precision(.fractionLength(2)))
                        .font(.system(.caption, design: .monospaced)).foregroundStyle(.secondary)
                }
                Slider(value: $temperature, in: 0...1, step: 0.05)
                    .tint(DesignConstants.systemOrange)
            }

            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Text("Max Tokens").font(.caption).foregroundStyle(.secondary)
                    Spacer()
                    Text(Int(maxTokens), format: .number)
                        .font(.system(.caption, design: .monospaced)).foregroundStyle(.secondary)
                }
                Slider(value: $maxTokens, in: 256...8192, step: 256)
                    .tint(DesignConstants.systemOrange)
            }

            VStack(alignment: .leading, spacing: 4) {
                Text("System Prompt").font(.caption).foregroundStyle(.secondary)
                TextEditor(text: $systemPrompt)
                    .font(.system(.caption, design: .monospaced))
                    .frame(height: 80)
                    .padding(6)
                    .background(DesignConstants.controlBackground, in: RoundedRectangle(cornerRadius: 6))
                    .overlay(RoundedRectangle(cornerRadius: 6).stroke(DesignConstants.dividerColor, lineWidth: 1))
            }
        }
    }
}
