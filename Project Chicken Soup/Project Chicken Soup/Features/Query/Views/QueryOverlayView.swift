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
    @Environment(\.horizontalSizeClass) private var horizontalSizeClass
    
    private var isCompact: Bool { horizontalSizeClass == .compact }
    
    private let suggestions = [
        "What happened in northern Italy in 1933?",
        "Whistleblower David Grusch testimony claims",
        "Plot timelines connected to Element 115",
        "Ariel School encounter in Ruwa, Zimbabwe 1994"
    ]
    
    var body: some View {
        VStack(spacing: DesignConstants.compactPadding) {
            HStack(spacing: 6) {
                if !isCompact {
                    Image(systemName: "sparkles")
                        .foregroundStyle(DesignConstants.systemOrangeText)
                        .bold()
                }
                
                TextField(
                    isStructuredQuery ? "Enter Temporal Query Language (TQL)..." : "Ask about UFOs, aliens, or time travel...",
                    text: $text
                )
                .textFieldStyle(.plain)
                .font(isCompact ? .subheadline : .headline)
                .focused($isFocused)
                .onSubmit {
                    onSubmit()
                    isFocused = false
                }
                
                if !isCompact {
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
                }
                
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
                } else {
                    Button("Execute", systemImage: "play.fill", action: {
                        onSubmit()
                        isFocused = false
                    })
                    .font(.system(isCompact ? .caption : .subheadline, design: .rounded).bold())
                    .foregroundStyle(.white)
                    .padding(.horizontal, isCompact ? 8 : 12)
                    .padding(.vertical, 8)
                    .background(DesignConstants.systemOrange, in: RoundedRectangle(cornerRadius: DesignConstants.buttonCornerRadius))
                    .buttonStyle(.plain)
                }
            }
            
            if !isCompact {
                MultimodalInputView(queryText: $text)
                    .padding(.top, 2)
            }
            
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
        .padding(isCompact ? 10 : DesignConstants.standardPadding)
        .background(DesignConstants.cardBackground.opacity(0.9))
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .overlay(RoundedRectangle(cornerRadius: 12).stroke(DesignConstants.dividerColor, lineWidth: 1))
        .frame(maxWidth: isCompact ? .infinity : 640)
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
