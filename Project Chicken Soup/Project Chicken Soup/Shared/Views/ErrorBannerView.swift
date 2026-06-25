import SwiftUI

struct ErrorBannerView: View {
    let error: Error?
    let onDismiss: () -> Void

    var body: some View {
        if let error = error {
            HStack(spacing: 8) {
                Image(systemName: "exclamationmark.triangle.fill")
                    .foregroundStyle(.white)
                Text(error.localizedDescription)
                    .font(.subheadline)
                    .bold()
                    .foregroundStyle(.white)
                    .lineLimit(2)
                Spacer()
                Button(action: onDismiss) {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundStyle(.white.opacity(0.8))
                }
                .buttonStyle(.plain)
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .background(Color.red.opacity(0.85))
            .clipShape(RoundedRectangle(cornerRadius: 8))
            .padding(.horizontal, 8)
            .padding(.top, 4)
            .transition(.opacity.combined(with: .move(edge: .top)))
        }
    }
}

struct ErrorBannerModifier: ViewModifier {
    @ObservedObject var backendService: BackendService

    func body(content: Content) -> some View {
        VStack(spacing: 0) {
            ErrorBannerView(error: backendService.eventsError ?? backendService.entitiesError ?? backendService.queryError ?? backendService.spacetimeError) {
                backendService.eventsError = nil
                backendService.entitiesError = nil
                backendService.queryError = nil
                backendService.spacetimeError = nil
            }
            content
        }
        .animation(.spring(duration: 0.3), value: backendService.eventsError != nil)
        .animation(.spring(duration: 0.3), value: backendService.entitiesError != nil)
        .animation(.spring(duration: 0.3), value: backendService.queryError != nil)
        .animation(.spring(duration: 0.3), value: backendService.spacetimeError != nil)
    }
}

extension View {
    func errorBanner(backendService: BackendService) -> some View {
        modifier(ErrorBannerModifier(backendService: backendService))
    }
}
