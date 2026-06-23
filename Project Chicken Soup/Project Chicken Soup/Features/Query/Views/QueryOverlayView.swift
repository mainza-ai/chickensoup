//
//  QueryOverlayView.swift
//  Project Chicken Soup
//
//  Created by mck on 6/22/26.
//

import SwiftUI

struct QueryOverlayView: View {
    @Binding var text: String
    @Binding var isStructuredQuery: Bool
    var onSubmit: () -> Void
    
    @State private var isExpanded = false
    @FocusState private var isFocused: Bool
    
    private let suggestions = [
        "What happened in northern Italy in 1933?",
        "Whistleblower David Grusch testimony claims",
        "Plot timelines connected to Element 115",
        "Ariel School encounter in Ruwa, Zimbabwe 1994"
    ]
    
    var body: some View {
        VStack(spacing: DesignConstants.compactPadding) {
            HStack(spacing: DesignConstants.compactPadding) {
                Image(systemName: "sparkles")
                    .foregroundStyle(DesignConstants.systemOrangeText)
                    .bold()
                
                TextField(
                    isStructuredQuery ? "Enter Temporal Query Language (TQL)..." : "Ask about UFOs, aliens, or time travel...",
                    text: $text
                )
                .textFieldStyle(.plain)
                .font(.headline)
                .focused($isFocused)
                .onSubmit {
                    onSubmit()
                    isFocused = false
                }
                
                Button(action: {
                    isStructuredQuery.toggle()
                }) {
                    Text(isStructuredQuery ? "TQL" : "Natural")
                        .font(.caption)
                        .bold()
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(
                            isStructuredQuery ? DesignConstants.systemOrange : Color.secondary.opacity(0.1),
                            in: RoundedRectangle(cornerRadius: 6)
                        )
                        .foregroundStyle(isStructuredQuery ? .white : .primary)
                }
                .buttonStyle(.plain)
                
                if !text.isEmpty {
                    Button(action: { text = "" }) {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundStyle(.secondary)
                    }
                    .buttonStyle(.plain)
                }
                
                if BackendService.shared.isSubmittingQuery {
                    ProgressView()
                        .scaleEffect(0.8)
                        .frame(width: 24, height: 24)
                        .padding(.horizontal, 8)
                } else {
                    Button("Execute", systemImage: "play.fill", action: {
                        onSubmit()
                        isFocused = false
                    })
                    .font(.subheadline)
                    .bold()
                    .foregroundStyle(.white)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 8)
                    .background(DesignConstants.systemOrange, in: RoundedRectangle(cornerRadius: DesignConstants.buttonCornerRadius))
                    .buttonStyle(.plain)
                }
            }
            
            MultimodalInputView(queryText: $text)
                .padding(.top, 2)
            
            // Expanded Suggestions Panel when focused or active
            if isFocused || isExpanded {
                VStack(alignment: .leading, spacing: DesignConstants.compactPadding) {
                    Divider()
                        .padding(.vertical, 4)
                    
                    Text("Predictive Suggestions")
                        .font(.caption)
                        .bold()
                        .foregroundStyle(.secondary)
                        .padding(.bottom, 2)
                    
                    ForEach(suggestions, id: \.self) { suggestion in
                        Button {
                            withAnimation(DesignConstants.hoverAnimation) {
                                text = suggestion
                                isExpanded = false
                                isFocused = false
                                onSubmit()
                            }
                        } label: {
                            HStack {
                                Image(systemName: "magnifyingglass")
                                    .font(.subheadline)
                                    .foregroundStyle(.secondary)
                                Text(suggestion)
                                    .font(.subheadline)
                                    .foregroundStyle(DesignConstants.primaryText)
                                Spacer()
                                Image(systemName: "arrow.up.left")
                                    .font(.caption)
                                    .foregroundStyle(.tertiary)
                            }
                            .padding(.vertical, 6)
                            .padding(.horizontal, 8)
                            .contentShape(Rectangle())
                        }
                        .buttonStyle(.plain)
                    }
                }
                .transition(.opacity.combined(with: .move(edge: .top)))
            }
        }
        .padding(DesignConstants.standardPadding)
        .liquidGlass()
        .frame(maxWidth: 640)
        .padding(.horizontal, DesignConstants.standardPadding)
        .onChange(of: isFocused) { _, newValue in
            withAnimation(DesignConstants.hoverAnimation) {
                isExpanded = newValue
            }
        }
    }
}

#Preview {
    @Previewable @State var query = ""
    @Previewable @State var structured = false
    ZStack {
        DesignConstants.warmBackground.ignoresSafeArea()
        QueryOverlayView(text: $query, isStructuredQuery: $structured, onSubmit: {})
    }
}
