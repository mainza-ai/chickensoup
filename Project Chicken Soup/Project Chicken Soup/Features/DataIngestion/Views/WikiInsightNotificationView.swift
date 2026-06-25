import SwiftUI

struct WikiInsightNotificationView: View {
    @ObservedObject var backendService = BackendService.shared
    @State private var showBanner = false

    var body: some View {
        ZStack(alignment: .top) {
            if showBanner {
                HStack(spacing: 12) {
                    Image(systemName: "leaf.fill")
                        .foregroundStyle(DesignConstants.systemGreenText)
                        .font(.title3)

                    VStack(alignment: .leading, spacing: 2) {
                        Text("Wiki Updated")
                            .font(.subheadline)
                            .bold()
                            .foregroundStyle(DesignConstants.primaryText)
                        Text("\(backendService.unreadWikiPagesFromChat) new \(backendService.unreadWikiPagesFromChat == 1 ? "page" : "pages") from your conversations")
                            .font(.caption)
                            .foregroundStyle(DesignConstants.secondaryText)
                    }

                    Spacer()

                    Button {
                        withAnimation(.spring(duration: 0.3)) {
                            showBanner = false
                            backendService.clearUnreadWikiPages()
                        }
                    } label: {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundStyle(.secondary)
                    }
                    .buttonStyle(.plain)
                }
                .padding(12)
                .background(DesignConstants.cardBackground)
                .clipShape(RoundedRectangle(cornerRadius: 12))
                .overlay(
                    RoundedRectangle(cornerRadius: 12)
                        .stroke(DesignConstants.systemGreen.opacity(0.3), lineWidth: 1)
                )
                .shadow(color: .black.opacity(0.1), radius: 8, y: 4)
                .padding(.horizontal)
                .transition(.move(edge: .top).combined(with: .opacity))
            }
        }
        .onChange(of: backendService.unreadWikiPagesFromChat) { _, newValue in
            guard backendService.chatWikiNotify else { return }
            if newValue > 0 {
                withAnimation(.spring(duration: 0.4)) {
                    showBanner = true
                }
                DispatchQueue.main.asyncAfter(deadline: .now() + 6.0) {
                    withAnimation(.spring(duration: 0.3)) {
                        showBanner = false
                    }
                }
            }
        }
    }
}
