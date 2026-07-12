import SwiftUI
import WebKit

#if os(macOS)
struct HTMLView: NSViewRepresentable {
    let htmlContent: String
    func makeNSView(context: Context) -> WKWebView { WKWebView() }
    func updateNSView(_ nsView: WKWebView, context: Context) { nsView.loadHTMLString(htmlContent, baseURL: nil) }
}
#else
struct HTMLView: UIViewRepresentable {
    let htmlContent: String
    func makeUIView(context: Context) -> WKWebView { WKWebView() }
    func updateUIView(_ uiView: WKWebView, context: Context) { uiView.loadHTMLString(htmlContent, baseURL: nil) }
}
#endif
