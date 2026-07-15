import SwiftUI

struct TextBlock {
    let content: String
    let isCode: Bool
}

struct MarkdownText: View {
    let text: String

    init(_ text: String) {
        self.text = text
    }

    var body: some View {
        let blocks = parseCodeBlocks(text)
        if blocks.isEmpty {
            Text(LocalizedStringKey(text))
        } else {
            VStack(alignment: .leading, spacing: 6) {
                ForEach(blocks.indices, id: \.self) { idx in
                    let block = blocks[idx]
                    if block.isCode {
                        CodeBlockView(code: block.content)
                    } else {
                        Text(LocalizedStringKey(block.content))
                            .textSelection(.enabled)
                    }
                }
            }
        }
    }

    private func parseCodeBlocks(_ raw: String) -> [TextBlock] {
        var blocks: [TextBlock] = []
        var remaining = raw
        while true {
            guard let open = remaining.range(of: "```") else {
                if !remaining.isEmpty { blocks.append(TextBlock(content: remaining, isCode: false)) }
                break
            }
            let before = String(remaining[remaining.startIndex..<open.lowerBound])
            if !before.isEmpty { blocks.append(TextBlock(content: before, isCode: false)) }
            let afterOpen = remaining[open.upperBound...]
            guard let close = afterOpen.range(of: "```") else {
                blocks.append(TextBlock(content: String(afterOpen), isCode: true))
                break
            }
            let code = String(afterOpen[afterOpen.startIndex..<close.lowerBound])
                .split(separator: "\n", maxSplits: 1, omittingEmptySubsequences: false)
            let codeContent = code.dropFirst().joined(separator: "\n")
            blocks.append(TextBlock(content: codeContent, isCode: true))
            remaining = String(remaining[close.upperBound...])
        }
        return blocks
    }
}

private struct CodeBlockView: View {
    let code: String

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text("Code")
                    .font(.caption2).foregroundStyle(.secondary)
                Spacer()
                Button("Copy", systemImage: "doc.on.doc", action: copyCode)
                    .buttonStyle(.plain).font(.caption2).foregroundStyle(DesignConstants.systemOrangeText)
                    .accessibilityLabel("Copy code block")
            }
            .padding(.horizontal, 8).padding(.top, 6)

            ScrollView(.horizontal, showsIndicators: false) {
                Text(code)
                    .font(.system(.caption, design: .monospaced))
                    .foregroundStyle(DesignConstants.primaryText)
                    .padding(.horizontal, 8).padding(.bottom, 6)
                    .textSelection(.enabled)
            }
        }
        .background(DesignConstants.controlBackground.opacity(0.5), in: RoundedRectangle(cornerRadius: 8))
        .overlay(RoundedRectangle(cornerRadius: 8).stroke(DesignConstants.dividerColor, lineWidth: 1))
    }

    private func copyCode() {
        #if os(macOS)
        NSPasteboard.general.clearContents()
        NSPasteboard.general.setString(code, forType: .string)
        #else
        UIPasteboard.general.string = code
        #endif
    }
}

#Preview {
    MarkdownText("Hello **world**!\n\n```swift\nlet x = 42\nprint(x)\n```")
        .padding()
}
